#!/usr/bin/env python3
"""Génère un masque « bande littorale » par territoire depuis OpenStreetMap coastline.

Interroge Overpass pour les ways tagués natural=coastline dans une bbox élargie,
projette en métrique locale (UTM le plus pertinent), bufferise de ±N mètres,
reprojete en WGS84 et exporte en GeoJSON.

Usage : python gen_masque_cote.py
"""
import json, time, sys, os
import requests
from shapely.geometry import shape, MultiLineString, LineString, MultiPolygon, mapping
from shapely.ops import unary_union, transform
from pyproj import Transformer

OUT_DIR = '/home/user/formation-resilience-littoral/data/masque_cote'
TAMPON_M = 500   # tampon de chaque côté (terre et mer) → bande totale de 1 km

# Bboxes (south, west, north, east) Overpass format + EPSG métrique le plus pertinent
TERRITOIRES = {
    'spm':      {'bbox': (46.65, -56.50, 47.20, -56.05), 'epsg': 32621, 'nom': 'Saint-Pierre-et-Miquelon'},
    'wallis':   {'bbox': (-14.45, -178.30, -13.20, -176.00), 'epsg': 32701, 'nom': 'Wallis-et-Futuna (Wallis + Futuna + Alofi)'},
    'nc':       {'bbox': (-22.85, 163.50, -19.40, 168.40), 'epsg': 32758, 'nom': 'Nouvelle-Calédonie (Grande Terre + Loyauté)'},
    'stmartin': {'bbox': (18.00, -63.20, 18.15, -63.00), 'epsg': 32620, 'nom': 'Saint-Martin'},
    'stbarth':  {'bbox': (17.85, -62.92, 17.95, -62.78), 'epsg': 32620, 'nom': 'Saint-Barthélemy'},
    'pf':       {'bbox': (-18.00, -152.20, -16.40, -148.00), 'epsg': 32706, 'nom': 'Polynésie française (Société)'},
}

def overpass_query(s, w, n, e):
    """Construit une requête Overpass pour les coastlines dans la bbox."""
    return f"""[out:json][timeout:60];
(way["natural"="coastline"]({s},{w},{n},{e}););
out geom;"""

def fetch_coastline(s, w, n, e, retries=3):
    """Récupère les coastlines via Overpass, ressaie en cas d'erreur."""
    # Miroir français (overpass-api.de répond 406 dans certains environnements proxy)
    url = 'https://overpass.openstreetmap.fr/api/interpreter'
    q = overpass_query(s, w, n, e)
    for attempt in range(retries):
        try:
            r = requests.post(
                url,
                data={'data': q},
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'User-Agent': 'masque-cote-generator/1.0 (formation-resilience-littoral; territoires d outre mer)'
                },
                timeout=180
            )
            if r.status_code == 200:
                return r.json()
            print(f'    HTTP {r.status_code}, retry {attempt+1}/{retries}', file=sys.stderr)
        except Exception as ex:
            print(f'    Erreur réseau : {ex}, retry {attempt+1}/{retries}', file=sys.stderr)
        time.sleep(8)
    return None

def overpass_to_geojson(osm):
    """Convertit la réponse Overpass en MultiLineString shapely."""
    if not osm or 'elements' not in osm:
        return None
    lines = []
    for el in osm['elements']:
        if el.get('type') != 'way' or 'geometry' not in el:
            continue
        coords = [(p['lon'], p['lat']) for p in el['geometry']]
        if len(coords) >= 2:
            lines.append(LineString(coords))
    if not lines:
        return None
    return MultiLineString(lines)

def generer_masque(key, conf):
    print(f'  [{key}] {conf["nom"]}')
    s, w, n, e = conf['bbox']
    print(f'    bbox = ({s}, {w}, {n}, {e})')
    osm = fetch_coastline(s, w, n, e)
    if not osm:
        print(f'    ✗ Échec récupération Overpass')
        return None
    print(f'    {len(osm.get("elements",[]))} way(s) coastline trouvé(s)')
    mls = overpass_to_geojson(osm)
    if not mls or mls.is_empty:
        print(f'    ✗ Aucune coastline exploitable')
        return None
    # Projeter en métrique
    to_metric = Transformer.from_crs('EPSG:4326', f'EPSG:{conf["epsg"]}', always_xy=True).transform
    to_wgs84 = Transformer.from_crs(f'EPSG:{conf["epsg"]}', 'EPSG:4326', always_xy=True).transform
    mls_m = transform(to_metric, mls)
    # Buffer ±TAMPON_M → bande littorale
    bande_m = mls_m.buffer(TAMPON_M, cap_style='round', join_style='round')
    bande_wgs = transform(to_wgs84, bande_m)
    # Stats
    longueur_km = mls_m.length / 1000.0
    surface_km2 = bande_m.area / 1e6
    print(f'    coastline = {longueur_km:.1f} km · bande ±{TAMPON_M} m = {surface_km2:.1f} km²')
    # FeatureCollection
    fc = {
        'type': 'FeatureCollection',
        'name': f'masque_cote_{key}',
        'metadata': {
            'territoire': key, 'nom': conf['nom'],
            'source': 'OpenStreetMap (natural=coastline), via Overpass API',
            'licence': 'ODbL (OpenStreetMap)',
            'tampon_m': TAMPON_M, 'epsg_metrique': conf['epsg'],
            'longueur_coastline_km': round(longueur_km, 1),
            'surface_bande_km2': round(surface_km2, 1),
            'date_generation': time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'usage': "Filtrage géographique des extractions SIG : ne retenir que les features qui touchent cette bande littorale. Évite les traits parasites dans les terres ou en pleine mer."
        },
        'features': [{
            'type': 'Feature',
            'geometry': mapping(bande_wgs),
            'properties': {'type': 'bande_littorale', 'tampon_m': TAMPON_M}
        }]
    }
    out_path = os.path.join(OUT_DIR, f'{key}.geojson')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(fc, f, ensure_ascii=False)
    sz_ko = os.path.getsize(out_path) // 1024
    print(f'    ✓ écrit {out_path} ({sz_ko} ko)')
    return out_path

if __name__ == '__main__':
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f'=== Génération masques côtiers (tampon ±{TAMPON_M} m, source OSM) ===\n')
    for key, conf in TERRITOIRES.items():
        generer_masque(key, conf)
        time.sleep(2)   # courtoisie envers Overpass
        print()
