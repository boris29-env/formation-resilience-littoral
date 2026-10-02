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

## Anciennes adresses

Les pages étaient auparavant toutes à la racine. Les anciennes adresses (`plateforme.html`, `kanban-suivi-cabinet.html`, etc.) restent en place sous forme de petites pages de redirection, qui conservent les paramètres d'URL et l'ancre. Les liens de session de la formation (`/?s=...` ou `/?session=...`) sont renvoyés par le portail vers `anse-goulven/`.

Les fichiers non HTML (images, `.pptx`, JSON) ne sont pas redirigés : un lien direct vers l'un d'eux doit être mis à jour vers son nouveau dossier.

## Publication

Le workflow `.github/workflows/pages.yml` publie tout le dépôt sur GitHub Pages à chaque push sur `main`.
