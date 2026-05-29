# Plateforme « Recomposition spatiale des littoraux ultramarins »
## Architecture, capacités, et brief de réflexion sur le concept

> **But de ce document.** Donner à un lecteur (humain ou Claude) une vision fidèle de ce que la
> plateforme *est aujourd'hui* (Partie I et II), puis ouvrir la réflexion sur ce qu'elle *pourrait
> devenir* en respectant les prérogatives de chaque acteur (Partie III). C'est un document de travail,
> pas une spécification figée. Il accompagne `atelier-outremer.html` (application mono-fichier) et la
> note de méthode `Methodologie_chaine_ouvrages_cotiers_6COM.md`.

---

# Partie I — Ce que la plateforme est aujourd'hui

## 1. Nature du produit

Une **application web mono-fichier** (`atelier-outremer.html`, ~4070 lignes, HTML + JS inline, sans
build). Déployée en pages statiques (GitHub Pages, branche `main`). Tout le calcul s'exécute **dans le
navigateur** ; les seuls appels réseau sont vers des services tiers (imagerie IGN/Esri, base
temps-réel Firebase, API Claude via proxy, synthèse vocale).

Elle remplit **deux rôles superposés**, et c'est la source de l'ambiguïté de concept qu'on cherche à
clarifier :

- **Un atelier pédagogique de co-construction** : un parcours en 8 sections qui fait travailler des
  groupes (élus, services, habitants) sur l'adaptation au recul du trait de côte, territoire par
  territoire, avec des assistants IA incarnés (témoin du passé, trajectoires climatiques, miroir
  institutionnel) et un diagnostic partagé en temps réel.
- **Un prototype de chaîne de détection côtière** : un moteur de photo-interprétation automatique
  (trait de côte, ouvrages, évolution multi-dates, zones basses) avec une boucle d'apprentissage
  supervisé partagée.

## 2. Le parcours en 8 sections (fil narratif)

| # | Section (id) | Fonction |
|---|---|---|
| 01 | Carte (`sec-carte`) | Carte Leaflet (fonds OSM / IGN Plan / IGN Ortho / Esri), marqueurs de sites exposés, import GeoJSON, outils d'annotation (secteurs, tracés). |
| 02 | Domaines de compétence (`sec-groupes`) | Présente les 5 domaines (Aménagement, Environnement, Habitat, Foncier, Gouvernance) ; sert à router les groupes. |
| 03 | Diagnostic (`sec-diag`) | Grille interactive : 2 axes de socle (connaissance, planification) + 4 modules (foncier, habitat, financement, gouvernance). Scores visualisés en silhouette de maison. Pré-rempli par la mission, validé par le territoire, synchronisé Firebase entre groupes. |
| 04 | Outils mobilisables (`sec-outils`) | Fiches d'outils propres au territoire, hiérarchisées par priorité (en place / priorité 1 / cadre en vigueur). |
| 05 | Voix du passé (`sec-passe`) | Assistant IA incarnant un témoin d'un événement documenté (ex. cyclone, Irma 2017). Conversation multi-tours (max 6), réponses sourcées, synthèse vocale optionnelle. |
| 06 | Analyse territoriale (`sec-cas`) | 4 études de cas approfondies : inventaire des enjeux exposés, orientation de recomposition site par site, verrou foncier/gouvernance, feuille de route. |
| 06 bis | Tableau de bord territorial (`sec-diag-inst`) | Tableau de bord « vivant » détenu par la collectivité : 6 thèmes (connaissance, planification, foncier, habitat, financement, gouvernance), notes et réponses éditables, assistant IA contextuel. |
| 07 | Analyse d'images côtières (`sec-image`) | Moteur SIG (voir §4). Routines : trait de côte, ouvrages, évolution, zones basses (MNT). |
| 07 | Voix du climat (`sec-climat`) | 4 trajectoires climatiques régionalisées (accord de Paris SSP1-1.9, TRACC SSP2-4.5, haut SSP3-7.0, emballement SSP5-8.5). Projections d'élévation marine par région. Conversation (max 8 tours). |
| 08 | Débriefing miroir (`sec-debrief`) | Synthèse IA des positions de tous les groupes ; renvoie ce que les choix révèlent des priorités du territoire. |

## 3. Le modèle de données « territoire »

`TERRITOIRES` (6 entrées : `spm`, `wallis`, `nc`, `stmartin`, `stbarth`, `pf`), `TERR_ACTIF` désigne
l'actif. Chaque territoire porte ~50-100 champs profondément spécifiques :

