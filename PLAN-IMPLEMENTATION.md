# Plan d'implémentation pour Claude Code

## Portail « Recomposition spatiale des littoraux ultramarins » (`atelier-outremer.html`)

> **Objet.** Ce document est un cahier des charges actionnable, destiné à être lu et exécuté par Claude Code sur le dépôt du portail. Il décrit, lot par lot, les évolutions à mettre en œuvre pour (1) valoriser le kit littoral et son scoring, (2) fiabiliser l'extraction des traits de côte et des ouvrages, (3) ouvrir une voie d'innovation crédible, le tout au regard des six collectivités d'outre-mer (COM) traitées et en mobilisant des données en source ouverte. Le livrable visé est une plateforme web indépendante, appropriable localement par chaque collectivité.
>
> **Principe directeur.** On commence par tout ce qui améliore l'existant sans rien casser et sans serveur (Lot A, navigateur seul). On prépare ensuite, de façon strictement optionnelle et à coût marginal, les briques client-serveur (Lot B). Aucune évolution ne doit dégrader le fonctionnement hors ligne ni l'usage pédagogique déjà abouti.
>
> **Exigence de rigueur.** Chaque tâche cite sa référence méthodologique (section 7). Aucune valeur, aucun seuil, aucune source n'est inventé. Lorsqu'une donnée locale n'est pas certaine (par exemple un code de projection pour Wallis-et-Futuna), le code doit l'exposer comme paramètre à confirmer localement, jamais comme un acquis.

---

## 0. Mode d'emploi pour Claude Code

