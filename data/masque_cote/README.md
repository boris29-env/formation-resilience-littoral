# Masques côtiers v2 — filtre interne de la chaîne d'extraction

Un fichier `.geojson` par territoire, **utilisé en interne par la plateforme** pour restreindre la zone de recherche des extractions (trait de côte, ouvrages, SAM, bandes de recul). **Non affiché sur la carte** — c'est un masque d'exclusion, pas un livrable.

## Géométrie

Chaque fichier contient deux features :

1. **Bande littorale asymétrique** : +200 m côté mer / +100 m côté terre, calculée par polygonisation des coastlines OSM puis différence `terre.buffer(+200) − terre.buffer(−100)`.
2. **Zones de port à exclure** : marinas, ports, jetées, ferries (OSM `harbour`, `leisure=marina`, `man_made=pier`, `amenity=ferry_terminal`, `industrial=port`), avec marge +20 m. Sert à ignorer les bateaux à quai et les jetées prises pour des traits.

## Couvertures actuelles (bandes +200/+100 m)

| Territoire | Coastline | Terre | Bande | Ports | Fichier |
|---|---|---|---|---|---|
| Saint-Pierre-et-Miquelon | 83 ways | 231 km² | 55 km² | 47 | 52 ko |
| Wallis-et-Futuna | 24 ways | 141 km² | 40 km² | 6 | 40 ko |
| Nouvelle-Calédonie | 1 142 ways | 18 536 km² | 1 054 km² | 401 | 1 042 ko |
| Saint-Martin | 210 ways | 82 km² | 30 km² | 413 | 65 ko |
| Saint-Barthélemy | 33 ways | 20 km² | 15 km² | 6 | 21 ko |
| Polynésie (Société) | 590 ways | 1 568 km² | 237 km² | 852 | 373 ko |

## Régénération

`tools/gen_masque_cote.py` (Overpass + shapely + pyproj). Ajuster `TAMPON_MER_M` (200 par défaut) ou `TAMPON_TERRE_M` (100) en tête de script.

## Source et licence

OpenStreetMap, données `natural=coastline` + `harbour/marina/pier/ferry/port`. Licence ODbL.