- **Statut & droit** : statut juridique (COM art. 74 / sui generis NC), régime coutumier le cas
  échéant (`coutume`, `coutume_content`), points de vigilance, sources.
- **Cartographie** : centre/zoom carte, sites exposés (`sites` avec horizons h30/h50/h100),
  points de départ d'analyse image (`imgDir`).
- **Diagnostic** : pré-remplissage par module (`prefill`), archétypes contextuels (`prefill_ctx`).
- **Récit & témoignage** : événement passé (`event_passe` : personnage, prompt système, voix TTS).
- **Outils** : fiches stratifiées par priorité (`fiches`).
- **Recomposition** : axes de feuille de route phasés (`fdr_axes`), indicateurs (`indicateurs`).

Aucune donnée saisie par l'utilisateur n'est stockée *dans* `TERRITOIRES` (statique) ; les
contributions vont dans Firebase.

## 4. Le moteur d'analyse d'images côtières (SIG)

Tout le traitement d'image est **local** (canvas, JS), à l'échelle d'une dalle. C'est volontairement
un prototype « bord client », distinct de la chaîne industrielle décrite dans la note de méthode.

**Sources d'imagerie**
- IGN Géoplateforme `data.geopf.fr` : ortho RGB (`ORTHOIMAGERY.ORTHOPHOTOS`), **ortho IRC/PIR**
  (`...IRC`, pour NDWI/NDVI), couches historiques (évolution multi-dates), MNT **RGE ALTI**.
- Esri World Imagery (`arcgisonline.com`) : repli satellite RGB, parfois plus net.

**Pipeline**
1. **Masque d'eau** — `computeWaterMask()` : NDWI sur l'IRC si disponible (l'eau absorbe le PIR,
   robuste même sur haut-fond turquoise), sinon indice cyan RGB `(g−r)/(g+r)+(b−r)/(b+r)` avec garde
   végétation. Seuillage Otsu réglable, composantes « mer » connectées, bouchage des trous parasites.
2. **Trait de côte** — `extraireTraitDeCote()` : contours mer/terre (marching squares), chaque
   segment classé par `_classeRivage()` selon un **logigramme adapté aux côtes sans marée** :
   sable (plage/eau) › bâti/ouvrage (au contact mer) › front végétal/mangrove. Une seule ligne.