1. **Ne pas réécrire le mono-fichier.** Le portail est une application mono-fichier (`atelier-outremer.html`, HTML et JS inline, sans build, environ 4070 lignes). Les évolutions du Lot A se font par ajout de fonctions et par modification ciblée des fonctions existantes nommées en section 1.4, sans introduire d'étape de build ni de dépendance npm.
2. **Travailler par branche et par lot.** Une branche par tâche (`feat/A1-scoring-sensibilite`, etc.), un commit par sous-tâche, un message de commit qui cite la référence méthodologique concernée.
3. **Conserver le repli hors connexion.** Tout appel réseau nouveau (tuiles, API, modèle) doit échouer proprement : si la ressource est indisponible, l'interface reste utilisable et signale l'indisponibilité, sans bloquer le parcours.
4. **Respecter la séparation des rôles.** Le navigateur manipule des vecteurs légers et des images déjà calculées ; il ne doit jamais tenter de traiter des dalles lourdes en masse. Le calcul lourd, quand il existe, est confié au Lot B (asynchrone, hors ligne de l'utilisateur).
5. **Critères de recette.** Chaque lot a une définition de « terminé » (section 8). Ne pas clore une tâche sans avoir vérifié son critère.
6. **Lire avant d'écrire.** Avant de modifier une fonction, lire la fonction entière et ses appelants dans le fichier. Le présent plan décrit l'intention, pas la totalité du code interne.

---

## 1. Ce que Claude Code doit savoir avant de commencer

### 1.1 Nature et déploiement

Application web mono-fichier, calcul intégralement côté navigateur (canvas, JS). Déploiement en pages statiques. Seuls appels réseau actuels : imagerie (IGN Géoplateforme, Esri), base temps réel Firebase, API Claude via proxy Cloudflare Worker, synthèse vocale. Aucune donnée saisie par l'utilisateur n'est stockée dans le modèle de données statique des territoires ; les contributions vont dans Firebase.

### 1.2 Double rôle assumé

- **Atelier pédagogique de co-construction** en huit sections (carte, domaines de compétence, diagnostic partagé, outils mobilisables, voix du passé, analyse territoriale, tableau de bord territorial, voix du climat, débriefing). C'est la partie la plus aboutie ; elle ne doit pas régresser.
- **Prototype de chaîne de détection côtière** (trait de côte, ouvrages, évolution multi-dates, zones basses), avec une boucle d'apprentissage supervisé partagée.

### 1.3 Système de scoring existant (à valoriser, Lot A1)

- **Diagnostic** visualisé en silhouette de maison : deux axes de socle (connaissance, planification) et quatre modules (foncier, habitat, financement, gouvernance). Pré-rempli par la mission, validé par le territoire, synchronisé entre groupes via Firebase.
- **Tableau de bord territorial** dit « vivant », détenu par la collectivité : six thèmes (connaissance, planification, foncier, habitat, financement, gouvernance), notes et réponses éditables.

### 1.4 Chaîne d'extraction existante (à fiabiliser, Lot A2 et A3)

Points d'ancrage dans le code, à réutiliser et ne pas renommer :

- `computeWaterMask()` : masque d'eau par NDWI sur ortho IRC si disponible, sinon indice cyan RGB ; seuillage Otsu ; composantes connectées ; bouchage des trous.
- `extraireTraitDeCote()` : contour mer/terre par marching squares ; classification de chaque segment par `_classeRivage()` selon un logigramme adapté aux côtes sans marée (sable, bâti/ouvrage, front végétal/mangrove).
- `extraireOuvrages()` : hypothèse de rectilinéarisation ; vecteur radiométrique et géométrique par segment ; classification par `classifieOuvrage()` selon la typologie Cerema (enrochement longitudinal, perré ou mur, digue selon largeur ; attribut `substitue_tc`) ; passes complémentaires `consoliderOuvrages`, `_detecterArrierePlage`, `_detecterBriseLames`, épis transversaux.
- `controleIA()` : seconde passe vision (Claude Sonnet) pour écarter les faux positifs ; désactivée par défaut.
- `lancerEvolution()` : trait de côte par millésime, segments comparables, tendance recul/accrétion.
- `lancerMNT()` : isolignes des zones basses à partir du RGE ALTI ; disponible uniquement là où l'IGN fournit l'altitude.
- Boucle d'apprentissage : vecteur de douze descripteurs `OUVR_FK = [sd, gran, cv, net, wf, persist, Lm, sat, rmb, larg, len, landReach]` ; régression logistique entraînée dans le navigateur (`entrainerModeleOuvrages`) ; `affinerOuvragesParModele()` note des candidats heuristiques (raffineur, pas détecteur autonome) ; seuils actuels 0,65 (ouvrage) et 0,40 (à vérifier) ; labels partagés sur Firebase global `outremer/_apprentissage_ouvrages/labels`, fusionnés avec localStorage, dédoublonnés par timestamp.
- Annotation carte : `dessinerSecteur`, `marquerOuvrage`, `validerSurCarte`, `chercherDansSecteurs`.
- Configuration des appels Claude : `getClaudeConfig()`. Mode formateur : `activerModeFormateur()`. Suppression des données : `supprimerDonnees`. Traitement par lot : `traiterTousSites`.

### 1.5 Modèle de données territoire

`TERRITOIRES` (six entrées : `spm`, `wallis`, `nc`, `stmartin`, `stbarth`, `pf`), `TERR_ACTIF` désigne l'actif. Chaque territoire porte le statut juridique, le régime coutumier le cas échéant, le centrage carte, les sites exposés avec horizons h30/h50/h100, les points de départ d'analyse image, le pré-remplissage du diagnostic, l'événement passé, les fiches d'outils et les axes de feuille de route.

### 1.6 Limites actuelles à corriger ou à exposer honnêtement

- Pas d'orthorectification ni de recalage sub-pixellaire propre : la précision géométrique est tributaire de la source.
- Tout est en WGS84 ; les projections locales ne sont pas appliquées (corrigé en A4).
- MNT et archives absents sur une partie du Pacifique : capacités inégales entre territoires (traité en A6).
- Référentiels et licences hétérogènes selon les territoires (traité en A4, A5 et section 3).

---

## 2. Principes d'architecture et stratégie de coût

### 2.1 Trois cercles d'exécution

1. **Cercle navigateur (Lot A).** Tout ce qui tient en JS local sur une dalle ou sur des vecteurs : scoring, classification heuristique, raffinage logistique, export, gouvernance. Coût d'hébergement nul (pages statiques). C'est le socle du livrable appropriable.
2. **Cercle serverless (Lot B, niveau 1).** Fonctions à la demande, sans serveur permanent, pour les tâches courtes : proxy d'API, signature de requêtes, agrégation de métadonnées, déclenchement de traitements. Le portail utilise déjà un Cloudflare Worker pour le proxy Claude ; on réutilise ce même mécanisme. Coût quasi nul dans les quotas gratuits.
3. **Cercle traitement lourd (Lot B, niveau 2).** Orthorectification, recalage, segmentation profonde, veille satellitaire massive. Jamais en continu : exécution par lot, ponctuelle, sur ressource éphémère (voir 2.3). Le navigateur ne reçoit que des produits déjà calculés (tuiles, GeoPackage, vecteurs).

### 2.2 Règle d'or de coût

Le navigateur reste le front unique. Le serveur ne calcule que ce qui est impossible dans le navigateur, et il le fait de manière asynchrone et discontinue. On préfère systématiquement : des produits pré-calculés à un calcul à la volée ; un quota gratuit existant à une infrastructure dédiée ; un déclenchement manuel ou planifié à un service qui tourne en permanence.

### 2.3 Comment faire le client-serveur à moindre coût (cœur de la demande)

- **Hébergement du front : pages statiques.** Inchangé. Aucune dépense.
- **Fonctions serverless : Cloudflare Workers (déjà en place) ou équivalent.** Quotas gratuits généreux pour des appels courts. On y met le proxy d'API, la composition de requêtes vers les catalogues d'images, et le déclenchement des traitements. Pas de serveur à administrer.
- **Stockage des produits dérivés : stockage objet.** Cloudflare R2, ou un bucket compatible S3, ou même un dépôt Git de données pour les volumes modestes. On y dépose les tuiles, les GeoPackage et les vecteurs produits par le Lot B. Le navigateur lit ces fichiers statiques. Le stockage objet en lecture est très bon marché et, sur R2, sans frais de sortie réseau.
- **Veille satellitaire : Google Earth Engine en usage recherche, ou Copernicus Data Space.** Earth Engine est gratuit pour un usage non commercial et recherche, et porte déjà Sentinel-2, Landsat et les projections IPCC AR6 régionalisées. On exécute la détection de changement dans Earth Engine (côté Google, donc sans coût d'infrastructure), et on n'exporte que de petits vecteurs d'alerte vers le stockage objet. Copernicus Data Space Ecosystem est l'alternative pleinement ouverte si l'on veut éviter toute dépendance Google.
- **Traitement profond ponctuel : machine éphémère à la demande, ou notebook gratuit.** Pour le fine-tuning ou l'inférence d'un modèle de segmentation, on utilise une session de calcul gratuite (par exemple un notebook Colab pour la phase d'amorçage) ou une instance GPU à la demande facturée à l'heure, allumée le temps du traitement par lot puis éteinte. On ne maintient jamais un GPU en ligne. Les poids du modèle, une fois entraînés, sont stockés en objet et réutilisés.
- **Inférence à la demande : API d'inférence managée.** Pour une inférence occasionnelle, une API d'inférence (par exemple Hugging Face Inference) évite tout serveur. Pour des volumes plus importants, on bascule sur le traitement par lot éphémère ci-dessus.
- **Base temporelle des ouvrages : base légère.** Une base relationnelle serverless (par exemple Cloudflare D1, SQLite) ou la base temps réel déjà utilisée suffit pour historiser des vecteurs et des statuts. Pas de SGBD lourd.

En résumé, l'ensemble du Lot B peut fonctionner dans des quotas gratuits ou à coût marginal pour une mission, tant que l'on respecte la discipline « pré-calcul, déclenchement discontinu, stockage objet statique ».

---

## 3. Cadre des six collectivités

La plateforme doit traiter les six COM de façon différenciée. Le code ne doit pas présupposer une couverture homogène. Chaque champ ci-dessous alimente soit le modèle `TERRITOIRES`, soit la logique d'export (A4), soit le bandeau de prérogatives et de licence (A5), soit la stratégie d'équité (A6).

### 3.1 Tableau de référence par territoire

| Territoire (clé) | Statut, prérogative dominante | Référentiel géodésique (à utiliser à l'export) | Imagerie en source ouverte | Licence imagerie | MNT national | Indicateur national d'érosion Cerema | Observatoire formalisé | Régime de marée | Indicateur de trait de côte recommandé |
|---|---|---|---|---|---|---|---|---|---|
| Saint-Pierre-et-Miquelon (`spm`) | COM art. 74, collectivité et État | RGSPM06, géographique EPSG 4463, projeté UTM 21N EPSG 4467 | IGN Géoplateforme `data.geopf.fr` (ortho, ortho IRC, cartes anciennes) | Etalab 2.0 (ouverte) | RGE ALTI disponible | Non (couverture spécifique récente, hors indicateur national des cinq DROM) | Non formalisé ; suivi BRGM et synthèse Cerema 2023 | Mésotidal (exception parmi les six) | Trait de côte corrigé du niveau d'eau ou rapporté à un niveau de référence |
| Wallis-et-Futuna (`wallis`) | Pays et autorités coutumières (royaumes Uvea, Alo, Sigave) ; GEMAPI non transposée | RGWF96, géographique EPSG 4480 ; projection métrique UTM zone 1S, code EPSG à confirmer localement | Pas d'ortho gratuite ; recours Dinamis/Pléiades sous condition ; Digital Earth Pacific (SPC) pour coastlines Sentinel-2 | Selon source (Dinamis sous condition ; DEP selon licence SPC) | Aucun MNT national gratuit | Non | Aucun ; supervision BRGM depuis l'antenne Nouvelle-Calédonie | Microtidal | Ligne de stabilité INSeaPTION, faute d'archives, complétée par saisie experte |
| Nouvelle-Calédonie (`nc`) | Sui generis, provinces, terres coutumières inaliénables (Sénat coutumier) | RGNC91-93, géographique EPSG 4749, projeté Lambert Nouvelle-Calédonie EPSG 3163 (UTM 57S/58S/59S EPSG 3168/3169/3170 selon besoin) | Géorep `georep.nc` ; Open Data NC `data.gouv.nc` (couches OBLIC, typologie du littoral) | Imagerie Géorep en CC BY-NC-SA (non commerciale, partage à l'identique) : contrainte forte | Selon Géorep | Non | OBLIC (formalisé depuis 2013, SGNC/DIMENC avec BRGM), 77 sites pilotes | Méso à microtidal selon les côtes | Ligne de stabilité et pied de plage INSeaPTION ; alignement OBLIC |
| Saint-Martin (`stmartin`) | COM art. 74, collectivité | RGAF09, géographique EPSG 5489, projeté UTM 20N EPSG 5490 | IGN Géoplateforme `data.geopf.fr` (ortho, ortho IRC, RGE ALTI) | Etalab 2.0 (ouverte) | RGE ALTI disponible | Non en tant que COM (synthèse Cerema 2023 ; atlas BRGM RP-65212-FR ; étude Irma RP-67291-FR) | Non formalisé | Microtidal (marnage faible) | Ligne de stabilité et jet de rive ; suivi rapproché post-Irma |
| Saint-Barthélemy (`stbarth`) | COM art. 74, collectivité | RGAF09, géographique EPSG 5489, projeté UTM 20N EPSG 5490 | IGN Géoplateforme `data.geopf.fr` | Etalab 2.0 (ouverte) | RGE ALTI disponible | Non en tant que COM (synthèse Cerema 2023 sur Saint-Barthélemy et Saint-Martin) | Non formalisé | Microtidal | Ligne de stabilité et jet de rive |
| Polynésie française (`pf`) | Pays (urbanisme et aménagement au Pays) | RGPF, géographique EPSG 4687, projeté UTM selon archipel : Société (Tahiti, Moorea) UTM 6S EPSG 3297 ; autres 5S/7S/8S EPSG 3296/3298/3299 | Te Fenua `tefenua.gov.pf` (portail du Pays) | Selon Te Fenua (à préciser dans le bandeau de licence) | Aucun MNT national IGN ; recours MNT global (précision moindre, inadaptée aux atolls) | Non | Non unifié ; CRIOBE (Moorea), UPF (GEPASUD, OGT), programmes STORISK, INSeaPTION, RESCCUE | Microtidal (très faible) | Ligne de stabilité et pied de plage INSeaPTION (protocole validé sur Tautira, Tahiamanu, Moorea, Aratika) |

### 3.2 Sources ouvertes communes aux six territoires

- **Sentinel-2** (programme Copernicus, ouvert) : 10 m, revisite environ cinq jours, bandes visibles et proche infrarouge. Accès via Copernicus Data Space Ecosystem ou Google Earth Engine. Sert la veille de changement (B1) et, le cas échéant, la segmentation par modèle de fondation (B2).
- **Landsat** (USGS, ouvert) : 30 m, archives depuis 1984. Sert la tendance de long terme.
- **Projections d'élévation marine IPCC AR6 régionalisées** : disponibles via le catalogue Earth Engine (jeu AR6 Sea Level Projections) et le portail NASA Sea Level Change ; marégraphie de référence via PSMSL. Sert l'affichage des projections par territoire (B et A1).
- **Outils ouverts** : DSAS (USGS, gratuit) pour les statistiques d'évolution ; CoastSat (dépôt `kvos/CoastSat`, open source) comme référence de chaîne sub-pixellaire ; données INSeaPTION publiées sur Sextant (Ifremer) pour Aratika, Tautira, Moorea.

### 3.3 Conséquence sur l'équité territoriale (voir A6)

Trois territoires sont bien dotés (SPM, Saint-Martin, Saint-Barthélemy : ortho IGN, ortho IRC, RGE ALTI, licence ouverte). Un territoire est sous licence restrictive (NC : CC BY-NC-SA). Deux territoires sont en déficit de données structurel (PF hors sites pilotes : pas de MNT national ; Wallis : ni ortho gratuite ni MNT ni observatoire). Le code doit afficher ce dégradé, jamais le masquer par des proxys silencieux.

---

## 4. Lot A, amélioration de l'existant (navigateur seul, sans serveur)

Priorité immédiate, faible risque, fort rendement. Aucune dépendance nouvelle obligatoire. Tient dans le mono-fichier.

### A1. Valoriser le kit littoral et fiabiliser le scoring

**A1.1 Documenter et rendre transparent le modèle de scoring.**
Adosser explicitement la construction du score au cadre de référence des indicateurs composites (réf. 7.1). Dans l'interface du diagnostic et du tableau de bord, ajouter un volet « méthode » qui expose, pour chaque axe et module : les variables qui le composent, leur normalisation, leur pondération effective, et la règle d'agrégation. Critère : un utilisateur peut lire d'où vient chaque score.

**A1.2 Rendre les pondérations explicites et ajustables, avec journalisation.**
Permettre à chaque collectivité de modifier les pondérations des axes et modules, dans une plage bornée, et journaliser ces choix dans le tableau de bord (traçabilité d'audit, horodatée). La pondération par défaut doit être affichée comme un choix, non comme une neutralité. Réf. 7.1 (la pondération égale est un choix méthodologique, pas un défaut neutre).

**A1.3 Ajouter une analyse de sensibilité visualisable.**
Implémenter un curseur de variation des pondérations (par exemple plus ou moins 30 %) qui recalcule le score en direct et affiche l'enveloppe de variation (score minimal, médian, maximal). Objectif : montrer la robustesse ou la fragilité d'un classement avant tout usage en réunion. Réf. 7.1 (l'analyse de sensibilité est une exigence, pas une option).

**A1.4 Séparer aléa, enjeu et capacité d'adaptation.**
Restructurer la lecture du tableau de bord pour distinguer clairement trois familles : l'aléa (érosion mesurée, niveau marin projeté, exposition cyclonique), l'enjeu (bâti, infrastructures, population, biens culturels et coutumiers), et la capacité d'adaptation (les quatre modules existants). Ne pas agréger ces familles dans un score unique compensatoire. Réf. 7.2 (la critique de l'indice de vulnérabilité côtière porte précisément sur le mélange aléa/vulnérabilité dans un même indice).

**A1.5 Intégrer la projection climatique par territoire.**
Afficher, pour chaque territoire et à côté du scoring, la trajectoire de réchauffement de référence applicable et la fourchette d'élévation marine régionalisée au point de marégraphe le plus proche, avec mention de la source et de la date. Ne jamais afficher la moyenne mondiale comme valeur locale. Réf. 7.3 (TRACC et projections AR6 régionalisées). Données chargées en statique (petit fichier JSON par territoire), mises à jour à la main.

### A2. Fiabiliser l'extraction du trait de côte

**A2.1 Introduire les indicateurs INSeaPTION pour les côtes sans marée.**
Pour `pf`, `nc` et `wallis`, faire produire par `extraireTraitDeCote()` non pas une seule ligne, mais deux indicateurs distincts et étiquetés : la ligne de stabilité (limite externe de végétation sur côte naturelle, base des ouvrages et remblais sur côte artificialisée) et le pied de plage (limite entre platier récifal et plage, ou jet de rive). Conserver la sortie actuelle comme « trait instantané » pour SPM. Réf. 7.4 (protocole INSeaPTION, validé sur Tautira, Tahiamanu, Moorea, Aratika).

**A2.2 Afficher une incertitude positionnelle explicite.**
Chaque trait extrait doit porter une incertitude positionnelle minimale, égale à au moins un pixel de la source (ordre de 0,2 à 0,5 m pour une ortho IGN), affichée et exportée. Pour les côtes sans marée, ajouter l'incertitude saisonnière du jet de rive (qui peut dépasser 2 m sur les atolls). Réf. 7.5 (budget d'incertitude des traits de côte). Ne jamais présenter une position sans sa marge.

**A2.3 Adopter les seuils d'évolution INSeaPTION dans `lancerEvolution()`.**
Classer chaque sous-secteur en stable, accrétion ou érosion selon le seuil documenté de plus ou moins 4,5 m sur la période, et exposer ce seuil comme paramètre. Découper la côte en sous-secteurs géomorphologiques cohérents (plage face à une passe, plage d'arrière-récif). Réf. 7.4 (Moorea, dix-neuf sous-secteurs, seuil de stabilité plus ou moins 4,5 m).

**A2.4 Exposer les statistiques d'évolution normalisées.**
Pour chaque transect, calculer et afficher le mouvement net du trait de côte et le taux annuel, selon les définitions du standard d'analyse de référence (réf. 7.6 : NSM, EPR, et si plusieurs dates, régression linéaire avec intervalle de confiance à 90 %). Ces statistiques doivent être exportables (voir A4).

### A3. Fiabiliser la détection et la typologie des ouvrages

**A3.1 Aligner strictement la typologie sur le schéma national.**
Faire produire par `classifieOuvrage()` les attributs exacts du schéma national de cartographie des ouvrages littoraux (réf. 7.7) : catégorie, classe, type, orientation (longitudinale ou transversale), longueur, année d'apparition, année de disparition, visibilité, hauteur si estimable, et l'attribut `substitue_tc` déjà présent. Les libellés de type doivent reprendre la nomenclature : digue côtière, mur de soutènement, perré (substitution au trait de côte) ; brise-lames, épi (lutte contre l'érosion). Réf. 7.7 (définitions du brise-lames longitudinal détaché et de l'épi transversal).

**A3.2 Renforcer la gouvernance du corpus d'apprentissage partagé.**
Le corpus global `outremer/_apprentissage_ouvrages/labels` est aujourd'hui ouvert. Ajouter : un identifiant d'opérateur sur chaque label ; une règle de quorum (un label n'est promu dans le corpus partagé que si au moins deux opérateurs concordent) ; un jeu de test gelé permettant de mesurer la performance du modèle à chaque ré-entraînement et de détecter une dérive. Réf. 7.8 (assurance qualité d'un corpus collaboratif, traçabilité de la lignée, détection de dérive). Tant que le quorum n'est pas atteint, un label reste local et n'affecte pas le modèle des autres sessions.

**A3.3 Conserver et signaler le statut de raffineur.**
`affinerOuvragesParModele()` doit rester un raffineur qui note des candidats heuristiques, jamais un détecteur autonome. L'interface doit signaler explicitement ce statut, et le contrôle vision `controleIA()` doit afficher, côte à côte, la classification heuristique, la confiance de la régression logistique et le verdict vision, avec stockage d'un court justificatif pour audit. Réf. 7.8 et 7.9 (les modèles de fondation conviennent au contrôle de plausibilité, pas à la détection autonome en faible résolution).

### A4. Interopérabilité et reprojection (condition d'appropriation)

**A4.1 Export GeoPackage aligné sur le schéma national.**
Ajouter un export GeoPackage (en plus des exports GeoJSON et CSV actuels) pour les traits de côte, les ouvrages et les statistiques d'évolution, avec le dictionnaire d'attributs aligné sur le schéma national (réf. 7.7) et les métadonnées minimales : type, longueur, `substitue_tc`, confiance, date de l'image, capteur, identifiant. Objectif : la donnée doit pouvoir remonter dans les observatoires et les SIG des collectivités. Réf. 7.6 et 7.7.

**A4.2 Reprojection locale à l'export.**
À l'export, reprojeter depuis le WGS84 interne vers le référentiel local du territoire actif (section 3.1) : EPSG 3297 et apparentés pour la Polynésie selon l'archipel, EPSG 3163 pour la Nouvelle-Calédonie, EPSG 5490 pour Saint-Martin et Saint-Barthélemy, EPSG 4467 pour Saint-Pierre-et-Miquelon, projection UTM 1S à confirmer pour Wallis-et-Futuna. La reprojection peut se faire en JS dans le navigateur (bibliothèque de transformation de coordonnées chargée en statique). Le code de projection de Wallis doit rester un paramètre éditable, non figé. Réf. 7.10 (référentiels géodésiques ultramarins).

**A4.3 Métadonnées de catalogue.**
Joindre à chaque export un bloc de métadonnées exploitable par les catalogues d'observatoire (champs descriptifs minimaux conformes aux pratiques des observatoires nationaux et ultramarins : producteur, date, emprise, source d'imagerie, licence, référentiel). Réf. 7.11 (réseau national des observatoires du trait de côte, charte d'adhésion).

### A5. Gouvernance des prérogatives et des licences dans l'interface

**A5.1 Bandeau de prérogatives par territoire.**
Afficher, pour le territoire actif, qui décide de quoi : l'État pour les risques et les référentiels nationaux ; la collectivité ou le Pays selon les cas pour l'urbanisme et l'aménagement ; les autorités coutumières en Nouvelle-Calédonie et à Wallis-et-Futuna pour toute recomposition touchant des terres coutumières. La plateforme alimente la décision, elle ne la prescrit pas. Réf. 7.12 (rapport de mission IGEDD-IGA et cadrage de conception).

**A5.2 Statut coutumier sur les couches concernées.**
En Nouvelle-Calédonie et à Wallis-et-Futuna, marquer les couches situées sur des terres coutumières par un statut explicite « décision relevant des instances coutumières ». La plateforme peut cartographier l'exposition sur ces terres, mais ne présente jamais une relocalisation comme acquise. Réf. 7.12.

**A5.3 Mention de licence par source d'imagerie.**
Afficher la licence de chaque source utilisée : Etalab 2.0 pour l'IGN (SPM, Saint-Martin, Saint-Barthélemy) ; CC BY-NC-SA pour l'imagerie Géorep de Nouvelle-Calédonie (interdiction d'usage commercial dérivé, partage à l'identique) ; licence Te Fenua pour la Polynésie à préciser ; conditions Dinamis ou SPC pour Wallis. Réf. 7.10 et section 3.

**A5.4 Garde-fou technique sur la licence calédonienne.**
Empêcher techniquement l'export public des dalles brutes de Nouvelle-Calédonie, pour respecter la clause non commerciale et partage à l'identique. Les produits dérivés (vecteurs) restent exportables sous réserve d'affichage de la licence d'origine. Réf. 7.10.

### A6. Équité territoriale dans le code

**A6.1 Dégradés de capacité assumés.**
Pour chaque fonction dépendant d'une donnée absente (par exemple `lancerMNT()` sans RGE ALTI en Polynésie et à Wallis), afficher un message clair indiquant la donnée manquante et l'alternative possible, plutôt qu'un échec silencieux ou un proxy trompeur. Réf. 7.13 (asymétrie documentaire entre territoires).

**A6.2 Mode « faible donnée » pour Wallis-et-Futuna et la Polynésie hors sites pilotes.**
Prévoir un mode où, faute d'archives et de MNT, la plateforme privilégie la saisie experte guidée et la veille (Lot B1), et signale explicitement le niveau de confiance réduit. Réf. 7.13 et section 3.3.

---

## 5. Lot B, évolutions client-serveur à moindre coût

Optionnel, activable territoire par territoire, sans jamais bloquer le Lot A. Architecture : front statique inchangé, fonctions serverless pour le déclenchement, traitement lourd discontinu, produits déposés en stockage objet et lus par le navigateur (voir 2.3 pour le détail du moindre coût).

### B0. Architecture cible

Le navigateur appelle une fonction serverless qui, soit renvoie un produit déjà calculé depuis le stockage objet, soit déclenche un traitement par lot. Les traitements lourds tournent hors ligne de l'utilisateur, écrivent leurs sorties (tuiles, GeoPackage, vecteurs d'alerte) en stockage objet, et signalent leur disponibilité. Aucun serveur permanent.

### B1. Veille de changement Sentinel-2 (chaînon d'actualisation manquant)

**Objectif.** Signaler où réexploiter de la très haute résolution, sans calculer de trait de côte fin en basse résolution. Logique hiérarchique : Sentinel-2 pour l'alerte, Landsat pour la tendance, très haute résolution pour la mesure. Réf. 7.14.
**Mise en œuvre à moindre coût.** Exécuter la détection de changement dans Google Earth Engine (usage recherche, gratuit) ou Copernicus Data Space, et n'exporter que de petits vecteurs d'alerte (segments où un changement significatif est détecté) vers le stockage objet. Le navigateur affiche ces alertes en surcouche sur la carte existante. Aucune infrastructure dédiée.
**Pertinence territoriale.** Particulièrement utile pour Wallis-et-Futuna et la Polynésie hors sites pilotes (mode faible donnée, A6.2), et pour le suivi rapproché post-Irma à Saint-Martin.

### B2. Segmentation profonde et modèle de fondation (fiabilisation forte)

**Objectif.** Améliorer la délimitation terre/eau et la première détection d'ouvrages au-delà de l'heuristique, notamment là où les archives manquent.
**Option recommandée pour territoires en déficit de données.** Tester un modèle de fondation géospatial multispectral sur Sentinel-2, qui atteint de bons résultats de délimitation côtière avec très peu d'images d'entraînement (réf. 7.9). Cela compense l'absence de MNT et d'ortho en Polynésie et à Wallis.
**Mise en œuvre à moindre coût.** Amorçage de l'entraînement sur une session de calcul gratuite (notebook), inférence par lot sur instance GPU à la demande allumée le temps du traitement puis éteinte, ou via une API d'inférence managée pour les volumes faibles. Poids stockés en objet et réutilisés. Le navigateur ne reçoit que des masques ou des vecteurs déjà calculés.
**Garde-fou.** Le résultat profond alimente le même rôle de raffineur et de contrôle que l'existant (A3.3) ; il ne devient pas un détecteur autonome non supervisé. Réf. 7.8 et 7.9.

### B3. Orthorectification et recalage (lever une limite structurelle)

**Objectif.** Corriger la principale limite géométrique actuelle (pas de recalage sub-pixellaire propre) sur les dalles lourdes, là où c'est nécessaire pour une mesure fiable.
**Mise en œuvre à moindre coût.** Traitement par lot ponctuel sur ressource éphémère, produisant des tuiles recalées déposées en stockage objet, que le navigateur consomme comme n'importe quelle source. Réf. 7.5 (sources d'erreur et recalage).
**Pertinence territoriale.** Prioritaire là où la décision foncière est imminente (recomposition de village, suivi de chantier post-cyclone).

### B4. Base temporelle des ouvrages (mémoire non écrasée)

**Objectif.** Historiser chaque ouvrage avec un statut (nouveau, maintenu, modifié, disparu) sans écraser l'historique, en cohérence avec les champs d'année d'apparition et de disparition du schéma national (A3.1).
**Mise en œuvre à moindre coût.** Base relationnelle serverless légère ou réutilisation de la base temps réel existante. Réf. 7.7 et 7.8.

---

## 6. Gouvernance de la donnée et appropriation locale (condition du livrable)

Le livrable est une plateforme web indépendante appropriable localement. Cette section conditionne l'acceptabilité par les acteurs et doit être traitée comme du code, pas comme un habillage.

1. **Détention de la donnée par le territoire.** Le tableau de bord territorial reste détenu et validé par la collectivité. Les pondérations (A1.2), les validations d'ouvrages (A3.2) et les notes appartiennent au territoire. Réf. 7.12.
2. **Licences respectées par construction.** Mention de licence par source (A5.3) et garde-fou technique calédonien (A5.4). Aucun export ne doit contredire la licence d'origine.
3. **Respect des prérogatives.** Bandeau de prérogatives (A5.1) et statut coutumier (A5.2) affichés pour chaque territoire concerné. La plateforme s'arrête au seuil de la décision.
4. **Interopérabilité vers les observatoires.** Export GeoPackage et métadonnées (A4) permettant la remontée vers OBLIC en Nouvelle-Calédonie, vers les observatoires des collectivités, et vers le réseau national. Réf. 7.11.
5. **Reprise en main locale.** Le mono-fichier, déployable en pages statiques, peut être hébergé par la collectivité elle-même. Documenter dans le dépôt : comment déployer, comment éditer le modèle `TERRITOIRES`, comment changer les sources d'imagerie et le référentiel d'export, comment activer ou non le Lot B. Objectif : aucune dépendance opaque à un tiers pour faire fonctionner le socle.
6. **Indicativité affichée.** La plateforme reste un appui à la décision indicatif qui ne crée aucune obligation. Cette mention, déjà présente, doit rester visible. Réf. 7.12.

---

## 7. Références méthodologiques

Toutes les références ci-dessous sont citées dans les tâches. Elles sont vérifiables. Lorsqu'un identifiant pérenne existe (DOI, code de rapport), il est indiqué.

**7.1 Indicateurs composites, cadre de référence.**
Nardo M., Saisana M., Saltelli A., Tarantola S., Hoffmann A., Giovannini E. (2008). *Handbook on Constructing Composite Indicators: Methodology and User Guide*. OCDE et Centre commun de recherche de la Commission européenne (JRC47008). ISBN 978-92-64-04345-9. Cadre en dix étapes : théorie, sélection, imputation, analyse multivariée, normalisation, pondération, agrégation, analyse d'incertitude et de sensibilité, retour aux données, visualisation. Points clés pour le scoring : la pondération égale est un choix, l'agrégation linéaire autorise la compensation entre dimensions, l'analyse de sensibilité aux pondérations est une exigence.

**7.2 Critique de l'indice de vulnérabilité côtière.**
Revue *Geo-Marine Letters* (2024), « Is the coastal vulnerability index a suitable index? Review and proposal of alternative indices for coastal vulnerability to sea level rise », doi:10.1007/s00367-024-00770-9. L'indice classique mélange variables d'aléa et de vulnérabilité et relève donc d'un indice de risque plutôt que de vulnérabilité ; d'où la nécessité de séparer aléa, enjeu et capacité (A1.4). Indice fondateur : Gornitz V. (1991).

**7.3 Trajectoire climatique de référence et projections régionalisées.**
Trajectoire de réchauffement de référence pour l'adaptation (TRACC), inscrite au Code de l'environnement par le décret n° 2026-23 du 23 janvier 2026 et l'arrêté du même jour : plus 2 °C en 2030, plus 2,7 °C en 2050, plus 4 °C en 2100 pour la France hexagonale ; déclinaisons ultramarines en cours, à dater explicitement. Projections d'élévation marine : GIEC, sixième rapport d'évaluation, groupe de travail I, table 9.9 (fourchettes likely à 2100 de 0,28 à 0,55 m sous SSP1-1.9 et de 0,63 à 1,01 m sous SSP5-8.5 ; trajectoire basse confiance SSP5-8.5 jusqu'à 0,63 à 1,60 m). Projections régionalisées disponibles via le catalogue Google Earth Engine (jeu AR6 Sea Level Projections) et le portail NASA Sea Level Change. Le Pacifique connaît généralement une élévation supérieure à la moyenne mondiale.

**7.4 Indicateurs de trait de côte adaptés aux côtes sans marée.**
Projet INSeaPTION (programme européen ERA4CS, BRGM, LIENSs, partenaires de Polynésie française). Deux indicateurs : ligne de stabilité (limite externe de végétation sur côte naturelle, base des ouvrages et remblais sur côte artificialisée) et pied de plage (limite entre platier récifal et plage, ou jet de rive). Seuils d'évolution : stable entre moins 4,5 et plus 4,5 m, accrétion au-delà de plus 4,5 m, érosion au-delà de moins 4,5 m. Découpage en sous-secteurs géomorphologiques (dix-neuf sous-secteurs à Moorea). Données publiées sur Sextant (Ifremer) pour Aratika, Tautira, Moorea. Échelle d'exploitation optimale calculée selon la méthode de Tobler (1987). Travaux associés : Duvat V. et collaborateurs (2017 et suivants) sur les Tuamotu et la Société.

**7.5 Budget d'incertitude des traits de côte.**
Trois sources : incertitude de mesure (résolution du pixel, géoréférencement, ombres, écume), incertitude liée à la marée et au jet de rive, incertitude humaine de digitalisation. Sur la façade atlantique européenne, l'incertitude de tendance est de l'ordre de 0,4 m par an (Castelle et collaborateurs, 2024). Sur les côtes sans marée, l'incertitude saisonnière du jet de rive domine et peut dépasser 2 m. La validation par mesure de terrain (GPS différentiel, drone, lidar) reste nécessaire. Pour la correction de marée, voir la chaîne CoastSat ci-dessous.

**7.6 Statistiques d'évolution normalisées.**
Digital Shoreline Analysis System (DSAS), USGS, version 5.x puis 6.x. Statistiques de référence : mouvement net du trait de côte (NSM), taux par les points extrêmes (EPR), régression linéaire (LRR) et régression linéaire pondérée par l'incertitude (WLR), intervalles de confiance à 90 %. Sortie standardisée exploitable en GeoPackage. Chaîne sub-pixellaire de référence : CoastSat (Vos K., Splinter K., Harley M., Simmons J., Turner I., 2019, *Environmental Modelling and Software*, doi:10.1016/j.envsoft.2019.104528 ; précision horizontale annoncée d'environ 10 m ; version 3.0 d'octobre 2024 intégrant la correction de marée FES2022). Limite : les SDS Landsat ne résolvent pas les changements inférieurs à environ 15 m (USGS, *Open-File Report 2025-1054*, doi:10.3133/ofr20251054).

**7.7 Typologie et cartographie des ouvrages.**
Cerema (août 2017), *Spécification technique de la cartographie des ouvrages et aménagements littoraux*, métropole et outre-mer, version 1.0. Trois niveaux d'attribution (catégorie, classe, type). Ouvrages se substituant au trait de côte : digue côtière, mur de soutènement, perré. Ouvrages de lutte contre l'érosion : brise-lames (longitudinal détaché, non rattaché au trait de côte, pour diminuer l'énergie de houle) et épi (transversal, placé sur l'estran). Attributs du schéma : orientation longitudinale ou transversale, longueur, année d'apparition, année de disparition, visibilité, hauteur. Base nationale Géolittoral de référence (cartographie nationale des ouvrages et aménagements littoraux).

**7.8 Assurance qualité d'un corpus d'apprentissage collaboratif.**
Bonnes pratiques : versionnage des labels et traçabilité de la lignée, identification et formation des opérateurs, règle de quorum (au moins deux opérateurs concordants pour promouvoir un label), jeu de test gelé pour mesurer la performance à chaque ré-entraînement et détecter une dérive. Principe issu des recommandations de cohérence d'interprétation (opérateur unique ou concordant, échelle constante) du protocole INSeaPTION (réf. 7.4) et des pratiques d'apprentissage supervisé partagé.

**7.9 Apprentissage profond et modèles de fondation pour la délimitation côtière.**
Segmentation sémantique (familles U-Net, SegFormer, DeepLab) pour la délimitation terre/eau. Modèle de fondation géospatial multispectral (famille Prithvi-EO-2.0, NASA et IBM, décembre 2024, arXiv 2412.02732) : bons résultats de délimitation côtière de petites îles sablonneuses avec très peu d'images d'entraînement (application Maldives sur Sentinel-2, novembre 2025, arXiv 2511.10177 ; F1 supérieur à 0,94 et IoU supérieur à 0,79 avec cinq images). Le modèle requiert des bandes Sentinel-2 (visible, proche infrarouge, deux infrarouges courts), incompatibles avec les seules orthos RGB mais adaptées à la veille satellitaire. Segment Anything Model (Meta, 2023) utilisable en zéro-shot avec prompting, mais limité en faible résolution (Osco et collaborateurs, 2023) : à réserver au contrôle assisté, pas à la détection autonome.

**7.10 Référentiels géodésiques et licences ultramarines.**
Polynésie française : RGPF (géographique EPSG 4687), UTM par archipel, zone 6S EPSG 3297 pour la Société (Tahiti, Moorea). Nouvelle-Calédonie : RGNC91-93 (géographique EPSG 4749), Lambert Nouvelle-Calédonie EPSG 3163. Antilles (Saint-Martin, Saint-Barthélemy) : RGAF09 (géographique EPSG 5489), UTM 20N EPSG 5490. Saint-Pierre-et-Miquelon : RGSPM06 (géographique EPSG 4463), UTM 21N EPSG 4467. Wallis-et-Futuna : RGWF96 (géographique EPSG 4480), projection métrique UTM zone 1S, code EPSG à confirmer localement. Licences : Etalab 2.0 pour l'IGN ; CC BY-NC-SA pour l'imagerie Géorep de Nouvelle-Calédonie (non commerciale, partage à l'identique) ; licence Te Fenua à préciser pour la Polynésie ; conditions Dinamis ou SPC pour Wallis.

**7.11 Réseau national des observatoires du trait de côte et observatoires ultramarins.**
Réseau national des observatoires du trait de côte (créé en 2017), charte d'adhésion fixant des règles d'acquisition, de qualification et de mise à disposition. Observatoires ultramarins documentés : OBLIC en Nouvelle-Calédonie (depuis 2013, Service géologique de Nouvelle-Calédonie et DIMENC avec le BRGM), observatoires de Guadeloupe, Martinique, Guyane (ODyC), La Réunion (Nout Bord'mer) et Mayotte. Saint-Pierre-et-Miquelon, Saint-Martin, Saint-Barthélemy, Polynésie française et Wallis-et-Futuna ne disposent pas d'observatoire formalisé du trait de côte au sens du réseau.

**7.12 Cadrage de mission et prérogatives.**
Rapport IGEDD-IGA (août 2025), *Étude complémentaire sur les outre-mer dans le cadre de la définition d'un modèle de financement pour accompagner la recomposition spatiale des territoires littoraux soumis au recul du trait de côte* (rapport 014917-02A), Daou S., Leclerc B. (IGEDD), Debrosse P., Klés V. (IGA). Cadrage des prérogatives : État pour les risques et référentiels nationaux ; collectivité ou Pays pour l'urbanisme et l'aménagement selon le statut ; autorités coutumières pour les terres coutumières inaliénables en Nouvelle-Calédonie et à Wallis-et-Futuna. La plateforme alimente la décision sans la prescrire.

**7.13 Asymétrie documentaire entre territoires.**
Documentée par l'absence d'indicateur national d'érosion sur les six COM (l'indicateur national couvre les cinq départements d'outre-mer, hors COM), par l'absence de MNT national et d'observatoire formalisé en Polynésie française hors sites pilotes et à Wallis-et-Futuna, et par la licence restrictive de l'imagerie calédonienne. Pour Saint-Martin et Saint-Barthélemy, synthèse Cerema 2023 et atlas BRGM (RP-65212-FR, étude Irma RP-67291-FR) en lieu et place d'un observatoire. Pour Wallis-et-Futuna, aucun rapport dédié au trait de côte n'a été publié récemment ; rapport BRGM RP-61407-FR (2012) sur les granulats signalant l'effet aggravant des prélèvements de sable.

**7.14 Articulation veille basse résolution et mesure très haute résolution.**
Logique hiérarchique : Sentinel-2 (10 m, revisite cinq jours) pour la veille et l'alerte de changement, Landsat (30 m, archives depuis 1984) pour la tendance de long terme, très haute résolution (Pléiades, ortho IGN, imagerie commerciale) pour la confirmation et la mesure fine. Barnard P. et collaborateurs (2023), *Cambridge Prisms: Coastal Futures*, doi:10.1017/cft.2022.4. Produits ouverts utilisables pour le Pacifique : Digital Earth Pacific (Pacific Community, SPC), pour la Nouvelle-Calédonie et Wallis-et-Futuna.

---

## 8. Critères de recette (définition de « terminé »)

**Lot A1, scoring.** Le volet méthode affiche la composition, la normalisation et la pondération de chaque score. Les pondérations sont modifiables et journalisées. Le curseur de sensibilité recalcule et affiche l'enveloppe de variation. Aléa, enjeu et capacité sont présentés séparément. La projection TRACC et la fourchette d'élévation régionalisée s'affichent par territoire avec source datée.

**Lot A2, trait de côte.** Pour `pf`, `nc`, `wallis`, la ligne de stabilité et le pied de plage sont produits et étiquetés distinctement. Chaque trait porte une incertitude positionnelle affichée et exportée. Le seuil d'évolution de plus ou moins 4,5 m est appliqué et paramétrable. Les statistiques NSM et EPR sont calculées et exportables.

**Lot A3, ouvrages.** Les attributs produits correspondent exactement au schéma national (catégorie, classe, type, orientation, longueur, années, visibilité, `substitue_tc`). La règle de quorum et l'identifiant d'opérateur sont effectifs sur le corpus partagé. Le jeu de test gelé mesure la performance à chaque ré-entraînement. Le statut de raffineur est signalé, le contrôle vision affiche les trois verdicts.

**Lot A4, interopérabilité.** L'export GeoPackage est produit avec le dictionnaire d'attributs et les métadonnées. La reprojection vers le référentiel local du territoire actif est correcte et vérifiée sur un point de contrôle par territoire. Le code de projection de Wallis est éditable.

**Lot A5, gouvernance.** Le bandeau de prérogatives et la mention de licence s'affichent par territoire. Le statut coutumier marque les couches concernées en Nouvelle-Calédonie et à Wallis. L'export des dalles brutes de Nouvelle-Calédonie est techniquement empêché.

**Lot A6, équité.** Chaque fonction dépendant d'une donnée absente affiche un message explicite et une alternative, sans échec silencieux. Le mode faible donnée est disponible pour Wallis et la Polynésie hors sites pilotes.

**Lot B, client-serveur.** Chaque brique fonctionne sans serveur permanent, lit ou écrit en stockage objet, et n'altère jamais le fonctionnement du Lot A si elle est désactivée. La veille Sentinel-2 produit des vecteurs d'alerte affichés en surcouche. La segmentation profonde reste un raffineur. Test contradictoire visé : sur une plage témoin par territoire, écart moyen inférieur à 5 m par rapport à un levé GPS différentiel ou drone de référence, lorsqu'un tel levé existe.

---

## 9. Séquencement recommandé

1. **Lot A5 et A6 d'abord (gouvernance et équité).** Faible coût technique, fort effet d'acceptabilité, condition d'appropriation. Bandeau de prérogatives, licences, statut coutumier, garde-fou calédonien, dégradés assumés.
2. **Lot A4 (interopérabilité et reprojection).** Débloque la remontée vers les observatoires et l'usage par les services techniques. Prérequis de crédibilité.
3. **Lot A1 (scoring).** Valorise le kit littoral et le rend défendable en réunion.
4. **Lot A2 et A3 (trait de côte et ouvrages).** Fiabilise la chaîne de détection.
5. **Lot B1 (veille Sentinel-2).** Premier pas client-serveur, à coût quasi nul, comble le chaînon d'actualisation et sert prioritairement les territoires en déficit de données.
6. **Lot B2, B3, B4.** Selon le besoin réel et la disponibilité d'un levé de validation, en respectant la discipline de moindre coût (pré-calcul, déclenchement discontinu, stockage objet).

**Seuils déclencheurs de révision du plan.** Mise à jour de l'indicateur national d'érosion intégrant des COM ; nouvelle version majeure de la trajectoire de réchauffement de référence ; publication d'un module Digital Earth Pacific couvrant Wallis-et-Futuna ; sortie d'un successeur de modèle de fondation capable d'un plongement multispectral à très haute résolution.

---

*Document de travail à valeur de cahier des charges. Sources : document de conception du portail, rapport d'état de l'art associé, pièces de la mission (rapport IGEDD-IGA 014917-02A d'août 2025, fiches INSeaPTION, spécification Cerema des ouvrages littoraux). Aucune valeur prescriptive sur la décision publique : la plateforme reste un appui indicatif. Les références de la section 7 doivent être vérifiées et, le cas échéant, actualisées au moment de la mise en œuvre.*
