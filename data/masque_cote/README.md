# Masques côtiers v3 — bande étroite ±30 m, ports soustraits

Un fichier `.geojson` par territoire, utilisé **en interne** par la plateforme pour restreindre la zone de recherche des extractions. Non affiché sur la carte.

## Géométrie (v3)

Chaque fichier contient deux features :

1. **Bande littorale étroite** : ±30 m de part et d'autre du trait de côte OSM, ports **soustraits** (on ne cherche pas dedans). Calculée par polygonisation des coastlines OSM puis `(terre.buffer(+30) − terre.buffer(−30)) − ports.buffer(+20)`.
2. **Zones de port** : marinas, ports, jetées, ferries (OSM `harbour`, `leisure=marina`, `man_made=pier`, `amenity=ferry_terminal`, `industrial=port`). Stockées pour traçabilité (déjà soustraites du masque).

## Couvertures actuelles (bandes ±30 m, ports exclus)

| Territoire | Coastline | Terre | Bande finale | Ports | Fichier |
|---|---|---|---|---|---|
| Saint-Pierre-et-Miquelon | 83 ways | 231 km² | **12 km²** | 47 | 166 ko |
| Wallis-et-Futuna | 24 ways | 141 km² | **8 km²** | 6 | 99 ko |
| Nouvelle-Calédonie | 1 142 ways | 18 536 km² | **225 km²** | 401 | 2 950 ko |
| Saint-Martin | 210 ways | 82 km² | **6 km²** | 413 | 156 ko |
| Saint-Barthélemy | 33 ways | 20 km² | **3 km²** | 6 | 56 ko |
| Polynésie (Société) | 590 ways | 1 568 km² | **50 km²** | 852 | 972 ko |

La bande est désormais aussi étroite qu'un seul couloir centré sur le trait OSM. Les ports y sont des trous (pas de fausses détections sur les bateaux à quai).

## Régénération

`tools/gen_masque_cote.py` — `TAMPON_MER_M=30`, `TAMPON_TERRE_M=30`, `SIMPLIF_M=10`. Modifier en tête pour ajuster.

## Source et licence

OpenStreetMap, `natural=coastline` + `harbour/marina/pier/ferry/port`. Licence ODbL.
