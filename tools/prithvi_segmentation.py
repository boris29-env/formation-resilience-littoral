#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Segmentation profonde côtière (Lot B2) via Prithvi-EO-2.0 (NASA/IBM,
arXiv:2412.02732, déc. 2024) sur composite Sentinel-2 SR Harmonized.

Référence méthodologique : 7.9 (modèles de fondation pour la délimitation
côtière, F1>0,94 IoU>0,79 sur Maldives avec 5 images d'entraînement,
arXiv:2511.10177 nov. 2025).

Position dans la chaîne (réf. méth. A3.3 et 7.9)
------------------------------------------------
Le résultat alimente le RAFFINEUR côté navigateur, jamais un détecteur
autonome. Les contours produits sont déposés dans data/segmentation/
et superposables sur la carte pour CONTRÔLE de plausibilité.

Logique
-------
1. Charger Sentinel-2 SR Harmonized depuis Earth Engine sur l'emprise du
   territoire (filtre nuage < 20 %).
2. Composite médian sur la période.
3. Extraire 6 bandes attendues par Prithvi : B02, B03, B04, B05, B06, B07
   (visible + red edge + 2 SWIR).
4. Exporter en GeoTIFF multibande (≤ 512×512 pour rester dans les quotas).
5. Inférence Prithvi-EO-2.0 (locale GPU ou Hugging Face Inference).
6. Vectorisation des contours par classe (eau / terre / sable / végétation).
7. Sortie GeoJSON dans data/segmentation/{territoire}.geojson.

Coût (réf. plan B 2.3)
----------------------
· Earth Engine : gratuit (recherche / non-commercial).
· Inférence Prithvi :
    - locale GPU : machine éphémère à la demande (allumée le temps du run, éteinte).
    - notebook Colab gratuit T4 : suffit pour une dalle de territoire.
    - Hugging Face Inference Endpoint : quota gratuit limité.
· Poids du modèle (~1.2 Go) : téléchargés une fois, stockés en objet.

Prérequis
---------
    pip install earthengine-api transformers accelerate torch \\
                rasterio shapely geopandas
    earthengine authenticate
    huggingface-cli login   # ou export HF_TOKEN=...

Usage
-----
    python tools/prithvi_segmentation.py \\
        --territoire wallis \\
        --periode 2025-01-01 2025-06-30 \\
        --inference local