3. **Ouvrages** — `extraireOuvrages()` : hypothèse qu'un ouvrage longitudinal **rectilinéarise** la
   côte. Chaque segment reçoit un vecteur radiométrique/géométrique, est classé par
   `classifieOuvrage()` (typologie **Cerema** : enrochement longitudinal / perré ou mur / digue selon
   largeur ; attribut `substitue_tc` quand l'ouvrage *devient* localement le trait de côte), puis
   chaîné. Passes complémentaires : consolidation des colinéaires (`consoliderOuvrages`), **ouvrages
   en retrait de plage** (`_detecterArrierePlage`), **brise-lames détachés** par ACP
   (`_detecterBriseLames`), épis transversaux.
4. **Contrôle IA optionnel (2ᵉ passe)** — `controleIA()` : envoie l'image + candidats à Claude
   (Sonnet, vision) pour écarter les faux positifs (forêt, rivière, ombre). Désactivé par défaut.
5. **Évolution multi-dates** — `lancerEvolution()` : trait de côte par millésime IGN, segments
   comparables, tracés datés (tendance recul/accrétion).
6. **Zones basses** — `lancerMNT()` : isolignes ≤ +N m depuis le RGE ALTI. **Disponible uniquement
   là où l'IGN fournit l'altitude (SPM, Antilles, métropole)** ; indisponible sur le Pacifique.

## 5. La boucle d'apprentissage supervisé

- **Vecteur de 12 features** : `OUVR_FK = [sd, gran, cv, net, wf, persist, Lm, sat, rmb, larg, len, landReach]`.
- **Modèle** : régression logistique entraînée *dans le navigateur* (`entrainerModeleOuvrages`),
  z-score, L2. Seuils : ≥0.65 ouvrage / 0.40-0.65 à vérifier / <0.40 rejeté.
- **Affinage** : `affinerOuvragesParModele()` — le modèle **note des candidats heuristiques** (pas de
  génération brute → pas d'hallucination). C'est un *raffineur*, pas un détecteur autonome.
- **Annotation carte** : dessiner un secteur (`dessinerSecteur`), marquer un ouvrage (`marquerOuvrage`),
  valider/invalider ✓/✗ (`validerSurCarte`), re-chercher à sensibilité accrue (`chercherDansSecteurs`).
- **Partage** : labels stockés sur Firebase **global** (`outremer/_apprentissage_ouvrages/labels`),
  fusionnés avec les labels locaux (localStorage), dédoublonnés par timestamp. Import/export de corpus
  JSON. Le modèle se ré-entraîne à chaque nouveau label.

## 6. Assistants IA

| Assistant | Modèle | Tours | Rôle |
|---|---|---|---|
| Voix du passé | `claude-haiku-4-5` | 6 | Témoin historique sourcé, TTS via proxy Voxtral. |
| Diagnostic instructeur | `claude-haiku-4-5` | ~6 | Accompagne le tableau de bord territorial, ancré sur les faits. |
| Voix du climat | `claude-haiku-4-5` | 8 | Trajectoires SSP régionalisées (GIEC AR6, SROCC, TRACC). |
| Débriefing / analyse image | `claude-sonnet-4-20250514` | — | Synthèse des positions ; vision pour le contrôle IA. |

Appels via `getClaudeConfig()` : **proxy** (Cloudflare Worker `dialogue-1972.margate22.workers.dev`)
ou **clé Anthropic directe** (sessionStorage, mode formateur). Format API Anthropic standard.

## 7. Persistance, partage, gouvernance des données

- **Firebase Realtime** (projet `resilience-8c52d`, europe-west1) :
  - `outremer/{session}/diagnostic|routing|diag_inst|collecte|image_analyses` — par session/groupe.
  - `outremer/_apprentissage_ouvrages/labels` — **global**, corpus d'apprentissage collaboratif.
- **localStorage** : labels, secteurs dessinés, corrections de trait manuelles.
- **Consentement** : bandeau, `sessionStorage`, journalisation Firebase, rétention 90 j,
  suppression sur demande (`supprimerDonnees`). Données collectées : conversations IA, scores de
  diagnostic, métadonnées d'analyses d'image.
- **Exports** : bilan/diagnostic (TXT), fiche de restitution, GeoJSON et CSV (extraction unique ou
  cumul), traitement par lot de tous les sites (`traiterTousSites`), export des données collectées (JSON).

## 8. Mode formateur

`activerModeFormateur()` déverrouille : réinitialisation de session, affichage de l'ID de session,
configuration de l'URL du proxy Voxtral, saisie/test d'une clé Anthropic.

---

# Partie II — Capacités, en clair

Ce que la plateforme **sait faire aujourd'hui**, formulé en verbes d'usage :

1. **Cartographier l'exposition** d'un territoire (sites, horizons d'élévation, fonds IGN/satellite).
2. **Extraire un trait de côte** classé (sable / ouvrage / végétation) sur une dalle, sans marée.
3. **Détecter et typer des ouvrages** côtiers (typologie Cerema) avec un raffinage par modèle appris.
4. **Apprendre en continu** d'un corpus de validations ✓/✗ partagé entre toutes les sessions.
5. **Mesurer une évolution** du rivage entre millésimes IGN (là où les archives existent).
6. **Délimiter les zones basses** par MNT (Atlantique/Antilles uniquement).
7. **Faire dialoguer** des groupes avec un passé incarné, des futurs climatiques régionalisés, et un
   miroir institutionnel — le tout sourcé.
8. **Produire un diagnostic partagé** et une feuille de route territoriale, exportables.
9. **Respecter une éthique de données** (consentement, rétention, suppression, indicativité affichée).

**Limites assumées (héritées de l'imagerie et de l'architecture)**
- Seuls les ouvrages **visibles** sont saisis ; pas d'état ni de dégradation (relève du terrain).
- Pas d'**orthorectification** ni de recalage sub-pixellaire propre : on consomme des images déjà
  calculées par les flux → précision géométrique tributaire de la source.
- Calcul **bord client** à l'échelle de la dalle : pas de traitement de dalles lourdes ni de chaîne
  industrielle ré-exécutable (ce que la note de méthode confie à un *service de traitement* serveur).
- **MNT et archives** absents sur une partie du Pacifique → capacités inégales selon les territoires.
- Référentiels géodésiques : tout est en **WGS84** ; les projections locales (RGPF, RGNC, RGAF09…)
  recommandées par la note de méthode ne sont pas encore appliquées.

---

# Partie III — Brief de réflexion : ce qu'on pourrait en faire, sans empiéter sur personne

> Cette partie est **le cœur de la demande** : prendre du recul sur le concept. Elle pose les
> questions, esquisse des pistes, et cadre des études de cas. Elle n'arrête rien.

## 9. La tension de concept à trancher

La plateforme oscille entre **trois identités** qui n'ont pas le même utilisateur ni la même exigence :

- **(A) Outil d'atelier / pédagogie** — public : mission, élus, habitants. Exigence : clarté, récit,
  appropriation. *C'est ce qui est le plus abouti.*
- **(B) Prototype de démonstration technique** — public : ingénieurs, observatoires. Exigence :
  montrer qu'une détection automatique est plausible et auditable. *C'est mûr mais « jouet ».*
- **(C) Maillon d'une chaîne opérationnelle** — public : Cerema, observatoires territoriaux (OBLIC,
  projets Moorea). Exigence : industrialisation, interopérabilité, traçabilité, versionnement.
  *C'est ce que décrit la note de méthode, et ce que la plateforme n'est pas encore.*

**Question 1.** Veut-on assumer (A) + (B) comme une *vitrine de co-construction et de faisabilité*,
en laissant (C) à un service serveur séparé ? Ou veut-on faire converger l'app vers le **front-end de
validation** de la chaîne (C) — celui qui *affiche, valide, pilote*, mais ne calcule pas le gros ?
La note de méthode tranche clairement pour la séparation : *« le site web manipule des vecteurs
légers et des images déjà calculées, le serveur manipule les pixels »*.

## 10. Respecter les prérogatives de chacun — la vraie contrainte de conception

C'est ici que « l'étude de cas » prend son sens. Les six collectivités n'ont **pas le même partage de
compétences**, et la plateforme doit rester à sa place : **un appui à la décision indicatif, qui ne
crée aucune obligation** (déjà affiché). Les prérogatives à respecter, par acteur :

- **L'État** : risques (PPRL), référentiels nationaux (IGN, SHOM, Cerema), financement (Fonds Barnier
  là où il s'applique). → La plateforme *alimente* mais ne *prescrit* pas.
- **La collectivité / le Pays** : l'urbanisme et l'aménagement relèvent selon les cas de la
  collectivité (St-Martin, St-Barth, SPM), du **Pays** (Polynésie française, Wallis-et-Futuna), ou
  de la **Nouvelle-Calédonie et de ses provinces** (régime sui generis). → Le territoire doit
  **détenir et valider** sa donnée (c'est déjà l'esprit du tableau de bord « vivant »).
- **Les autorités coutumières** : à Wallis (royaumes d'Uvea, Alo, Sigave) et en Nouvelle-Calédonie
  (Sénat coutumier, conseils coutumiers ; **terres coutumières inaliénables**), toute recomposition
  suppose un **accord coutumier explicite**. → La plateforme peut *cartographier l'exposition* sur ces
  terres, mais ne doit jamais présenter une relocalisation comme acquise ; elle distingue l'enjeu
  technique de la **décision**, qui appartient aux instances coutumières.
- **Les observatoires & le national** : OBLIC en NC (la chambre territoriale recommande de
  *consolider la connaissance des ouvrages*), projets d'observatoire en PF, base Cerema / Géolittoral,
  Réseau national des observatoires du trait de côte. → La donnée produite gagne à être
  **interopérable** (typologie Cerema — déjà alignée — et, à terme, format GeoPackage/WFS).

**Contrainte juridique concrète sur la donnée** : l'imagerie de Nouvelle-Calédonie (Géorep) est en
**CC BY-NC-SA** (non commerciale, partage à l'identique). Cela borne ce que la plateforme peut faire
des produits dérivés et doit figurer dans la gouvernance de la donnée. L'IGN (Etalab 2.0) et Te Fenua
sont plus permissifs. Wallis n'a pas de couverture gratuite (recours Dinamis/Pléiades sous condition).

**Question 2.** Comment matérialiser *dans l'interface* le fait que la plateforme s'arrête au seuil de
la décision ? Pistes : un **bandeau de prérogative par territoire** (qui décide quoi), un statut
explicite « terre coutumière → décision = conseil coutumier » sur les couches concernées, une mention
de licence de donnée par source.

## 11. Études de cas candidates (chacune exerce des capacités ET des contraintes différentes)

| Cas | Territoire | Capacités exercées | Prérogatives / contraintes spécifiques |
|---|---|---|---|
| **Isthme de Miquelon-Langlade** | SPM | MNT zones basses (dispo !), évolution multi-dates, ouvrages (enrochements). | Marée mésotidale (exception) ; relocalisation du village ; compétence collectivité + État. |
| **Reconstruction post-Irma** | Saint-Martin | Détection d'ouvrages, évolution rapide, suivi de chantier. | Fréquence d'actualisation élevée ; imagerie d'urgence ; compétence collectivité. |
| **Ligne de stabilité Moorea** | Polynésie fr. | Trait de côte logigramme, front végétal, observatoire. | Compétence **Pays** ; Te Fenua ; projection RGPF UTM 6S ; projet d'observatoire. |
| **Inventaire OBLIC** | Nouvelle-Calédonie | Détection + apprentissage partagé, export Cerema. | **CC BY-NC-SA** ; régime sui generis ; **terres coutumières** ; consolidation recommandée. |
| **Cas pionnier Wallis** | Wallis-et-Futuna | Faible donnée → veille + saisie experte. | Pas d'ortho gratuite (Dinamis) ; **accord coutumier** préalable ; GEMAPI non transposée. |

**Question 3.** Une étude de cas devrait-elle être un **scénario guidé** *dans* la plateforme (une
section qui enchaîne carte → détection → diagnostic → feuille de route pour ce site), plutôt qu'un
parcours générique ? Cela donnerait corps au concept et montrerait la valeur bout-en-bout.

## 12. Pistes d'évolution, classées par ambition

**Court terme — consolider l'existant (faible risque)**
- **Bandeau de prérogatives** par territoire + statut coutumier sur les couches ; mention de licence
  de donnée par source. *Répond directement à « respecter les prérogatives de tout le monde ».*
- **Export aligné Cerema/Géolittoral** : GeoPackage + dictionnaire d'attributs (type, longueur,
  `substitue_tc`, confiance, date image, capteur, identifiant), pour l'interopérabilité nationale.
- **Reprojection locale** à l'export (RGPF, RGNC, RGAF09, RGSPM) au lieu du seul WGS84.

**Moyen terme — combler les manques de la note de méthode**
- **Couche de veille** (la bonne place de Sentinel-2 / Digital Earth Pacific) : non pas dans le masque
  d'eau de détection (on l'a retirée, à raison), mais en **détection de changement** à 10 m qui
  *signale* où ré-exploiter la THR. C'est le chaînon « actualisation » manquant.
- **Base temporelle** : statut nouveau/maintenu/modifié/disparu par ouvrage, historique non écrasé.
- **Curation du corpus d'apprentissage** : aujourd'hui le corpus global est ouvert ; prévoir
  validation par opérateur unique formé (recommandation INSeaPTION), traçabilité de la lignée.

**Long terme — la chaîne (C)**
- **Service de traitement serveur** (orthorectification, recalage, segmentation sur dalles lourdes)
  avec l'app comme front de visualisation/validation/pilotage. C'est l'architecture cible de la note
  de méthode ; l'app actuelle en préfigure le front.

## 13. Questions ouvertes à soumettre à la réflexion de Claude

1. **Identité** : assumer une vitrine (A+B), ou viser le front d'une chaîne (C) ? Les deux sont-ils
   conciliables dans un mono-fichier, ou faut-il scinder ?
2. **Place de l'humain** : où s'arrête l'automatisation, où commence l'arbitrage expert/élu/coutumier ?
   Comment l'interface le rend-elle évident ?
3. **Gouvernance de la donnée partagée** : qui possède le corpus d'apprentissage ? Sous quelle
   licence (au regard du CC BY-NC-SA calédonien) ? Comment éviter qu'un mauvais label dégrade le
   modèle pour tous ?
4. **Interopérabilité** : faut-il s'aligner dès maintenant sur le schéma Cerema/Géolittoral pour que
   la donnée *remonte* dans les observatoires, ou rester un démonstrateur autonome ?
5. **Équité territoriale** : comment ne pas créer une plateforme « à deux vitesses » entre territoires
   richement dotés (SPM, Antilles : MNT, archives) et démunis (Wallis, Pacifique) ?
6. **Veille vs détection** : quelle articulation propre entre la couche 10 m (changement) et la THR
   (détection fine), maintenant qu'on a clarifié que Sentinel n'a pas sa place dans le masque d'eau ?

---

*Document de travail. Sources de cadrage : `Methodologie_chaine_ouvrages_cotiers_6COM.md` (note de
méthode v1.1) et le code de `atelier-outremer.html`. Aucune valeur prescriptive ; sert de base à une
réflexion sur la conception.*
