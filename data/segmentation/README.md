# Segmentation profonde — Lot B2 (raffineur sur Sentinel-2)

Sorties du script `tools/prithvi_segmentation.py` : un fichier `.geojson` par territoire contenant les contours produits par un modèle de fondation géospatial (Prithvi-EO-2.0, NASA/IBM) appliqué à des composites Sentinel-2 SR Harmonized.

## Position dans la chaîne (réf. méth. 7.9)

> *Le résultat profond alimente le même rôle de raffineur et de contrôle que l'existant (A3.3) ; il ne devient pas un détecteur autonome non supervisé.*

Ces masques ne remplacent pas la détection heuristique de la plateforme : ils **vérifient** et **complètent** la délimitation côtière, notamment **là où les archives THR manquent** (Wallis, Polynésie hors sites pilotes).

## Schéma `{territoire}.geojson`

```jsonc
{
  "type": "FeatureCollection",
  "name": "segmentation_prithvi",
  "metadata": {
    "territoire": "wallis",
    "modele": "ibm-nasa-geospatial/Prithvi-EO-2.0",
    "version_modele": "300M",
    "source_imagerie": "Sentinel-2 SR Harmonized (Copernicus, via Earth Engine)",
    "licence_imagerie": "Données ouvertes Copernicus",
    "licence_modele": "Apache 2.0 (à confirmer auprès du dépôt Hugging Face)",
    "periode": "2025-01-01 / 2025-06-30",
    "bandes": ["B02", "B03", "B04", "B05", "B06", "B07"],
    "resolution_m": 10,
    "classes": ["eau", "terre", "sable", "vegetation"],
    "date_generation": null,
    "outil": "tools/prithvi_segmentation.py",
    "statut": "vide — aucun run effectué."
  },
  "features": []
}
```

Chaque feature :

```jsonc
{
  "type": "Feature",
  "geometry": { "type": "LineString" | "Polygon", "coordinates": [...] },
  "properties": {
    "classe": "eau" | "terre" | "sable" | "vegetation",
    "confiance": 0.92,
    "date_acquisition": "2025-03-15",
    "scene_id": "S2A_MSIL2A_..."
  }
}
```

## Rafraîchissement

Voir `tools/README.md`. Prithvi-EO-2.0 demande **GPU** pour exécution rapide (sinon CPU, lent). Trois pistes :

1. **Notebook Colab gratuit** avec GPU T4 → exécution ad hoc, téléchargement du fichier produit.
2. **Hugging Face Inference Endpoint** → quota gratuit limité, suffisant pour ~1 dalle/jour.
3. **Instance GPU à la demande** (Lambda Cloud, RunPod) facturée à l'heure → traitement par lot ponctuel.

Tant qu'aucun opérateur n'a tourné l'outil, les six fichiers restent **vides** et l'interface affiche `(0)` sans inventer de donnée.
