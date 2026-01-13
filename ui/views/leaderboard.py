# ui/views/leaderboard.py
import streamlit as st
import pandas as pd
from core.database import run_query

def render_leaderboard():
    st.markdown("### 🏆 Classement Mondial des Experts")
    
    # Explication de la règle de gestion (Transparence)
    st.info("""
    **⚖️ Règle du Classement :** L'expertise (le **Niveau**) est la priorité absolue. 
    À niveau égal, les experts sont départagés par leur **Score Prestige** (XP cumulée).
    """)
    
    # Récupération de tous les utilisateurs (Top 100) triés par Niveau puis Score
    users = run_query('''
        SELECT name, level, total_score, city, last_seen 
        FROM users 
        ORDER BY level DESC, total_score DESC 
        LIMIT 100
    ''', fetch_all=True)
    
    if not users:
        st.info("Le classement est vide pour le moment.")
        return

    # Transformation en DataFrame pour un bel affichage
    df = pd.DataFrame(users, columns=["Expert", "Niveau", "Score Prestige", "Ville", "Dernière Activité"])
    
    # Mapping des noms de niveaux (Grades)
    grade_map = {
        1: "🔰 Opérateur",
        2: "📦 Coordinateur",
        3: "🌐 Architecte",
        4: "🏭 Directeur (COO)",
        5: "👑 Visionnaire"
    }
    df['Grade'] = df['Niveau'].map(grade_map)
    
    # Réorganisation des colonnes pour mettre le Grade en avant
    df = df[["Expert", "Grade", "Niveau", "Score Prestige", "Ville", "Dernière Activité"]]
    
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
    st.caption("💡 Le grade (Niveau) reflète votre avancement dans le curriculum. Le score Prestige est le cumul de vos bonnes réponses. Plus vous montez en niveau, plus votre autorité dans le classement est forte.")
