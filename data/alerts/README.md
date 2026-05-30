# Veille satellitaire Sentinel-2 — vecteurs d'alerte (Lot B1)

Ce dossier contient les vecteurs d'alerte de changement détectés sur Sentinel-2 (10 m) pour chacun des six territoires de la plateforme. Un fichier `.geojson` par territoire, lu directement par le navigateur via `chargerVeilleSentinel(key)`.

## Logique d'usage (réf. méth. 7.14)

Articulation hiérarchique :
- **Sentinel-2 (10 m, revisite 5 jours)** — *alerte de changement* (ce dossier).
- **Landsat (30 m, archives 1984+)** — tendance de long terme (Lot B futur).
- **Très haute résolution** (ortho IGN, Pléiades, Esri) — *confirmation et mesure fine* dans l'app principale.

Une alerte Sentinel-2 **signale où réexploiter la THR** ; elle ne mesure pas le trait de côte fin elle-même.

## Schéma des fichiers `{territoire}.geojson`

```jsonc
{
  "type": "FeatureCollection",
  "name": "veille_sentinel2",
  "metadata": {
    "territoire": "wallis",
    "source": "Sentinel-2 SR Harmonized (Copernicus, via Earth Engine ou Copernicus Data Space)",
    "licence": "Données ouvertes Copernicus",
    "periode_reference": "2020-01-01 / 2020-12-31",
    "periode_courante": "2025-01-01 / 2025-06-30",
    "ndwi_seuil": 0.0,
    "resolution_m": 10,
    "magnitude_min_m": 20,
    "date_generation": "2026-05-30T18:00:00Z",
    "outil": "tools/sentinel_veille_GEE.py",
    "note": "Vecteurs d'alerte indicatifs. Chaque alerte signale une zone où le rivage a bougé d'au moins 20 m entre les deux périodes. À réexploiter en très haute résolution pour confirmation."
  },
  "features": [
    {
      "type": "Feature",
      "geometry": { "type": "LineString", "coordinates": [[lon, lat], …] },
      "properties": {
        "alerte_type": "recul" | "avancee" | "changement",
        "magnitude_m": 35,
        "priorite": "haute" | "moyenne" | "basse",
        "periode_ref": "2020",
        "periode_cur": "2025",
        "ndwi_delta": -0.18,
        "secteur_nom": "Sud de Mata-Utu",
        "note": "Segment côtier au sud de Mata-Utu, recul ~35 m sur 5 ans"
      }
    }
  ]
}
```

## Rafraîchissement

Voir `tools/README.md`. En résumé :
1. Authentifier auprès d'Earth Engine (compte recherche, gratuit) ou de Copernicus Data Space.
2. Exécuter `python tools/sentinel_veille_GEE.py --territoire {key} --periode_ref 2020 --periode_cur 2025`.
3. Le script écrit `data/alerts/{key}.geojson` ; on commit, on push.

Le navigateur consomme la donnée au prochain chargement du territoire. Aucun serveur permanent, aucune infrastructure dédiée.

## Statut initial

Les six fichiers sont initialement **vides** (aucune `feature`) avec une `metadata.note` explicite. Le navigateur affiche alors « aucune alerte de changement enregistrée — exécutez `tools/sentinel_veille_GEE.py` pour rafraîchir ». Tant qu'un opérateur n'a pas exécuté le script, on ne montre rien plutôt que d'inventer.
