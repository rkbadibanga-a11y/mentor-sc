# core/badges.py
import datetime
import streamlit as st
from core.database import run_query

def calculate_badges(uid):
    """Calcule la liste des badges acquis selon les stats actuelles (DB + Session)."""
    
    # 1. Récupération des données fraîches
    # On prend les valeurs de session qui sont plus à jour que la DB juste après une réponse
    qc = st.session_state.get('q_count', 0)
    lvl = st.session_state.get('level', 1)
    wins = st.session_state.get('consecutive_wins', 0)
    cw = st.session_state.get('crisis_wins', 0)
    rd = st.session_state.get('redemptions', 0)
    
    # Pour les stats par catégorie, on doit interroger la DB car c'est là qu'elles sont stockées/cumulées
    # Attention : la réponse courante vient peut-être d'être ajoutée dans quiz_engine, il faut que run_query ait accès aux dernières données.
    # Dans quiz_engine, on fait INSERT INTO history mais on n'update pas forcément la table stats (à vérifier).
    # Vérification faite : quiz_engine n'update PAS la table `stats` explicitement dans validate_answer ! 
    # C'est un bug potentiel. On va corriger ça.
    
    d = dict(run_query('SELECT category, correct_count FROM stats WHERE user_id = ?', (uid,), fetch_all=True))
    
    # Glossaire
    glossary_count_res = run_query('SELECT COUNT(*) FROM glossary WHERE user_id = ?', (uid,), fetch_one=True)
    glossary_count = glossary_count_res[0] if glossary_count_res else 0
    
    # Heure
    current_hour = datetime.datetime.now().hour
    is_night_owl = current_hour >= 22 or current_hour <= 6

    # 2. Définition des règles
    badges_def = [
        # Carrière
        ("🔰", "Opérateur SC", qc >= 5, "A répondu à 5 questions."),
        ("📦", "Resp. Exploitation", qc >= 120, "Expertise validée (Niveau 1 fini)."),
        ("🚚", "Coordinateur Flux", lvl >= 2, "A atteint le Niveau 2."),
        ("📊", "Planificateur Confirmé", qc >= 250, "Expertise validée (Niveau 2 fini)."),
        ("⚙️", "Ingénieur SC", lvl >= 3, "A atteint le Niveau 3."),
        ("🔮", "Data Strategist SC", qc >= 380, "Expertise validée (Niveau 3 fini)."),
        ("🏭", "COO (Directeur Ops)", lvl >= 4, "A atteint le Niveau 4."),
        ("👑", "Visionnaire SC", qc >= 500, "Le sommet de la Supply Chain."),
        
        # Spécialisations (Basé sur table stats)
        ("💸", "Le Négociateur", d.get('Achats', 0) >= 10, "10 bonnes réponses en Achats."),
        ("🧊", "Gardien du Stock", d.get('Stocks', 0) >= 20, "20 bonnes réponses en Stocks."),
        ("🚢", "Globe-Trotter", d.get('Transport', 0) >= 15, "15 bonnes réponses en Transport."),
        ("🤖", "Oracle Digital", d.get('IA & Data', 0) >= 15, "15 bonnes réponses en IA/Data."),
        ("🥋", "Sensei Lean", d.get('Stratégie Lean', 0) >= 15, "15 bonnes réponses en Lean."),
        
        # Gameplay
        ("🔥", "Maître du Chaos", cw >= 1, "A survécu à une crise."),
        ("🔥", "On Fire", wins >= 10, "10 victoires consécutives."),
        ("🧟", "Le Survivant", rd >= 1, "A utilisé une rédemption."),
        ("📚", "L'Encyclopédie", glossary_count >= 50, "Glossaire riche de 50 termes."),
        ("🦉", "Oiseau de Nuit", is_night_owl, "Travaille tard le soir.")
    ]
    
    earned = []
    metadata = {}
    
    for emoji, title, condition, desc in badges_def:
        if condition:
            earned.append(title)
            metadata[title] = {"emoji": emoji, "desc": desc}
            
    return earned, metadata

def get_badge_groups():
    """Retourne la structure d'affichage des badges (Titre de section -> Liste de badges)."""
    return [
        ("📈 Rangs de Carrière", [
            ("🔰", "Opérateur SC", "5 questions"), ("📦", "Resp. Exploitation", "Niv 1"),
            ("🚚", "Coordinateur Flux", "Niv 2 atteint"), ("📊", "Planificateur Confirmé", "Niv 2 fini"),
            ("⚙️", "Ingénieur SC", "Niv 3 atteint"), ("🔮", "Data Strategist SC", "Niv 3 fini"),
            ("🏭", "COO (Directeur Ops)", "Niv 4 atteint"), ("👑", "Visionnaire SC", "Titre Ultime")
        ]),
        ("🎯 Spécialisations", [
            ("💸", "Le Négociateur", "10 Achats"), ("🧊", "Gardien du Stock", "20 Stocks"),
            ("🚢", "Globe-Trotter", "Expert Transport"), ("🤖", "Oracle Digital", "Maître IA"),
            ("🥋", "Sensei Lean", "Expert Lean"), ("🔥", "Maître du Chaos", "1ère Crise maîtrisée")
        ]),
        ("🎮 Gameplay", [
            ("🔥", "On Fire", "10 victoires"), ("🧟", "Le Survivant", "1 Rédemption"),
            ("📚", "L'Encyclopédie", "50 termes"), ("🦉", "Oiseau de Nuit", "Session nocturne")
        ])
    ]

def check_new_badge(uid):
    """Vérifie si un nouveau badge vient d'être débloqué."""
    current_earned, metadata = calculate_badges(uid)
    
    # On récupère les anciens (stockés en session)
    previous_earned = st.session_state.get('earned_badges_cache', [])
    
    # Diff
    new_badges = [b for b in current_earned if b not in previous_earned]
    
    # Mise à jour du cache
    st.session_state.earned_badges_cache = current_earned
    
    # Si nouveau badge, on retourne le premier (pour affichage modal)
    if new_badges:
        title = new_badges[0]
        return {
            "title": title,
            "emoji": metadata[title]["emoji"],
            "desc": metadata[title]["desc"]
        }
    return None
