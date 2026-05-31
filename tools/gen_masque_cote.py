#!/usr/bin/env python3
"""Génère un masque côtier ASYMÉTRIQUE + zones de port à exclure (v2).

Améliorations vs v1 :
1. Tampon asymétrique : +500 m côté mer (large, garde-fou), +100 m côté terre
   (étroit, évite les routes intérieures parallèles).
2. Polygonisation des coastlines OSM en polygones de terre via shapely
   (utilise la convention OSM : terre à droite quand on suit le trait).
3. Récupération des zones de port (harbour, marina, pier, ferry_terminal,
   landuse=industrial+port) → ajoutées comme features d'exclusion pour
   ignorer les bateaux à quai.

Usage : python gen_masque_cote.py
Sortie : data/masque_cote/{territoire}.geojson — FeatureCollection avec
  · Feature 1 : bande littorale (Polygon/MultiPolygon)
  · Features suivantes : zones de port à exclure (Polygon)
"""
import json, time, sys, os
import requests
from shapely.geometry import shape, MultiLineString, LineString, Polygon, MultiPolygon, mapping
from shapely.ops import unary_union, polygonize, transform
from pyproj import Transformer

OUT_DIR = '/home/user/formation-resilience-littoral/data/masque_cote'
TAMPON_MER_M = 200   # bande côté mer : réduite à 200 m pour resserrer la zone de recherche
TAMPON_TERRE_M = 100
SIMPLIF_M = 30       # simplification plus fine, bande plus étroite

TERRITOIRES = {
    'spm':      {'bbox': (46.65, -56.50, 47.20, -56.05), 'epsg': 32621, 'nom': 'Saint-Pierre-et-Miquelon'},
    'wallis':   {'bbox': (-14.45, -178.30, -13.20, -176.00), 'epsg': 32701, 'nom': 'Wallis-et-Futuna'},
    'nc':       {'bbox': (-22.85, 163.50, -19.40, 168.40), 'epsg': 32758, 'nom': 'Nouvelle-Calédonie'},
    'stmartin': {'bbox': (18.00, -63.20, 18.15, -63.00), 'epsg': 32620, 'nom': 'Saint-Martin'},
    'stbarth':  {'bbox': (17.85, -62.92, 17.95, -62.78), 'epsg': 32620, 'nom': 'Saint-Barthélemy'},
    'pf':       {'bbox': (-18.00, -152.20, -16.40, -148.00), 'epsg': 32706, 'nom': 'Polynésie française (Société)'},
}

OVERPASS = 'https://overpass.openstreetmap.fr/api/interpreter'
HEADERS = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'User-Agent': 'masque-cote-generator/2.0 (formation-resilience-littoral)'
}

def overpass_post(q, retries=3, timeout=180):
    for attempt in range(retries):
        try:
            r = requests.post(OVERPASS, data={'data': q}, headers=HEADERS, timeout=timeout)
            if r.status_code == 200:
                return r.json()
            print(f'    HTTP {r.status_code}, retry {attempt+1}/{retries}', file=sys.stderr)
        except Exception as ex:
            print(f'    Erreur : {ex}, retry {attempt+1}/{retries}', file=sys.stderr)
        time.sleep(10)
    return None

def fetch_coastline(s, w, n, e):
    q = f'[out:json][timeout:90];(way["natural"="coastline"]({s},{w},{n},{e}););out geom;'
    return overpass_post(q)

def fetch_ports(s, w, n, e):
    q = f'''[out:json][timeout:90];
(
  way["harbour"="yes"]({s},{w},{n},{e});
  relation["harbour"="yes"]({s},{w},{n},{e});
  way["leisure"="marina"]({s},{w},{n},{e});
  relation["leisure"="marina"]({s},{w},{n},{e});
  way["man_made"="pier"]({s},{w},{n},{e});
  way["amenity"="ferry_terminal"]({s},{w},{n},{e});
  way["industrial"="port"]({s},{w},{n},{e});
);
out geom;'''
    return overpass_post(q)

def osm_ways_to_lines(osm):
    lines = []
    if not osm:
        return lines
    for el in osm.get('elements', []):
        if el.get('type') != 'way' or 'geometry' not in el:
            continue
        coords = [(p['lon'], p['lat']) for p in el['geometry']]
        if len(coords) >= 2:
            lines.append(LineString(coords))
    return lines

def osm_ways_to_polygons(osm):
    polys = []
    if not osm:
        return polys
    for el in osm.get('elements', []):
        if el.get('type') not in ('way', 'relation'):
            continue
        tags = el.get('tags', {})
        if el.get('type') == 'way' and 'geometry' in el:
            coords = [(p['lon'], p['lat']) for p in el['geometry']]
            if len(coords) < 2:
                continue
            if tags.get('man_made') == 'pier':
                polys.append(('pier', LineString(coords)))
            elif len(coords) >= 4 and coords[0] == coords[-1]:
                try:
                    polys.append(('zone', Polygon(coords)))
                except Exception:
                    pass
        elif el.get('type') == 'relation' and 'members' in el:
            outer_lines = []
            for m in el.get('members', []):
                if m.get('role') == 'outer' and m.get('type') == 'way' and 'geometry' in m:
                    cc = [(p['lon'], p['lat']) for p in m['geometry']]
                    if len(cc) >= 2:
                        outer_lines.append(LineString(cc))
            if outer_lines:
                try:
                    union = unary_union(outer_lines)
                    for p in polygonize(union):
                        polys.append(('zone', p))
                except Exception:
                    pass
    return polys

