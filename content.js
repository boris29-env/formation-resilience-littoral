/* ============================================================================
   Bibliothèques de contenu pour Cap 2028 (mission IGEDD n° 016714-01)
   « Comment bien préparer les sorties d'emplois fonctionnels de l'IGEDD ? »

   Module ES importé par cap2028.html. Aucune donnée nominative.
   Chaque item est étiqueté avec un ou plusieurs axes thématiques (A à H).
   ============================================================================ */

export const AXES = {
  A: "Organisation interne apprenante",
  B: "Parcours-types de professionnalisation",
  C: "Marque employeur et rayonnement",
  D: "Leviers indemnitaires et statutaires",
  E: "Dimension territoriale (MIGT)",
  F: "Mobilisation des réseaux professionnels",
  G: "Déontologie et indépendance",
  H: "Coopération institutionnelle"
};

export const CONTENT = {

  axes: ["A","B","C","D","E","F","G","H"],

  /* ------------------------------------------------------------------
     Design fiction : questions prospectives et signaux faibles
     ------------------------------------------------------------------ */
  designFiction: {
    prompts: [
      { texte: "Et si, en 2030, le passage par l'IGEDD était devenu un label de carrière explicitement reconnu par les employeurs publics ?", axes: ["C"] },
      { texte: "Et si chaque inspecteur disposait, dès son recrutement, d'un contrat de parcours assorti d'une cible de sortie ?", axes: ["A","B"] },
      { texte: "Et si les MIGT devenaient la première porte d'entrée vers des postes en services déconcentrés et en collectivités ?", axes: ["E"] },
      { texte: "Et si, faute de préparation, une partie des inspecteurs se retrouvait en disponibilité subie en fin de mandat ?", axes: ["A","D"], noir: true },
      { texte: "Et si l'IGEDD publiait chaque année l'annuaire anonymisé des trajectoires de ses anciens ?", axes: ["C"] },
      { texte: "Et si l'encadrement déontologique des passages vers le secteur privé se durcissait sensiblement d'ici 2032 ?", axes: ["G"] },
      { texte: "Et si la lisibilité de la trajectoire indemnitaire devenait le premier argument de recrutement de l'IGEDD ?", axes: ["D"] },
      { texte: "Et si, en 2032, un réseau alumni actif ouvrait chaque année des débouchés identifiés aux inspecteurs en fin de mandat ?", axes: ["C","F"] },
      { texte: "Et si les employeurs du pôle ministériel réservaient chaque année des postes fléchés aux sortants des inspections générales ?", axes: ["H"] },
      { texte: "Et si, en 2030, le renouvellement du détachement était devenu l'exception, et la sortie préparée la norme ?", axes: ["B","D"] },
      { texte: "Et si une part importante des inspecteurs quittait l'IGEDD avant le terme du mandat, faute de visibilité sur la suite ?", axes: ["A","C"], noir: true },
      { texte: "Et si la formation suivie à l'IGEDD était certifiante et reconnue sur le marché des cadres dirigeants publics ?", axes: ["A","B"] }
    ],
    signauxFaibles: [
      "Montée des mobilités de cadres supérieurs vers les opérateurs et les collectivités",
      "Attentes croissantes des recruteurs sur les compétences managériales démontrées",
      "Exigence accrue de transparence sur les parcours des hauts fonctionnaires",
      "Tension sur les rémunérations proposées en sortie d'emploi fonctionnel",
      "Rôle croissant des réseaux d'anciens dans l'accès aux postes de direction",
      "Vigilance déontologique renforcée sur les passages entre public et privé",
      "Généralisation des mandats à durée déterminée dans l'encadrement supérieur",
      "Concurrence entre inspections générales pour attirer les mêmes profils",
      "Développement du mentorat et du coaching dans la fonction publique",
      "Demande des employeurs territoriaux pour des profils rompus à l'évaluation des politiques publiques",
      "Importance prise par la visibilité professionnelle numérique des cadres publics",
      "Montée en puissance des DRH ministérielles sur la gestion personnalisée des cadres supérieurs",
      "Difficultés de repositionnement observées dans d'autres corps après détachement",
      "Attrait croissant des cadres expérimentés pour les fonctions d'expertise plutôt que de direction",
      "Valorisation par les recruteurs des expériences territoriales et de terrain",
      "Allongement des carrières et multiplication des transitions professionnelles tardives"
    ]
  },

  /* ------------------------------------------------------------------
     Codéveloppement : situations anonymes proposables par l'animateur
     ------------------------------------------------------------------ */
  codev: {
    situations: [
      { texte: "Un inspecteur arrive à dix-huit mois de la fin de son premier mandat. Les postes qu'il identifie ne correspondent pas au niveau de responsabilité qu'il exerçait avant de rejoindre l'IGEDD. Il s'interroge sur la manière d'élargir sa recherche sans dévaloriser son parcours, et sur ce que l'institution peut faire pour l'appuyer.", axes: ["A","B","D"] },
      { texte: "Une inspectrice envisage de rejoindre une collectivité territoriale dont le projet correspond à ses aspirations. La discontinuité indemnitaire qu'entraînerait ce départ la fait hésiter. Elle cherche comment objectiver l'écart, le négocier avec l'employeur pressenti, et sécuriser sa trajectoire sur la durée.", axes: ["D"] },
      { texte: "Un inspecteur est sollicité par un opérateur qu'il a contrôlé récemment. L'offre est attractive et correspond à ses compétences. Il s'interroge sur le risque déontologique de ce rapprochement, sur la saisine éventuelle de la HATVP et sur l'image renvoyée à l'institution.", axes: ["G"] },
      { texte: "Un inspecteur peut revenir dans son corps d'origine à l'issue du mandat. Il craint un repositionnement en retrait par rapport aux fonctions qu'il occupe à l'IGEDD. Il cherche comment préparer ce retour pour qu'il soit perçu comme une étape de parcours et non comme un recul.", axes: ["B","D"] },
      { texte: "Un inspecteur très expérimenté, recruté en fin de carrière, approche du terme de son mandat. Il hésite entre demander un second détachement et s'orienter vers un poste d'expertise. Il souhaite l'avis du groupe sur la manière d'arbitrer entre ces deux voies et sur le bon moment pour décider.", axes: ["B","D"] },
      { texte: "Une inspectrice affectée en MIGT a construit un ancrage territorial solide. Elle souhaite le valoriser auprès d'employeurs régionaux (services déconcentrés, opérateurs, collectivités) mais peine à formaliser cette expérience dans un dossier de candidature. Elle demande au groupe comment traduire cet ancrage en compétences lisibles.", axes: ["E"] }
    ]
  },

  /* ------------------------------------------------------------------
     Six chapeaux : sujets avec une consigne par chapeau
     ------------------------------------------------------------------ */
  sixChapeaux: {
    sujets: [
      {
        titre: "La préparation des sorties d'emploi fonctionnel à l'IGEDD",
        axes: ["A"],
        consignes: {
          blanc: "Que savons-nous de façon certaine des sorties à venir : échéances, dispositifs existants, cadre statutaire ?",
          rouge: "Que suscite, chez vous, la perspective de la sortie, sans avoir à le justifier ?",
          noir:  "Quels sont les risques, les angles morts et les fragilités du dispositif actuel ?",
          jaune: "Quels atouts et quelles opportunités la sortie peut-elle représenter ?",
          vert:  "Quelles idées neuves pour mieux préparer la sortie ?",
          bleu:  "Comment séquencer et piloter concrètement cette préparation, et qui en est responsable ?"
        }
      },
      {
        titre: "La marque employeur de l'IGEDD",
        axes: ["C"],
        consignes: {
          blanc: "Comment l'IGEDD est-elle perçue aujourd'hui par les employeurs publics ? Que savons-nous de sa notoriété réelle ?",
          rouge: "Qu'éprouvez-vous à l'idée de vous présenter comme ancien de l'IGEDD : fierté, doute, indifférence ?",
          noir:  "Qu'est-ce qui affaiblit aujourd'hui la reconnaissance du passage par l'IGEDD ?",
          jaune: "Qu'apporterait une marque employeur forte, au recrutement comme à la sortie ?",
          vert:  "Quelles initiatives concrètes pour faire rayonner l'inspection : annuaire des trajectoires, réseau alumni, événements ?",
          bleu:  "Qui doit porter la marque employeur, avec quels moyens et quel calendrier ?"
        }
      },
      {
        titre: "La sécurisation des trajectoires indemnitaires et statutaires",
        axes: ["D"],
        consignes: {
          blanc: "Quels sont les faits : effets de seuil, changements de groupe, règles du second détachement, conditions du retour au corps d'origine ?",
          rouge: "Comment vivez-vous l'incertitude sur la rémunération et le statut après le mandat ?",
          noir:  "Quels risques, individuels et collectifs, si la trajectoire reste illisible ?",
          jaune: "Que permettrait une trajectoire lisible avant, pendant et après le mandat ?",
          vert:  "Quelles pistes pour amortir les discontinuités : mécanismes transitoires, information précoce, accompagnement ?",
          bleu:  "Qui doit instruire ces leviers, avec la DES, la DIESE et les DRH ministérielles, et selon quel séquencement ?"
        }
      },
      {
        titre: "Le rôle des MIGT dans la diversification des parcours",
        axes: ["E"],
        consignes: {
          blanc: "Que savons-nous du positionnement des MIGT et de leurs liens avec les services déconcentrés, les opérateurs et les collectivités ?",
          rouge: "Quel rapport personnel entretenez-vous avec l'ancrage territorial : attrait, éloignement, contrainte ?",
          noir:  "Quelles limites à faire des MIGT un levier de sortie : accès inégal, charge des missions, lisibilité ?",
          jaune: "Quels bénéfices l'expérience territoriale apporte-t-elle, aux employeurs comme aux inspecteurs ?",
          vert:  "Comment amplifier ce levier : mobilités croisées, partenariats régionaux, missions partagées ?",
          bleu:  "Comment organiser la contribution des MIGT à la préparation des sorties, et qui la coordonne ?"
        }
      }
    ]
  },

  /* ------------------------------------------------------------------
     Débat mouvant : affirmations clivantes, défendables des deux côtés
     ------------------------------------------------------------------ */
  debatMouvant: {
    affirmations: [
      { texte: "Sans accompagnement formalisé dès le recrutement, la sortie d'emploi fonctionnel restera subie.", axes: ["A","B"] },
      { texte: "La lisibilité de la trajectoire indemnitaire est le premier facteur d'attractivité de l'IGEDD.", axes: ["D"] },
      { texte: "Aujourd'hui, le passage à l'IGEDD est un atout personnel, pas un label reconnu par les employeurs.", axes: ["C"] },
      { texte: "Le retour au corps d'origine doit rester la voie de sortie par défaut.", axes: ["B","D"] },
      { texte: "La dimension territoriale portée par les MIGT est le principal différenciant de l'IGEDD face aux autres inspections.", axes: ["E"] },
      { texte: "Un second détachement ne doit pas devenir la solution de facilité.", axes: ["B"] },
      { texte: "Une déontologie exigeante limite, de fait, l'employabilité des inspecteurs en sortie.", axes: ["G"] },
      { texte: "L'IGEDD devrait communiquer publiquement sur les trajectoires de ses anciens.", axes: ["C"] },
      { texte: "La préparation de la sortie relève d'abord de l'agent, pas de l'institution.", axes: ["A","H"] },
      { texte: "Le choix des missions confiées pendant le mandat doit être orienté par le projet de sortie de l'inspecteur.", axes: ["A","B"] },
      { texte: "L'IGEDD doit mobiliser systématiquement les réseaux professionnels de ses membres au profit des sortants.", axes: ["F"] },
      { texte: "Sans coopération étroite avec la DIESE et les DRH ministérielles, aucun dispositif de sortie ne fonctionnera.", axes: ["H"] },
      { texte: "Les inspecteurs des groupes supérieurs n'ont pas besoin du même accompagnement que les autres.", axes: ["A","D"] }
    ]
  },

  /* ------------------------------------------------------------------
     World café : jeux de trois tables thématiques
     ------------------------------------------------------------------ */
  worldCafe: {
    jeux: [
      {
        nom: "Préparer (les trois temps du mandat)",
        axes: ["A","B"],
        tables: [
          "Dès le recrutement : quel contrat de parcours ?",
          "Pendant le mandat : quelles missions et formations pour se rendre visible ?",
          "À l'approche de la sortie : quels dispositifs d'accompagnement ?"
        ]
      },
      {
        nom: "Valoriser (atouts et leviers)",
        axes: ["C","D","E"],
        tables: [
          "Marque employeur et réseau alumni",
          "Dimension territoriale et MIGT",
          "Leviers indemnitaires et statutaires"
        ]
      },
      {
        nom: "Sécuriser (cadre et coopérations)",
        axes: ["F","G","H"],
        tables: [
          "Déontologie et prévention des conflits d'intérêts",
          "Mobilisation des réseaux professionnels",
          "Coopération avec les employeurs et les DRH du pôle ministériel"
        ]
      },
      {
        nom: "Comparer (parangonnage)",
        axes: ["B","C"],
        tables: [
          "Que retenir des pratiques de l'IGF et du CGAAER ?",
          "Que retenir de la Cour des comptes et des chambres régionales et territoriales des comptes ?",
          "Quelles pratiques des cabinets de conseil méritent d'être transposées ?"
        ]
      }
    ]
  },

  /* ------------------------------------------------------------------
     Cartographie d'arguments : thèses et amorces pour et contre
     ------------------------------------------------------------------ */
  cartoArguments: {
    theses: [
      {
        texte: "L'IGEDD doit valoriser explicitement le passage en inspection comme label de carrière.",
        axes: ["C"],
        amorces: [
          { type: "pour",   parent: "root", texte: "Un label reconnu renforce l'attractivité du recrutement et facilite le repositionnement en sortie." },
          { type: "pour",   parent: "root", texte: "Une marque employeur lisible aligne l'IGEDD sur les pratiques des inspections comparables." },
          { type: "contre", parent: "root", texte: "Un label trop marqué peut figer les profils et nuire à la diversité des parcours." },
          { type: "contre", parent: "root", texte: "La valorisation externe peut entrer en tension avec l'exigence de réserve et d'impartialité de l'inspection." }
        ]
      },
      {
        texte: "Chaque inspecteur doit signer, dès le recrutement, un contrat de parcours avec une cible de sortie.",
        axes: ["A","B"],
        amorces: [
          { type: "pour",   parent: "root", texte: "Un contrat donne dès l'entrée un horizon clair et engage l'agent comme l'institution." },
          { type: "pour",   parent: "root", texte: "Une cible explicite permet d'orienter les missions et les formations tout au long du mandat." },
          { type: "contre", parent: "root", texte: "Une cible fixée cinq ans à l'avance risque d'être obsolète au moment de la sortie." },
          { type: "contre", parent: "root", texte: "Le contrat peut rigidifier la gestion et être perçu comme un droit acquis difficile à tenir." }
        ]
      },
      {
        texte: "Le pilotage de la préparation des sorties doit être confié au Secrétariat général de l'IGEDD.",
        axes: ["A"],
        amorces: [
          { type: "pour",   parent: "root", texte: "Un pilotage unique garantit la continuité du dispositif et l'équité entre inspecteurs." },
          { type: "pour",   parent: "root", texte: "Le Secrétariat général dispose de la vision d'ensemble des effectifs et des échéances." },
          { type: "contre", parent: "root", texte: "Un pilotage central éloigne la démarche du terrain des sections et des MIGT." },
          { type: "contre", parent: "root", texte: "La responsabilité de la sortie doit rester d'abord partagée entre l'agent et son encadrement direct." }
        ]
      },
      {
        texte: "Les sorties vers le secteur privé doivent être encadrées plus strictement que les autres.",
        axes: ["G"],
        amorces: [
          { type: "pour",   parent: "root", texte: "L'impartialité de l'inspection exige des garanties renforcées sur les passages vers les entités contrôlées." },
          { type: "pour",   parent: "root", texte: "Anticiper les exigences de la HATVP sécurise l'agent comme l'institution." },
          { type: "contre", parent: "root", texte: "Un encadrement différencié peut dissuader des candidatures de qualité au recrutement." },
          { type: "contre", parent: "root", texte: "Le droit commun de la déontologie suffit s'il est appliqué avec rigueur et anticipation." }
        ]
      },
      {
        texte: "Les MIGT doivent devenir le levier prioritaire d'élargissement des employeurs potentiels.",
        axes: ["E"],
        amorces: [
          { type: "pour",   parent: "root", texte: "L'ancrage territorial ouvre l'accès aux services déconcentrés, aux opérateurs et aux collectivités." },
          { type: "pour",   parent: "root", texte: "La dimension territoriale différencie l'IGEDD des autres inspections générales." },
          { type: "contre", parent: "root", texte: "Tous les inspecteurs ne passent pas en MIGT : prioriser ce levier crée une inégalité d'accès aux débouchés." },
          { type: "contre", parent: "root", texte: "Les employeurs territoriaux ne représentent qu'une partie des débouchés au niveau attendu en sortie." }
        ]
      },
      {
        texte: "La préparation de la sortie doit commencer dès la première année du mandat.",
        axes: ["A","B"],
        amorces: [
          { type: "pour",   parent: "root", texte: "L'anticipation élargit le champ des possibles et étale dans le temps formations et mises en visibilité." },
          { type: "pour",   parent: "root", texte: "Les premiers départs de janvier 2028 montrent que cinq ans constituent un horizon court." },
          { type: "contre", parent: "root", texte: "Une préparation trop précoce peut détourner l'inspecteur de l'investissement dans ses missions." },
          { type: "contre", parent: "root", texte: "Le projet de sortie se précise surtout en seconde partie de mandat, à la lumière des missions réalisées." }
        ]
      }
    ]
  }
};
