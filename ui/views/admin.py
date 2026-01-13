# ui/views/admin.py
import streamlit as st
import pandas as pd
from core.database import run_query
from utils.export_utils import create_excel_export

def render_admin_dashboard():
    st.title("👨‍💼 Tableau de Bord Administrateur")
    st.markdown("Vue exhaustive des utilisateurs et de leurs interactions.")

    tab1, tab2, tab3 = st.tabs(["👥 Liste des Utilisateurs", "📩 Feedbacks & Messages", "🛠️ Maintenance & Stock"])

    with tab1:
        st.subheader("Base Utilisateurs")
        # Récupération de tous les utilisateurs
        users = run_query("SELECT user_id, name, email, level, xp, total_score, hearts, q_count, city, last_seen FROM users ORDER BY last_seen DESC", fetch_all=True)
        if users:
            df_users = pd.DataFrame(users, columns=["ID", "Prénom", "Email", "Niv", "XP", "Score", "Vies", "Q. Répondues", "Ville", "Dernière connexion"])
            st.dataframe(df_users, use_container_width=True)
            
            # Export Excel des utilisateurs
            if st.button("📥 Exporter la base utilisateurs (Excel)", use_container_width=True):
                data_dict = df_users.to_dict(orient='records')
                # Simplification pour l'export util
                export_data = {f"{u['Prénom']} ({u['Email']})": f"Niveau {u['Niv']} - {u['XP']} XP" for u in data_dict}
                output = create_excel_export("Base Utilisateurs Mentor SC", export_data, {"Total Users": len(df_users)})
                st.download_button("💾 Télécharger Base_Users.xlsx", output, "MentorSC_Users.xlsx")
        else:
            st.info("Aucun utilisateur trouvé.")

    with tab2:
        st.subheader("Messages reçus")
        feedback = run_query("SELECT timestamp, user_name, user_email, message, context FROM user_feedback ORDER BY timestamp DESC", fetch_all=True)
        if feedback:
            df_feedback = pd.DataFrame(feedback, columns=["Date", "Auteur", "Email", "Message", "Provenance"])
            st.table(df_feedback)
            
            if st.button("🗑️ Purger les feedbacks", type="primary"):
                run_query("DELETE FROM user_feedback", commit=True)
                st.success("Feedbacks effacés.")
                st.rerun()
        else:
            st.info("Aucun message reçu pour le moment.")

    with tab3:
        st.subheader("État de la Banque de Questions")
        stats = run_query("SELECT level, COUNT(*) FROM question_bank GROUP BY level", fetch_all=True)
        if stats:
            df_stats = pd.DataFrame(stats, columns=["Niveau", "Nombre de Questions"])
            st.bar_chart(df_stats.set_index("Niveau"))
            st.table(df_stats)
        
        st.markdown("---")
        st.markdown("##### 🚀 Remplissage Manuel (X3)")
        st.write("Cette opération va générer 5 nouvelles triades (15 questions) pour chaque module du curriculum via l'IA.")
        if st.button("🔥 Lancer le Stockage Massif", use_container_width=True):
            from services.stocker import stock_database
            with st.status("Génération en cours (cela peut prendre 2-3 minutes)..."):
                stock_database()
            st.success("Banque de questions enrichie avec succès !")
            st.rerun()
