# services/content_service.py
import random
from typing import Dict, List

# Base de secours "Elite" classée par difficulté
FALLBACK_DATABASE = {
    1: [ # NIVEAU 1 : FONDAMENTAUX
        {
            "question": "Quelle est la définition fondamentale de la Supply Chain ?",
            "options": {"A": "Le transport uniquement", "B": "La gestion des flux physiques, infos et financiers", "C": "L'achat au prix bas", "D": "Le stockage"},
            "correct": "B", "explanation": "Elle englobe tous les flux du fournisseur au client final.",
            "category": "Fondamentaux", "concept_key": "Supply Chain Definition", "concept_def": "Gestion globale des flux.",
            "theory": "La SC est une vision systémique de l'entreprise.", "example": "Coordination entre usine et transporteur.", "tip": "Pensez 'End-to-End'."
        },
        {
            "question": "Le 'Lead Time' correspond à :",
            "options": {"A": "Le temps de transport", "B": "Le délai entre commande et réception", "C": "La durée de stockage", "D": "Le temps de production"},
            "correct": "B", "explanation": "C'est le temps de traversée total du flux.",
            "category": "Logistique", "concept_key": "Lead Time", "concept_def": "Temps de réponse du flux.",
            "theory": "Indicateur clé de réactivité.", "example": "Si je commande lundi et reçoit jeudi, LT = 3 jours.", "tip": "Réduire le LT améliore le BFR."
        }
    ],
    2: [ # NIVEAU 2 : PLANIFICATION
        {
            "question": "Dans le calcul du stock de sécurité, quel facteur est primordial ?",
            "options": {"A": "La couleur du produit", "B": "La variabilité de la demande et du délai", "C": "Le nombre de caristes", "D": "La taille de l'usine"},
            "correct": "B", "explanation": "Le stock de sécurité couvre les incertitudes.",
            "category": "Stocks", "concept_key": "Stock de Sécurité", "concept_def": "Tampon contre l'aléa.",
            "theory": "Basé sur la loi normale (Sigma).", "example": "Retard fournisseur de 2 jours imprévu.", "tip": "Un taux de service de 100% est économiquement impossible."
        }
    ],
    3: [ # NIVEAU 3 : STRATÉGIE & DIGITAL
        {
            "question": "Qu'est-ce que l'effet 'Coup de Fouet' (Bullwhip Effect) ?",
            "options": {"A": "Une méthode autoritaire", "B": "L'amplification de la variabilité vers l'amont", "C": "L'accélération des flux", "D": "La réduction des stocks"},
            "correct": "B", "explanation": "Une petite variation client devient un tsunami chez le fournisseur.",
            "category": "Planification", "concept_key": "Bullwhip Effect", "concept_def": "Distorsion de l'info.",
            "theory": "Causé par le manque de visibilité.", "example": "Surproduction massive suite à une promo locale.", "tip": "Le VMI (Vendor Managed Inventory) est un remède efficace."
        }
    ],
    4: [ # NIVEAU 4 : LEAN & MANAGEMENT
        {
            "question": "En Lean, que signifie le terme 'Muda' ?",
            "options": {"A": "Standard", "B": "Gaspillage", "C": "Vitesse", "D": "Qualité"},
            "correct": "B", "explanation": "Tout ce qui n'apporte pas de valeur au client.",
            "category": "Stratégie Lean", "concept_key": "Muda", "concept_def": "Gaspillage technique.",
            "theory": "Il existe 7 types de Mudas (TIMWOOD).", "example": "Attendre une validation mail pendant 2 jours.", "tip": "La surproduction est le pire des Mudas."
        }
    ]
}

def get_fallback_question(level: int = 1) -> Dict:
    """Renvoie une question de secours adaptée au niveau de l'utilisateur."""
    # On prend les questions du niveau actuel, ou du niveau inférieur si vide
    pool = FALLBACK_DATABASE.get(level, FALLBACK_DATABASE[1])
    q = random.choice(pool).copy()
    q["is_fallback"] = True
    return q
