# app.py
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv
import os

# Chargement direct des clés
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

from core.database import init_db, run_query
from ui.styles import apply_styles
from ui.components import render_sidebar, render_mentor_footer
from ui.views.auth import render_login
from ui.views.mission import render_mission
from ui.views.coach import render_coach
from ui.views.masterclass import render_masterclass
from ui.views.notes import render_notes
from ui.views.profile import render_profile
from ui.views.glossary import render_glossary
from utils.assets import trigger_queued_sounds
from services.certificate_factory import show_diploma_celebration
import time 

def main():
    st.set_page_config(page_title="Mentor SC", page_icon="📦", layout="wide")
    apply_styles()
    init_db()

    # --- DÉTECTION ÉCHEC CRISE VIA URL (INFAILLIBLE) ---
    if st.query_params.get("status") == "crisis_fail":
        uid = st.session_state.get('user_id') or st.query_params.get('uid')
        if uid:
            # 1. Application de la sanction
            st.session_state.hearts = max(0, st.session_state.get('hearts', 3) - 2)
            st.session_state.crisis_active = False
            st.session_state.answered = True
            st.session_state.result = "LOSS"
            st.session_state.last_result = "LOSS"
            st.session_state.show_crisis_failure_dialog_trigger = True # Flag spécifique
            
            # 2. Synchronisation DB
            run_query('UPDATE users SET hearts=? WHERE user_id=?', (st.session_state.hearts, uid), commit=True)
            
            # 3. Nettoyage URL
            st.query_params.clear()
            st.query_params["uid"] = uid
            st.rerun()

    # --- PERSISTANCE DE SESSION (Auto-Login via URL) ---
    if not st.session_state.get('auth') and 'uid' in st.query_params:
        uid = st.query_params['uid']
        res = run_query('SELECT * FROM users WHERE user_id=?', (uid,), fetch_one=True)
        if res:
            st.session_state.update({
                'auth':True, 'user_id':res[0], 'user':res[1], 'user_email': res[9], 'user_city': res[10],
                'level':int(res[2] or 1), 'xp':int(res[3] or 0), 'total_score':int(res[4] or 0),
                'mastery':int(res[5] or 0), 'q_count':int(res[6] or 0), 'hearts':int(res[7] or 3),
                'xp_checkpoint':int(res[12] or 0), 'crisis_wins': int(res[13] or 0),
                'redemptions': int(res[14] or 0), 'has_diploma': bool(res[15] or 0),
                'current_run_xp': int(res[16] or 0),
                'joker_5050': int(res[17] if len(res)>17 else 3), 
                'joker_hint': int(res[18] if len(res)>18 else 3),
                'data': None, 'question_queue': [], 'consecutive_wins': 0,
                'active_tab': 'mission', 'celebration_done': False, 'show_diploma': False,
                'prefetched_data': None, 'current_engine': 'Base de données',
                'crisis_dialog_shown': False, 'result': None, 'last_result': None,
                'crisis_active': False, 'crisis_start_time': 0, 'answered': False,
                'show_chaos_celebration': False, 'show_operator_celebration': False,
                'pending_badge': None
            })

    if 'auth' not in st.session_state:
        st.session_state.update({
            'auth': False, 'user': '', 'user_id': '', 'level': 1, 'xp': 0, 'hearts': 5,
            'q_count': 0, 'mastery': 0, 'total_score': 0, 'active_tab': 'mission',
            'question_queue': [], 'chat_history': [], 'data': None,
            'mentor_message': '', 'last_result': None, 'mentor_voice': True,
            'result': None, # ICI
            'crisis_active': False, 'answered': False,
            'redemptions': 0, 'crisis_wins': 0, 'redemption_mode': False, 
            'redemption_count': 0, 'consecutive_wins': 0, 'session_cleaned': False, 
            'current_engine': 'Auto', 'has_diploma': False,
            'show_diploma': False, 'refill_in_progress': False,
            'celebration_done': False,
            'joker_5050': 0, 'joker_hint': 0, 'active_joker_5050': False,
            'prefetched_data': None,
            'crisis_active': False, 'crisis_start_time': 0,
            'crisis_dialog_shown': False,
            'show_chaos_celebration': False,
            'show_operator_celebration': False # ICI
        })

    if not st.session_state.auth:
        render_login()
    else:
        # --- CÉLÉBRATION DIPLÔME (Écran prioritaire) ---
        if st.session_state.show_diploma:
            show_diploma_celebration()
            return # On stoppe le rendu ici pour afficher uniquement la fête

        # 1. RENDU BARRE LATÉRALE (Uniquement ici)
        with st.sidebar:
            render_sidebar()

        # 2. Événements de fond
        trigger_queued_sounds()
        
        # 3. Navigation Principale
        menu = {
            "mission": "🎯 Mission", 
            "coach": "💬 Mentor SC", 
            "process": "📚 Master Class", 
            "glossary": "📖 Glossaire", 
            "notes": "📝 Notes", 
            "profile": "📊 Profil",
            "leaderboard": "🏆 Classement"
        }
        
        if "active_tab" not in st.session_state:
            st.session_state.active_tab = "mission"

        selected = st.pills(
            "Menu", 
            options=list(menu.keys()), 
            format_func=lambda x: menu[x], 
            default=st.session_state.active_tab, 
            label_visibility="collapsed",
            key="main_nav_pills"
        )
        
        if selected and selected != st.session_state.active_tab:
            st.session_state.active_tab = selected
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        uid = st.session_state.user_id
        tab = st.session_state.active_tab
        
        if tab == "mission": render_mission()
        elif tab == "coach": render_coach()
        elif tab == "process": render_masterclass()
        elif tab == "leaderboard":
            from ui.views.leaderboard import render_leaderboard
            render_leaderboard()
        elif tab == "notes": render_notes(uid)
        elif tab == "profile": render_profile(uid)
        elif tab == "glossary": render_glossary(uid)

        # Le footer est géré ici globalement mais ne s'affiche que s'il y a un message
        render_mentor_footer()
        
        # --- AUTO-TRIGGER CÉLÉBRATION (Pour démo "Diplome") ---
        # Si c'est l'user "Diplome" et qu'on n'a pas encore fait la fête...
        if st.session_state.user == "Diplome" and not st.session_state.get('celebration_done'):
            time.sleep(5) # Délai de 5 secondes (l'interface est visible mais figée)
            st.session_state.show_diploma = True
            st.session_state.celebration_done = True
            st.session_state.has_diploma = True # On s'assure qu'il l'a
            run_query("UPDATE users SET has_diploma=1 WHERE user_id=?", (st.session_state.user_id,), commit=True)
            st.rerun()

        # --- AUTO-TRIGGER BADGE (Pour démo "Badge") ---
        if st.session_state.user == "Badge" and not st.session_state.get('operator_celebration_done'):
            time.sleep(5)
            # Force les données pour que le profil soit cohérent
            st.session_state.q_count = 5
            st.session_state.crisis_wins = 1
            run_query("UPDATE users SET q_count=5, crisis_wins=1 WHERE user_id=?", (st.session_state.user_id,), commit=True)
            
            st.session_state.show_operator_celebration = True
            st.session_state.operator_celebration_done = True
            st.rerun()

if __name__ == "__main__":
    main()