L'option `--inference hf` bascule sur Hugging Face Inference (plus lent
mais sans GPU local requis).
"""
import argparse
import json
import os
import sys
import datetime as _dt

# Bboxes par défaut (cohérentes avec sentinel_veille_GEE.py)
BBOX_TERR = {
    'spm':      (-56.55, 46.70, -56.10, 47.20),
    'wallis':   (-178.30, -13.50, -176.00, -14.45),
    'nc':       (163.50, -22.80, 168.30, -19.50),
    'stmartin': (-63.20, 18.00, -63.00, 18.15),
    'stbarth':  (-62.90, 17.85, -62.78, 17.95),
    'pf':       (-152.00, -18.00, -148.00, -16.50),
}

# Bandes Sentinel-2 attendues par Prithvi-EO-2.0 (cf. config du modèle Hugging Face)
S2_BANDS = ['B02', 'B03', 'B04', 'B05', 'B06', 'B07']

# Classes de sortie (mapping arbitraire — à ajuster selon le tête de segmentation utilisée)
CLASSES = {0: 'eau', 1: 'terre', 2: 'sable', 3: 'vegetation'}

MODEL_ID = 'ibm-nasa-geospatial/Prithvi-EO-2.0-300M'


def _connect_ee(project):
    """Initialise Earth Engine (cf. sentinel_veille_GEE.py)."""
    try:
        import ee  # type: ignore
    except ImportError:
        print('ERREUR : `pip install earthengine-api`.', file=sys.stderr)
        sys.exit(2)
    try:
        ee.Initialize(project=project) if project else ee.Initialize()
        return ee
    except Exception as e:
        print(f'ERREUR Earth Engine : {e}', file=sys.stderr)
        print('Tentative : `earthengine authenticate` puis relancez.', file=sys.stderr)
        sys.exit(3)


def _exporter_composite(ee, bbox, date_start, date_end, out_tiff):
    """Compose et exporte un Sentinel-2 SR Harmonized multibande en local."""
    geom = ee.Geometry.Rectangle(list(bbox))
    col = (
        ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        .filterBounds(geom)
        .filterDate(date_start, date_end)
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
        .select(S2_BANDS)
    )
    n = col.size().getInfo()
    if n == 0:
        return None, 0
    composite = col.median().clip(geom)
    url = composite.getDownloadURL({
        'scale': 10,
        'region': geom,
        'format': 'GEO_TIFF',
        'crs': 'EPSG:4326',
    })
    import urllib.request
    print(f'  téléchargement composite ({n} scènes)…')
    urllib.request.urlretrieve(url, out_tiff)
    return out_tiff, n


def _inference_locale(tiff_path):
    """Exécution Prithvi-EO-2.0 en local (GPU recommandé, sinon CPU lent)."""
    try:
        import torch  # type: ignore
        from transformers import AutoModel  # type: ignore
        import rasterio  # type: ignore
        import numpy as np  # type: ignore
    except ImportError as e:
        print(f'ERREUR : dépendance manquante ({e}). `pip install transformers torch rasterio`.', file=sys.stderr)
        sys.exit(2)
    print(f'  chargement modèle {MODEL_ID}…')
    model = AutoModel.from_pretrained(MODEL_ID, trust_remote_code=True)
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model = model.to(device).eval()
    with rasterio.open(tiff_path) as src:
        arr = src.read()  # (bands, H, W)
        transform = src.transform
        crs = src.crs
    # Prithvi attend (1, T, C, H, W) — T=1 pour image instantanée
    x = torch.from_numpy(arr).float().unsqueeze(0).unsqueeze(0).to(device)
    with torch.no_grad():
        out = model(x)
    # La sortie dépend de la tête de segmentation : ici on suppose une head ajoutée
    # produisant un logit (B, C, H, W). À adapter au modèle réellement utilisé.
    if hasattr(out, 'logits'):
        logits = out.logits
    else:
        logits = out
    if logits.dim() == 5:  # (B, T, C, H, W)
        logits = logits[:, 0]
    mask = logits.argmax(dim=1).squeeze(0).cpu().numpy()
    return mask, transform, crs


def _inference_hf(tiff_path):
    """Inférence via Hugging Face Inference Endpoint (à configurer côté HF)."""
    try:
        import requests  # type: ignore
    except ImportError:
        print('ERREUR : `pip install requests`.', file=sys.stderr)
        sys.exit(2)
    endpoint = os.environ.get('HF_PRITHVI_ENDPOINT')
    token = os.environ.get('HF_TOKEN')
    if not endpoint or not token:
        print('ERREUR : variables HF_PRITHVI_ENDPOINT et HF_TOKEN requises.', file=sys.stderr)
        sys.exit(3)
    with open(tiff_path, 'rb') as f:
        r = requests.post(
            endpoint,
            headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/octet-stream'},
            data=f.read(),
            timeout=300,
        )
    if r.status_code != 200:
        print(f'ERREUR HF : {r.status_code} {r.text[:200]}', file=sys.stderr)
        sys.exit(4)
    # Réponse attendue : {"mask": [[...]], "transform": [...], "crs": "EPSG:4326"}
    data = r.json()
    import numpy as np  # type: ignore
    from rasterio.transform import Affine  # type: ignore
    from rasterio.crs import CRS  # type: ignore
    mask = np.array(data['mask'], dtype=np.uint8)
    transform = Affine(*data['transform'])
    crs = CRS.from_string(data.get('crs', 'EPSG:4326'))
    return mask, transform, crs


def _vectoriser(mask, transform, crs, classes_map=None):
    """Vectorise un masque (H×W de labels entiers) en features GeoJSON par classe."""
    try:
        from rasterio.features import shapes  # type: ignore
        from shapely.geometry import shape  # type: ignore
    except ImportError:
        print('ERREUR : `pip install rasterio shapely`.', file=sys.stderr)
        sys.exit(2)
    classes_map = classes_map or CLASSES
    features = []
    for geom, val in shapes(mask.astype('int32'), transform=transform):
        cls = classes_map.get(int(val))
        if cls is None or cls == 'eau':
            continue  # on ne vectorise pas l'eau (volume), uniquement terre/sable/vegetation
        g = shape(geom)
        if g.is_empty or g.area < 1e-7:  # filtre micro-polygones
            continue
        features.append({
            'type': 'Feature',
            'geometry': g.__geo_interface__,
            'properties': {
                'classe': cls,
                'confiance': None,  # à enrichir si la tête produit une probabilité
                'methode': 'segmentation profonde Prithvi-EO-2.0 (NASA/IBM)',
            }
        })
    return features


def main():
    ap = argparse.ArgumentParser(description='Segmentation profonde Prithvi-EO-2.0 sur Sentinel-2')
    ap.add_argument('--territoire', required=True, choices=list(BBOX_TERR.keys()))
    ap.add_argument('--periode', nargs=2, metavar=('DEBUT', 'FIN'),
                    default=['2024-01-01', '2024-12-31'])
    ap.add_argument('--inference', choices=['local', 'hf'], default='local')
    ap.add_argument('--bbox', help='Bbox personnalisée : "ouest,sud,est,nord"')
    ap.add_argument('--out', help='Fichier de sortie (défaut : data/segmentation/{territoire}.geojson)')
    ap.add_argument('--project', help='Projet Earth Engine (sinon EE_PROJECT env)')
    ap.add_argument('--keep_tiff', action='store_true', help='Conserver le composite TIFF intermédiaire')
    args = ap.parse_args()

    bbox = BBOX_TERR[args.territoire]
    if args.bbox:
        bbox = tuple(float(x) for x in args.bbox.split(','))

    out_path = args.out or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'data', 'segmentation', f'{args.territoire}.geojson'
    )

    project = args.project or os.environ.get('EE_PROJECT')
    ee = _connect_ee(project)

    tmp_tiff = f'/tmp/prithvi_s2_{args.territoire}.tif'
    tiff, n = _exporter_composite(ee, bbox, args.periode[0], args.periode[1], tmp_tiff)
    if not tiff:
        print(f'ERREUR : aucune scène Sentinel-2 disponible sur la période.', file=sys.stderr)
        sys.exit(4)

    print(f'[Prithvi] inférence ({args.inference})…')
    if args.inference == 'local':
        mask, transform, crs = _inference_locale(tiff)
    else:
        mask, transform, crs = _inference_hf(tiff)

    print(f'  vectorisation…')
    features = _vectoriser(mask, transform, crs)
    print(f'  {len(features)} contour(s) produit(s)')

    output = {
        'type': 'FeatureCollection',
        'name': 'segmentation_prithvi',
        'metadata': {
            'territoire': args.territoire,
            'modele': MODEL_ID,
            'source_imagerie': 'Sentinel-2 SR Harmonized (Copernicus, via Earth Engine)',
            'licence_imagerie': 'Données ouvertes Copernicus',
            'licence_modele': 'Apache 2.0 (vérifier le dépôt Hugging Face)',
            'periode': f'{args.periode[0]} / {args.periode[1]}',
            'bandes': S2_BANDS,
            'resolution_m': 10,
            'classes': list(set(CLASSES.values())),
            'n_scenes': n,
            'date_generation': _dt.datetime.utcnow().isoformat() + 'Z',
            'outil': 'tools/prithvi_segmentation.py',
            'note': "Raffineur de contrôle de plausibilité — ne remplace pas la détection heuristique principale (réf. méth. 7.9 / A3.3)."
        },
        'features': features,
    }
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f'  écrit : {out_path}')

    if not args.keep_tiff and os.path.exists(tmp_tiff):
        os.remove(tmp_tiff)


if __name__ == '__main__':
    main()
