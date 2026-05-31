# Masques côtiers — bande littorale par territoire

Un fichier `.geojson` par territoire, contenant un **MultiPolygon de la bande littorale** (tampon ±500 m autour de la coastline OSM). Sert à **filtrer par construction** toutes les extractions de la plateforme : seuls les contours/ouvrages qui touchent cette bande sont retenus, les artefacts dans l'arrière-pays ou en pleine mer sont écartés.

## Effet attendu

Sur les lagons coralliens (Saint-Barthélemy, Tuamotu, etc.), même si l'heuristique pixel produit des contours fractals à l'intérieur des récifs, le filtre supprime tout ce qui est trop loin du vrai littoral. Combiné avec SAM, c'est une double sécurité : précision *intra*-bande (SAM) + sécurité *extra*-bande (masque).

## Schéma

```jsonc
{
  "type": "FeatureCollection",
  "name": "masque_cote_<terr>",
  "metadata": {
    "territoire": "stbarth",
    "nom": "Saint-Barthélemy",
    "source": "OpenStreetMap (natural=coastline), via Overpass API",
    "licence": "ODbL (OpenStreetMap)",
    "tampon_m": 500,
    "epsg_metrique": 32620,
    "longueur_coastline_km": 59.2,
    "surface_bande_km2": 43.5,
    "simplification_tolerance_m": 50,
    "date_generation": "...",
    "usage": "Filtrage géographique des extractions SIG..."
  },
  "features": [
    { "type": "Feature",
      "geometry": { "type": "MultiPolygon", "coordinates": [...] },
      "properties": { "type": "bande_littorale", "tampon_m": 500 } }
  ]
}
```

## Régénération

Le script `tools/gen_masque_cote.py` (à exécuter offline avec accès internet) interroge Overpass pour les coastlines OSM dans la bbox du territoire, les projette en UTM métrique local, applique un buffer de ±500 m, simplifie à 50 m, et écrit le fichier. Régénérer pour intégrer les mises à jour OSM ou ajuster le tampon.

## Couvertures actuelles

| Territoire | Coastline (km) | Bande (km²) | Fichier (ko) |
|---|---|---|---|
| Saint-Pierre-et-Miquelon | 217 | 161 | 24 |
| Wallis-et-Futuna | 142 | 126 | 24 |
| Nouvelle-Calédonie (Grande Terre + Loyauté) | 3 973 | 3 097 | 460 |
| Saint-Martin | 123 | 80 | 16 |
| Saint-Barthélemy | 59 | 43 | 12 |
| Polynésie française (Société) | 968 | 670 | 100 |

Total : ~640 ko pour les 6 territoires. Chargé une seule fois par territoire au moment du choix.

## Source et licence

Source : OpenStreetMap, données `natural=coastline`.
Licence : ODbL (Open Database License) — réutilisation libre avec attribution. À mentionner dans les exports dérivés.
