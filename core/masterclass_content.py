MASTERCLASS_DATA = {
    "SESSION 1": {
        "title": "🏛️ Stratégie & Réseau",
        "modules": {
            "1.1 Stratégie & Architecture": """
### L'ALIGNEMENT STRATÉGIQUE (Fisher’s Matrix)

La théorie de Marshall Fisher est fondamentale : une Supply Chain ne peut pas être performante partout. Elle doit être alignée avec la nature du produit.

#### 1. Les Produits Fonctionnels (Ex: Pâtes, Ampoules, Ciment)
*   **Caractéristiques** : Demande stable et prévisible, cycle de vie long (> 2 ans), marge faible, faible variété.
*   **Stratégie requise : EFFICIENTE (Lean)**.
*   **Priorité** : Réduction des coûts physiques à tout prix.
*   **Moyens** : Taux d'utilisation des machines maximal, production en gros lots, stocks minimisés, fournisseurs low-cost (même lointains).
*   **Exemple** : Action ou Lidl.

#### 2. Les Produits Innovants (Ex: Mode, Smartphones)
*   **Caractéristiques** : Demande imprévisible, cycle de vie court (3 mois), marge forte, forte variété.
*   **Stratégie requise : RÉACTIVE (Agile)**.
*   **Priorité** : Vitesse et Disponibilité (Service).
*   **Moyens** : Capacités excédentaires (buffers) pour absorber les pics, fournisseurs de proximité (même plus chers), stocks de sécurité élevés pour ne jamais manquer une vente.
*   **Exemple** : Zara (Production en Europe, transport avion accepté).

---

### DESIGN DU RÉSEAU (Network Design)

L'arbitrage entre Coût de Transport et Coût de Stockage.

#### Centralisé (1 Hub Européen)
*   **Pour qui ?** Produits à forte valeur (Luxe, Pharma), produits à rotation lente (Slow movers).
*   **Avantages** : Réduction massive du stock global (mutualisation des aléas : si l'Espagne vend moins, l'Allemagne vend plus, le stock central compense). Coûts fixes réduits (1 seul loyer, 1 seule équipe).
*   **Inconvénients** : Délai de livraison plus long vers le client final. Coût de transport aval plus élevé.

#### Décentralisé (5 Entrepôts Régionaux)
*   **Pour qui ?** Produits lourds/volumineux (Eau, Meubles), produits à forte rotation (Fast movers).
*   **Avantages** : Livraison J+1 garantie. Coût transport final faible (proximité).
*   **Inconvénients** : Explosion du stock (il faut du stock de sécurité partout). Frais fixes multipliés.

#### La Loi de la Racine Carrée (Square Root Law)
Elle quantifie le gain de stock lors d'une centralisation.
*   *Formule* : Stock Futur = Stock Actuel * Racine(Nb Entrepôts Futurs / Nb Entrepôts Actuels).
*   *Impact* : Passer de 4 entrepôts à 1 seul réduit mécaniquement le stock de sécurité de **50%**. C'est un levier de cash massif.

---

### MATRICE DE KRALJIC (Stratégie Achats)

Croisement de l'**Impact Financier** et du **Risque Approvisionnement**.

1.  **Achats Simples** (Faible/Faible) : Fournitures, Visserie standard.
    *   *Enjeu* : Efficacité administrative.
    *   *Action* : Automatiser (Catalogues en ligne, P-Cards). Ne pas passer de temps à négocier.
2.  **Achats Levier** (Fort Impact/Faible Risque) : Électricité, Transport standard, Carton.
    *   *Enjeu* : Profitabilité.
    *   *Action* : Mise en concurrence agressive (Appels d'offres). Le marché est abondant, profitez-en.
3.  **Achats Goulot** (Faible Impact/Fort Risque) : Pièce détachée unique, Arôme spécifique.
    *   *Enjeu* : Continuité des opérations.
    *   *Action* : Sécuriser le stock. Ne pas chercher le prix, chercher la garantie de livraison.
4.  **Achats Stratégiques** (Fort/Fort) : Moteur, Ingrédient clé.
    *   *Enjeu* : Avantage concurrentiel.
    *   *Action* : Partenariat long terme. Innovation commune. On ne change pas de fournisseur.
            """
        }
    },
    "SESSION 2": {
        "title": "📈 S&OP & Prévisions",
        "modules": {
            "1.2 Pilotage de la Demande": """
### LE S&OP (SALES & OPERATIONS PLANNING)

Processus de décision mensuel pour aligner Ventes, Ops et Finance sur un horizon tactique (3-18 mois).

#### Les 5 Étapes Standard :
1.  **Portfolio Review** (Marketing) : Nettoyage du catalogue. On ne prévoit pas ce qu'on ne vend plus.
2.  **Demand Review** (Sales) : Calcul de la "Demande Non Contrainte" (ce qu'on vendrait si on avait stock infini). C'est le souhait commercial.
3.  **Supply Review** (Ops) : Calcul de la capacité réelle (Usine/Fournisseurs). Identification des goulots d'étranglement.
4.  **Reconciliation (Pre-S&OP)** : Le cœur du travail. On identifie les écarts (Demande > Offre) et on prépare des scénarios chiffrés pour la direction (ex: "Payer des heures sups pour produire plus" vs "Lisser la demande").
5.  **Executive S&OP** (CEO) : Arbitrage final et validation du "One Number Plan".

---

### LA SCIENCE DE LA PRÉVISION

#### Décomposition de la Demande
*   **Tendance (Trend)** : La direction de fond (hausse, baisse, stable).
*   **Saisonnalité** : Les cycles récurrents (ex: Pic en Décembre, Creux en Août).
*   **Bruit (Noise)** : L'aléatoire pur. Impossible à prévoir.

#### Nettoyage de l'Historique (Baseline)
C'est l'étape critique. Si vous avez vendu 10 000 unités en mars grâce à une promo exceptionnelle, ne donnez pas ce chiffre brut au logiciel pour l'an prochain. Il faut "lisser" l'historique pour trouver la vente naturelle (Baseline) et ajouter les promos futures comme des "blocs" (Building Blocks).

#### Indicateurs de Performance (KPI)
*   **Biais (Bias)** : Somme(Prévision - Réel). Indique si on est structurellement optimiste ou pessimiste. Un biais persistant est plus grave qu'une erreur ponctuelle car il crée du surstock (optimisme) ou de la rupture (pessimisme).
*   **MAPE** : L'erreur absolue moyenne en %. C'est le thermomètre de la fiabilité.
*   **FVA (Forecast Value Added)** : Mesure la valeur ajoutée de chaque étape.
    *   *Calcul* : Précision du Logiciel vs Précision après correction humaine.
    *   *Constat* : Souvent, les corrections manuelles des commerciaux dégradent la précision du logiciel. Le FVA permet de le prouver factuellement.
            """
        }
    },
    "SESSION 3": {
        "title": "📦 Gestion des Stocks",
        "modules": {
            "2.1 Paramétrage Expert": """
### SEGMENTATION AVANCÉE (ABC-XYZ)

Le pilotage fin demande de croiser la **Valeur** (ABC) et la **Volatilité** (XYZ).

*   **AX (Haute Valeur / Stable)** : Les produits faciles et rentables. Gestion en flux tendu, automatisée, stock de sécurité très faible.
*   **AY (Haute Valeur / Variable)** : Demande attention. Prévision collaborative nécessaire.
*   **AZ (Haute Valeur / Imprévisible)** : **DANGER**. Stocker du Z coûte une fortune en obsolescence. Stratégie : Centralisation maximale (1 point de stock mondial) ou Make-to-Order (pas de stock).
*   **CX (Faible Valeur / Stable)** : Gestion basique.
*   **CZ (Faible Valeur / Imprévisible)** : Les "irritants". Stratégie : Stocker massivement (ex: 1 an de stock). Le coût de possession est faible et cela évite les ruptures et les frais de gestion.

---

### LE STOCK DE SÉCURITÉ (Safety Stock)

Il couvre deux risques distincts :
1.  **Incertitude Demande** : Le client commande plus que prévu.
2.  **Incertitude Délai** : Le fournisseur livre en retard.

#### La Formule Experte
`SS = Z * Racine( (SigmaD² * L) + (SigmaL² * Dmoy²) )`

*   **Z (Facteur de Service)** : Dépend de votre taux de service cible.
    *   95% = 1.65 écarts-types.
    *   98% = 2.05 écarts-types.
    *   99.9% = 3.09 écarts-types.
    *   *Impact* : Passer de 95% à 99% augmente le stock de sécurité de **+40% à +60%**.
*   **SigmaD** : La variabilité des ventes (écart-type).
*   **L** : Le délai moyen.
*   **SigmaL** : La variabilité du délai fournisseur (sa fiabilité).

#### Levier de réduction
Pour baisser le stock sans baisser le taux de service, le levier le plus puissant est souvent de **fiabiliser le fournisseur** (réduire SigmaL) plutôt que d'améliorer la prévision (difficile). Un fournisseur régulier permet de réduire les stocks.

---

### FIABILITÉ DES STOCKS (IRA)

Un WMS ne sert à rien si les stocks informatiques sont faux.
*   **Inventaire Tournant (Cycle Counting)** : Compter une partie du stock chaque jour.
    *   Les articles A : Comptés 1 fois par mois. Tolérance erreur < 0.5%.
    *   Les articles B : 1 fois par trimestre.
    *   Les articles C : 1 fois par an.
*   **Objectif IRA (Inventory Record Accuracy)** : > 98%. En dessous, le MRP (calcul de besoins) génère des commandes fausses.
            """
        }
    },
    "SESSION 4": {
        "title": "💰 Finance & Cash",
        "modules": {
            "3.1 Finance Supply Chain": """
### TOTAL LANDED COST (Le Coût Complet)

Acheter en Chine semble moins cher (Prix Ex-Works), mais il faut calculer l'addition complète jusqu'à l'entrepôt :
1.  **Prix Achat** (Matière + Marge fournisseur).
2.  **Emballage** (Packing, Palettisation).
3.  **Pré-acheminement** (Transport usine -> Port départ).
4.  **Douane Export** (Frais locaux).
5.  **Fret Principal** (Maritime/Aérien).
6.  **Assurance** (Ad valorem).
7.  **Droits de Douane (Duty)** : % sur la valeur CIF (Marchandise + Fret).
8.  **Post-acheminement** (Port arrivée -> Entrepôt).
9.  **Coût de Possession** : Le coût financier du stock immobilisé pendant les 6 semaines de transport (Cash bloqué).

---

### OPTIMISATION EOQ & FRANCO

#### Formule de Wilson (EOQ)
Elle détermine la quantité de commande optimale qui minimise la somme des **Coûts de Passation** (Administratif) et des **Coûts de Possession** (Stockage).
`EOQ = Racine( (2 * Demande * Coût Commande) / Coût Possession Unitaire )`

#### Le Dilemme du Franco
Le fournisseur offre le transport pour une grosse commande.
*   **Calcul** : Comparer le "Gain Transport" (ex: 500€) avec le "Surcoût de Possession" (Coût de stocker le surplus pendant des mois).
*   Si Gain > Surcoût : Accepter. Sinon, refuser et payer le transport (ou négocier le seuil).

---

### INCOTERMS 2020

Ils définissent le transfert de **Frais** et de **Risques**.
*   **EXW (Ex-Works)** : L'acheteur gère tout depuis l'usine fournisseur. **Risqué**. Vous êtes responsable de la déclaration douane export dans un pays dont vous ignorez les lois.
*   **FCA (Free Carrier)** : Mieux que EXW. Le fournisseur gère la douane export, vous prenez la main ensuite.
*   **FOB (Free On Board)** : Standard import maritime. Le fournisseur paie jusqu'au bateau. Vous choisissez le fret maritime et maîtrisez le coût et le délai.
*   **DDP (Delivered Duty Paid)** : Le fournisseur livre chez vous tout payé. Confort total, mais vous perdez le contrôle du transport et payez souvent une marge cachée dessus.

### CASH MANAGEMENT & BFR
Le stock est une dette.
*   **BFR (Besoin en Fonds de Roulement)** : Stock + Créances Clients - Dettes Fournisseurs.
*   **Cash-to-Cash Cycle** : Le temps entre le paiement de la matière et l'encaissement du client.
*   **Levier** : Négocier le DPO (Délai paiement fournisseur). Passer de 30 à 60 jours finance 1 mois de stock gratuitement.
            """
        }
    },
    "SESSION 5": {
        "title": "🚚 Logistique Physique",
        "modules": {
            "4.1 Entrepôt & Transport": """
### GESTION D'ENTREPÔT (WMS)

**Règle d'Or** : "Système > Humain". Si le WMS dit de poser en A12, on pose en A12. Sinon, l'inventaire devient faux.

#### Stratégies de Rangement (Putaway)
*   **Chaotique (Random)** : On met la palette dans le premier trou vide. Optimise le taux de remplissage mais nécessite un WMS fiable.
*   **Dédié (Fixed)** : Chaque produit a sa place attitrée. Plus visuel mais perd de la place (si le stock est vide, la place reste vide).

#### Stratégies de Préparation (Picking)
*   **Pick to Order** : Le préparateur fait tout le tour de l'entrepôt pour 1 commande. (Inefficace).
*   **Batch Picking** : Le système regroupe 10 commandes. Le préparateur va une fois à l'emplacement et prend 10 articles. (Gain productivité énorme).
*   **Slotting** : Placer les articles A (Forte rotation) près des quais et à hauteur d'homme (Golden Zone) pour réduire les trajets et la fatigue.

---

### TRANSPORT

#### Le Poids Volumétrique (Taxable Weight)
Les transporteurs (surtout aérien/express) facturent au plus élevé entre le Poids Réel et le Volume converti.
*   **Règle Aérien** : 1 m³ = 167 kg (Ratio 1:6).
*   *Exemple* : 1m³ de plumes (10kg réel) sera facturé comme 167kg.
*   *Action* : Densifier les emballages, éviter de transporter de l'air.

#### Modes d'expédition
*   **FCL (Full Container Load)** : Conteneur complet. Forfait fixe. Rentable si rempli > 70%.
*   **LCL (Less than Container Load)** : Groupage. On paie au m³. Rentable pour les petits volumes (< 13m³).

---

### DOUANE

*   **HS Code (Nomenclature)** : Code universel (6 chiffres + suffixes) qui définit le produit et sa taxe. Une erreur de classement expose à un redressement fiscal sur 3 ans.
*   **Origine (Made In)** : Dépend de la "dernière transformation substantielle", pas juste de l'expédition. Un produit assemblé en France avec 90% de composants chinois peut rester d'origine chinoise selon les règles.
*   **OEA (Opérateur Économique Agréé)** : Statut de confiance accordé par la Douane. Permet de réduire les contrôles physiques et d'accélérer le dédouanement. Vital pour les gros importateurs.
            """
        }
    },
    "SESSION 6": {
        "title": "🚀 Futur & Leadership",
        "modules": {
            "5.1 Stratégie & RSE": """
### SUPPLY CHAIN ANALYTICS

Sortir de l'**Excel Hell** (dépendance à des fichiers macros locaux, fragiles et non sécurisés).
La Stack Moderne :
*   **ETL (Power Query)** : Pour automatiser le nettoyage des données (80% du temps gagné).
*   **BI (Power BI / Tableau)** : Pour la visualisation et la communication vers la DG.
*   **Python** : Pour les prévisions avancées et le Big Data.

### LEADERSHIP & CHANGE

Le Directeur SC est transverse. Il doit influencer sans avoir d'autorité hiérarchique sur l'Usine ou le Commerce.
*   **Méthode** : Parler le langage de l'autre.
    *   Au Financier : Parlez BFR et Cash.
    *   Au Commercial : Parlez Disponibilité et Parts de marché.
*   **Modèle ADKAR** : Pour gérer le changement (nouvel ERP).
    *   **A**wareness (Conscience du problème).
    *   **D**esire (Envie de changer).
    *   **K**nowledge (Formation).
    *   **A**bility (Coaching terrain).
    *   **R**einforcement (Célébration pour ancrer).

### RSE & DURABILITÉ

*   **Scope 3** : C'est là que tout se joue (Emissions des Fournisseurs + Transport). Souvent 80% de l'impact total.
    *   *Levier* : Basculer de l'Avion au Maritime (-95% CO2).
*   **Loi AGEC** : Fin de la destruction des invendus. Obligation de gérer la Reverse Logistics (Retours, Dons, Recyclage).
*   **Résilience (China + 1)** : Stratégie de sourcing pour ne jamais dépendre d'un seul pays. Avoir une source Low-Cost (Asie) et une source Réactive (Proche Import) pour basculer en cas de crise.
            """
        }
    }
}