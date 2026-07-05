# Tests d'intégration

## SAM (Segment Anything Model)

Validation end-to-end du module SAM ajouté dans la plateforme.

### Prérequis
```bash
cd /tmp
npm install @huggingface/transformers@3.0.2 onnxruntime-node
```

### Tests

**`test_sam_e2e.cjs`** — vérifie le chargement du modèle, l'encoding image, et la prédiction sur 2 points (clic mer + clic terre). Mesure les temps et les scores IoU.

**`test_sam_pipeline.cjs`** — chaîne complète : SAM → masque → `keepSeaComponents` + `fillWaterHoles` + `shorelinesFromMask` + `smoothChaikin` + `pxToGeo` → GeoJSON. Vérifie la cohérence des contours produits avec la bbox WGS84.

### Résultats de référence (Nouméa, dalle 1024×1024)

- Chargement modèle (cache) : ~1 s
- Encoding image : ~1,2 s (CPU Node)
- Inférence par clic : 1-2,5 s (CPU Node) — 5 à 10× plus rapide en WebGPU navigateur
- Clic lagon (50,50) : score IoU **0,986**, couverture 33,7%, pixel dans le masque ✓
- Pipeline complet : 1 contour propre (1540 m, 296 points), aucun trait fractal

### Modèle utilisé

`Xenova/slimsam-77-uniform` (Hugging Face), SlimSAM-77 ONNX optimisé pour navigateur, ~40 Mo, sous licence Apache 2.0 (à vérifier au dépôt).
