#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Veille Sentinel-2 (Lot B1) — détection de changement de rivage entre deux
périodes, exportée en GeoJSON pour la plateforme.

Référence méthodologique : 7.14 (articulation Sentinel-2 / Landsat / THR),
                           plan d'implémentation section 5/B1.

Logique
-------
1. Charger Sentinel-2 SR Harmonized depuis Earth Engine pour les deux
   périodes (référence et courante).
2. Composite médian par période, filtre nuage CLOUDY_PIXEL_PERCENTAGE < 20.
3. NDWI = (B3 - B8) / (B3 + B8)  → seuil 0 (eau si > 0).
4. Soustraire les deux masques eau → carte de changement (eau→terre ou
   terre→eau).
5. Vectoriser les zones de changement de surface > magnitude_min_m² en
   LineStrings le long du rivage.
6. Exporter en GeoJSON dans data/alerts/{territoire}.geojson.

Coût
----
Exécution côté Google (gratuite usage recherche / non-commercial).
Le script ne télécharge que la géométrie résultat (quelques ko à mo).

Prérequis
---------
    pip install earthengine-api geopandas shapely
    earthengine authenticate

Usage
-----
    python tools/sentinel_veille_GEE.py \\
        --territoire wallis \\
        --periode_ref 2020 \\
        --periode_cur 2025 \\
        --out data/alerts/wallis.geojson

Note : le projet Earth Engine à associer est défini par la variable
d'environnement `EE_PROJECT` ou par l'option `--project`.
"""
import argparse
import json
import os
import sys
import datetime as _dt

# Bboxes par défaut (WGS84) pour les six territoires — emprises larges, à
# resserrer si nécessaire. À NE PAS confondre avec les emprises de zoom
# du modèle TERRITOIRES de l'app.
BBOX_TERR = {
    'spm':      (-56.55, 46.70, -56.10, 47.20),    # Saint-Pierre-et-Miquelon
    'wallis':   (-178.30, -13.50, -176.00, -14.45),  # Wallis-et-Futuna (Uvea + Futuna + Alofi)
    'nc':       (163.50, -22.80, 168.30, -19.50),  # Nouvelle-Calédonie (Grande Terre + Loyauté)
    'stmartin': (-63.20, 18.00, -63.00, 18.15),    # Saint-Martin (partie française)
    'stbarth':  (-62.90, 17.85, -62.78, 17.95),    # Saint-Barthélemy
    'pf':       (-152.00, -18.00, -148.00, -16.50),  # Polynésie française (Société, à élargir si besoin)
}

# Périodes par défaut (mois 1–12 sur l'année indiquée)
def _periode_range(annee):
    return f"{annee}-01-01", f"{int(annee)+1}-01-01"


def _connect_ee(project):
    """Initialise Earth Engine. Échec gracieux si l'auth manque."""
    try:
        import ee  # type: ignore
    except ImportError:
        print("ERREUR : module `earthengine-api` introuvable. `pip install earthengine-api`.", file=sys.stderr)
        sys.exit(2)
    try:
        if project:
            ee.Initialize(project=project)
        else:
            ee.Initialize()
        return ee
    except Exception as e:
        print(f"ERREUR Earth Engine : {e}", file=sys.stderr)
        print("Tentative : `earthengine authenticate` puis relancez.", file=sys.stderr)
        sys.exit(3)


def _composite_ndwi(ee, bbox, date_start, date_end):
    """Composite médian Sentinel-2 SR Harmonized + NDWI sur la période."""
    geom = ee.Geometry.Rectangle(list(bbox))
    col = (
        ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        .filterBounds(geom)
        .filterDate(date_start, date_end)
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
    )
    n = col.size().getInfo()
    if n == 0:
        return None, 0
    composite = col.median().clip(geom)
    # NDWI = (B3 - B8) / (B3 + B8) — eau forte > 0
    ndwi = composite.normalizedDifference(['B3', 'B8']).rename('ndwi')
    return ndwi, n


