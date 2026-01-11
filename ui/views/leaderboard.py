# ui/views/leaderboard.py
import streamlit as st
import pandas as pd
from core.database import run_query

def render_leaderboard():
    st.markdown("### 🏆 Classement Mondial des Experts")
    st.markdown("Découvrez qui sont les leaders de la Supply Chain Performance.")
    
    # Récupération de tous les utilisateurs (Top 100)
    users = run_query('''
        SELECT name, total_score, level, city, last_seen 
        FROM users 
        ORDER BY total_score DESC 
        LIMIT 100
    ''', fetch_all=True)
    
    if not users:
        st.info("Le classement est vide pour le moment.")
        return

    # Transformation en DataFrame pour un bel affichage
    df = pd.DataFrame(users, columns=["Expert", "Score Prestige", "Niveau", "Ville", "Dernière Activité"])
    
    # Ajout du rang
    df.index = range(1, len(df) + 1)
    df.index.name = "Rang"

    # Style pour le podium
    def color_rows(row):
        if row.name == 1: return ['background-color: rgba(255, 215, 0, 0.1)'] * len(row)
        if row.name == 2: return ['background-color: rgba(192, 192, 192, 0.1)'] * len(row)
        if row.name == 3: return ['background-color: rgba(205, 127, 50, 0.1)'] * len(row)
        return [''] * len(row)

    st.table(df.style.apply(color_rows, axis=1))

    st.markdown("---")
    st.caption("Le score Prestige est cumulé à chaque bonne réponse (+20 pts). Les crises maîtrisées et les diplômes augmentent votre renommée.")