def construire_terre(lines_m):
    """Polygonise les coastlines (en métrique) en polygones de terre."""
    if not lines_m:
        return None
    merged = unary_union(lines_m)
    try:
        polys = list(polygonize(merged))
    except Exception:
        polys = []
    polys = [p for p in polys if p.area > 100]  # ignore micro-artefacts (< 100 m²)
    if not polys:
        return None
    return unary_union(polys) if len(polys) > 1 else polys[0]

def generer(key, conf):
    print(f'  [{key}] {conf["nom"]}')
    s, w, n, e = conf['bbox']

    osm_coast = fetch_coastline(s, w, n, e)
    if not osm_coast:
        print(f'    ✗ Overpass coastline vide'); return None
    lines = osm_ways_to_lines(osm_coast)
    print(f'    coastline : {len(lines)} way(s)')
    if not lines:
        return None
    time.sleep(2)

    osm_ports = fetch_ports(s, w, n, e)
    raw_polys = osm_ways_to_polygons(osm_ports) if osm_ports else []
    print(f'    port/marina : {len(raw_polys)} géométrie(s)')

    to_m = Transformer.from_crs('EPSG:4326', f'EPSG:{conf["epsg"]}', always_xy=True).transform
    to_w = Transformer.from_crs(f'EPSG:{conf["epsg"]}', 'EPSG:4326', always_xy=True).transform

    lines_m = [transform(to_m, l) for l in lines]
    terre = construire_terre(lines_m)
    if terre is None or terre.is_empty:
        print(f'    ⚠ polygonisation échouée → fallback buffer symétrique')
        bande = unary_union(lines_m).buffer(TAMPON_MER_M, cap_style='round', join_style='round')
    else:
        print(f'    terre polygonisée : {terre.area / 1e6:.1f} km²')
        terre_ext = terre.buffer(TAMPON_MER_M, cap_style='round', join_style='round')
        terre_int = terre.buffer(-TAMPON_TERRE_M, cap_style='round', join_style='round')
        if terre_int.is_empty:
            bande = terre_ext.difference(terre)
            print(f'    île trop petite pour érosion {TAMPON_TERRE_M} m → bande = couronne mer uniquement')
        else:
            bande = terre_ext.difference(terre_int)
    bande = bande.simplify(SIMPLIF_M, preserve_topology=True)
    if bande.is_empty:
        print(f'    ✗ bande vide'); return None
    bande_wgs = transform(to_w, bande)
    bande_km2 = bande.area / 1e6
    print(f'    bande +{TAMPON_MER_M}m mer / +{TAMPON_TERRE_M}m terre = {bande_km2:.1f} km²')

    port_polys_m = []
    for kind, g in raw_polys:
        g_m = transform(to_m, g)
        if kind == 'pier':
            g_m = g_m.buffer(15, cap_style='flat')
        port_polys_m.append(g_m)
    if port_polys_m:
        ports_union = unary_union(port_polys_m).buffer(20)
        ports_union = ports_union.simplify(10, preserve_topology=True)
        ports_wgs = transform(to_w, ports_union)
        ports_km2 = ports_union.area / 1e6
        print(f'    zones port à exclure (+20 m marge) : {ports_km2:.3f} km²')
    else:
        ports_wgs = None

    features = [{
        'type': 'Feature',
        'geometry': mapping(bande_wgs),
        'properties': {'type': 'bande_littorale', 'tampon_mer_m': TAMPON_MER_M, 'tampon_terre_m': TAMPON_TERRE_M}
    }]
    if ports_wgs is not None and not ports_wgs.is_empty:
        features.append({
            'type': 'Feature',
            'geometry': mapping(ports_wgs),
            'properties': {'type': 'zone_port_exclue', 'description': 'Ports/marinas/jetées OSM + marge 20 m — détections ignorées'}
        })

    fc = {
        'type': 'FeatureCollection',
        'name': f'masque_cote_{key}',
        'metadata': {
            'territoire': key, 'nom': conf['nom'],
            'source': 'OpenStreetMap (natural=coastline + harbour/marina/pier), via Overpass',
            'licence': 'ODbL (OpenStreetMap)',
            'version': 'v2-asymetrique',
            'tampon_mer_m': TAMPON_MER_M,
            'tampon_terre_m': TAMPON_TERRE_M,
            'epsg_metrique': conf['epsg'],
            'simplification_tolerance_m': SIMPLIF_M,
            'surface_bande_km2': round(bande_km2, 2),
            'nb_zones_port': len(port_polys_m),
            'date_generation': time.strftime('%Y-%m-%dT%H:%M:%SZ'),
        },
        'features': features
    }
    out_path = os.path.join(OUT_DIR, f'{key}.geojson')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(fc, f, ensure_ascii=False)
    sz_ko = os.path.getsize(out_path) // 1024
    print(f'    ✓ écrit {out_path} ({sz_ko} ko)')
    return out_path

if __name__ == '__main__':
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f'=== Masques côtiers v2 (asymétrique +{TAMPON_MER_M}m mer / +{TAMPON_TERRE_M}m terre + ports) ===\n')
    for key, conf in TERRITOIRES.items():
        generer(key, conf)
        time.sleep(3)
        print()
