# Outils hors ligne — Lot B1 (veille satellitaire)

Scripts à exécuter hors ligne pour rafraîchir les vecteurs d'alerte de changement consommés par la plateforme. Les sorties sont déposées dans `data/alerts/` et lues directement par le navigateur (aucun serveur permanent, voir le plan d'implémentation).

## Scripts

### `sentinel_veille_GEE.py` — Earth Engine

Détecte les changements de rivage entre deux périodes en composant des médianes Sentinel-2 SR Harmonized, NDWI, et vectorise les zones où le rivage a bougé de ≥ N pixels.

**Prérequis**

```bash
pip install earthengine-api
earthengine authenticate
```

Cela crée un compte recherche / non commercial sur Earth Engine (gratuit dans le cadre Code de l'environnement, voir `https://earthengine.google.com/noncommercial/`). Un projet GCP doit être associé à l'usage Earth Engine (variable `EE_PROJECT` ou option `--project`).

**Exécution**

```bash
python tools/sentinel_veille_GEE.py \
  --territoire wallis \
  --periode_ref 2020 \
  --periode_cur 2025 \
  --magnitude_min_m 20
```

Sortie : `data/alerts/wallis.geojson` (FeatureCollection respectant le schéma documenté dans `data/alerts/README.md`).

**Coût** : exécution côté Google (gratuite). Le script ne télécharge que la géométrie résultat (quelques ko à mo).

### `prithvi_segmentation.py` — Segmentation profonde Prithvi-EO-2.0

Applique le modèle de fondation géospatial **Prithvi-EO-2.0** (NASA/IBM, arXiv:2412.02732) à un composite Sentinel-2 SR Harmonized, et produit des contours côtiers vectorisés (terre, sable, végétation).

**Position dans la chaîne (réf. méth. 7.9 / A3.3)** : le résultat est un **raffineur de contrôle**, jamais un détecteur autonome. Particulièrement utile pour Wallis et la Polynésie hors sites pilotes (faute d'archives THR).

**Prérequis**

```bash
pip install earthengine-api transformers accelerate torch rasterio shapely geopandas
earthengine authenticate
huggingface-cli login    # ou : export HF_TOKEN=...
```

**Modes d'inférence**

| Mode | Coût | Quand l'utiliser |
|---|---|---|
| `--inference local` | GPU local ou Colab gratuit T4 | dalle de territoire, exécution ad hoc |
| `--inference hf` | Quota gratuit HF Inference Endpoint (configurer `HF_PRITHVI_ENDPOINT`) | volumes faibles sans GPU |

**Exécution**

```bash
python tools/prithvi_segmentation.py \
  --territoire wallis \
  --periode 2025-01-01 2025-06-30 \
  --inference local
```

Sortie : `data/segmentation/wallis.geojson` (contours par classe).

**Note de licence** : Prithvi-EO-2.0 est distribué sous Apache 2.0 selon le dépôt Hugging Face — à vérifier au moment de l'usage opérationnel. Les bandes Sentinel-2 sont en données ouvertes Copernicus.

## Articulation hiérarchique (réf. méth. 7.14)

1. **Sentinel-2 (10 m, revisite 5 j)** — alerte de changement (ce dossier).
2. **Landsat (30 m, archives 1984+)** — tendance de long terme (à venir).
3. **Très haute résolution** (ortho IGN, Pléiades, Esri) — confirmation et mesure dans l'app principale.

Une alerte Sentinel-2 *signale où réexploiter la THR* ; elle ne mesure pas le trait de côte fin.

## Rafraîchissement périodique

Plusieurs options, à choisir selon les moyens de l'opérateur :

- **Manuel** : exécuter le script à la demande (par exemple après un cyclone) sur chacun des six territoires.
- **GitHub Actions** (suggéré, non activé par défaut faute de credentials dans le dépôt) : un workflow planifié peut authentifier auprès d'Earth Engine via un secret `EE_PRIVATE_KEY` et committer les nouveaux fichiers automatiquement.
- **Notebook collaboratif** (Colab) : le script tourne dans une session Colab gratuite, qui télécharge le GeoJSON et le pousse via Git ou via un téléversement manuel.

## Sources documentaires

- Sentinel-2 SR Harmonized : `COPERNICUS/S2_SR_HARMONIZED` (Earth Engine).
- Programme Copernicus, conditions d'accès : `https://dataspace.copernicus.eu`.
- Méthode NDWI : McFeeters S.K. (1996), *Int. J. Remote Sensing* 17(7) ; révision Xu (2006) MNDWI pour zones urbaines.
- Articulation veille / mesure : Barnard P. et al. (2023), *Cambridge Prisms: Coastal Futures*, doi:10.1017/cft.2022.4.
