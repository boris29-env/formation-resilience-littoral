# Projets littoral et IGEDD

Ce dépôt regroupe plusieurs projets web statiques publiés sur GitHub Pages :
https://boris29-env.github.io/formation-resilience-littoral/

La page d'accueil (`index.html`) est un portail qui renvoie vers chaque projet. Chaque projet vit dans son propre dossier.

| Dossier | Projet | Adresse |
|---|---|---|
| `anse-goulven/` | Formation « Résilience du littoral » (7 h) : espace participant Anse-de-Goulven, images de montage, support `.pptx` | `/anse-goulven/` |
| `littus/` | LITTUS, atlas dynamique du trait de côte, avec ses données JSON (cellules sédimentaires, érosion Cerema) | `/littus/` |
| `suivi-cabinet/` | Kanban, journal et arbitrage du suivi cabinet | `/suivi-cabinet/kanban-suivi-cabinet.html` |
| `outils-igedd/` | Déclaration annuelle de compétences, trombinoscope | `/outils-igedd/masque-competences.html` |
| `worker/` | Worker Cloudflare `dialogue-1972`, utilisé par Anse-de-Goulven (déployé séparément avec `wrangler`) | |

## Visualiseur d'Anse-de-Goulven

Le visualiseur intégré à `anse-goulven/index.html` utilise MapLibre GL JS et les services de la Géoplateforme IGN. Il propose :

- le Plan IGN, l'orthophotographie ou une vue hybride ;
- une recherche dans les lieux et enjeux fictifs du cas pédagogique ;
- quatre compositions de couches : repérage, risques, vulnérabilités et préparation du PCS ;
- les couches de submersion, de recul du trait de côte, d'enjeux, de réseaux et d'itinéraires d'évacuation ;
- un calage des repères structurants sur la carte tactique du support (port au contact de la baie, marais arrière-littoral, digue côté terrestre) ;
- une simulation cartographique en cinq phases de la tempête Argonne, synchronisée avec la variante tirée, les perturbateurs et les conséquences des embûches révélées après le vote PCS.

Le pont JavaScript `window.GoulvenMap` expose `startCrisis()`, `setCrisisPhase(index)` et `stopCrisis()` pour piloter la carte depuis les séquences pédagogiques. Toutes les données propres au scénario restent fictives et sans valeur réglementaire ou opérationnelle.

## Anciennes adresses

Les pages étaient auparavant toutes à la racine. Les anciennes adresses du suivi cabinet (`kanban-suivi-cabinet.html`, `journal-suivi-cabinet.html`, `arbitrage-suivi-cabinet.html`) restent en place sous forme de petites pages de redirection, qui conservent les paramètres d'URL et l'ancre. Les liens de session de la formation (`/?s=...` ou `/?session=...`) sont renvoyés par le portail vers `anse-goulven/`.

Les fichiers non HTML (images, `.pptx`, JSON) ne sont pas redirigés : un lien direct vers l'un d'eux doit être mis à jour vers son nouveau dossier.

## Publication

Le workflow `.github/workflows/pages.yml` publie le site sur GitHub Pages à chaque push sur `main`. Seules les pages et leurs ressources sont publiées : la documentation (`*.md`) et le dossier `worker/` restent dans le dépôt.