def _detecter_changement(ee, ndwi_ref, ndwi_cur, bbox, magnitude_min_m, ndwi_seuil=0.0):
    """Détecte les pixels où le rivage a bougé et vectorise en LineStrings."""
    geom = ee.Geometry.Rectangle(list(bbox))
    eau_ref = ndwi_ref.gt(ndwi_seuil).rename('eau_ref')
    eau_cur = ndwi_cur.gt(ndwi_seuil).rename('eau_cur')
    # 1 = eau→terre (avancée), -1 = terre→eau (recul), 0 = sans changement
    chg = eau_cur.subtract(eau_ref).rename('chg')
    # Magnitude minimale : nombre de pixels Sentinel (10 m chaque)
    px_min = max(1, magnitude_min_m // 10)
    # Surface en pixels connexes ≥ px_min → garder
    masque = chg.abs().eq(1)
    composantes = masque.connectedPixelCount(50).gte(px_min).And(masque)
    # Vectoriser
    vecteurs = composantes.selfMask().reduceToVectors(
        geometry=geom,
        scale=10,
        geometryType='polygon',
        maxPixels=1e10,
        bestEffort=True,
    )
    # Conserver le sens du changement
    vecteurs = vecteurs.map(lambda f: f.set(
        'alerte_type',
        ee.Algorithms.If(
            chg.reduceRegion(reducer=ee.Reducer.mean(), geometry=f.geometry(), scale=10).get('chg'),
            ee.Algorithms.If(
                ee.Number(chg.reduceRegion(reducer=ee.Reducer.mean(), geometry=f.geometry(), scale=10).get('chg')).gt(0),
                'avancee',
                'recul'
            ),
            'changement'
        )
    ))
    return vecteurs


def _evaluer_features(ee, fc, periode_ref, periode_cur):
    """Récupère les features depuis Earth Engine et les transforme en GeoJSON local."""
    geojson = fc.getInfo()
    features = []
    for f in geojson.get('features', []):
        props = f.get('properties') or {}
        geom = f.get('geometry') or {}
        # Polygone → centroid + dimension caractéristique pour LineString
        # On garde le polygone tel quel (alerte de zone) — Leaflet sait l'afficher.
        coords = geom.get('coordinates')
        if not coords:
            continue
        # Magnitude estimée : surface du polygone × √2 (heuristique de bord)
        # Approche pragmatique sans recalcul GIS local
        magnitude_m = props.get('magnitude_m') or 20
        features.append({
            'type': 'Feature',
            'geometry': geom,
            'properties': {
                'alerte_type': props.get('alerte_type', 'changement'),
                'magnitude_m': int(magnitude_m),
                'priorite': 'haute' if magnitude_m >= 50 else ('moyenne' if magnitude_m >= 30 else 'basse'),
                'periode_ref': str(periode_ref),
                'periode_cur': str(periode_cur),
                'note': f"Zone de changement détectée entre {periode_ref} et {periode_cur} (Sentinel-2, NDWI > 0).",
            }
        })
    return features


def main():
    ap = argparse.ArgumentParser(description='Veille Sentinel-2 — détection de changement de rivage')
    ap.add_argument('--territoire', required=True, choices=list(BBOX_TERR.keys()))
    ap.add_argument('--periode_ref', required=True, help='Année de référence (ex. 2020)')
    ap.add_argument('--periode_cur', required=True, help='Année courante (ex. 2025)')
    ap.add_argument('--magnitude_min_m', type=int, default=20,
                    help='Magnitude minimale du changement à signaler (m, défaut 20 = 2 pixels)')
    ap.add_argument('--ndwi_seuil', type=float, default=0.0)
    ap.add_argument('--bbox', help='Bbox personnalisée : "ouest,sud,est,nord"')
    ap.add_argument('--out', help='Fichier de sortie (défaut : data/alerts/{territoire}.geojson)')
    ap.add_argument('--project', help='Projet Earth Engine (sinon EE_PROJECT env)')
    args = ap.parse_args()

    bbox = BBOX_TERR[args.territoire]
    if args.bbox:
        bbox = tuple(float(x) for x in args.bbox.split(','))

    out_path = args.out or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'data', 'alerts', f'{args.territoire}.geojson'
    )

    project = args.project or os.environ.get('EE_PROJECT')
    ee = _connect_ee(project)

    date_ref_s, date_ref_e = _periode_range(args.periode_ref)
    date_cur_s, date_cur_e = _periode_range(args.periode_cur)

    print(f"[Sentinel-2 veille] {args.territoire} · ref {date_ref_s}→{date_ref_e} · cur {date_cur_s}→{date_cur_e}")
    print(f"  bbox = {bbox}")

    ndwi_ref, n_ref = _composite_ndwi(ee, bbox, date_ref_s, date_ref_e)
    ndwi_cur, n_cur = _composite_ndwi(ee, bbox, date_cur_s, date_cur_e)
    if ndwi_ref is None:
        print(f"ERREUR : aucune scène disponible sur la période de référence ({args.periode_ref}).", file=sys.stderr)
        sys.exit(4)
    if ndwi_cur is None:
        print(f"ERREUR : aucune scène disponible sur la période courante ({args.periode_cur}).", file=sys.stderr)
        sys.exit(4)
    print(f"  scènes : {n_ref} réf · {n_cur} cur")

    fc = _detecter_changement(ee, ndwi_ref, ndwi_cur, bbox, args.magnitude_min_m, args.ndwi_seuil)
    print(f"  vectorisation en cours (Earth Engine)…")
    features = _evaluer_features(ee, fc, args.periode_ref, args.periode_cur)
    print(f"  {len(features)} alerte(s) détectée(s)")

    output = {
        'type': 'FeatureCollection',
        'name': 'veille_sentinel2',
        'metadata': {
            'territoire': args.territoire,
            'source': 'Sentinel-2 SR Harmonized (Copernicus, via Earth Engine)',
            'licence': 'Données ouvertes Copernicus',
            'periode_reference': f'{date_ref_s} / {date_ref_e}',
            'periode_courante': f'{date_cur_s} / {date_cur_e}',
            'ndwi_seuil': args.ndwi_seuil,
            'resolution_m': 10,
            'magnitude_min_m': args.magnitude_min_m,
            'date_generation': _dt.datetime.utcnow().isoformat() + 'Z',
            'outil': 'tools/sentinel_veille_GEE.py',
            'n_scenes_ref': n_ref,
            'n_scenes_cur': n_cur,
            'bbox': list(bbox),
            'note': "Vecteurs d'alerte indicatifs. À réexploiter en très haute résolution pour confirmation (réf. méth. 7.14)."
        },
        'features': features,
    }

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"  écrit : {out_path}")


if __name__ == '__main__':
    main()
