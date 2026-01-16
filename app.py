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
from ui.views.tools import render_tools
from ui.views.admin import render_admin_dashboard
from utils.assets import trigger_queued_sounds
from services.certificate_factory import show_diploma_celebration
import extra_streamlit_components as stx

def main():
    st.set_page_config(page_title="Mentor SC", page_icon="📦", layout="wide")
    
    # CRITIQUE : Les styles doivent être appliqués à chaque rafraîchissement
    apply_styles()
    
    # Init DB une seule fois par session serveur
    if 'db_init' not in st.session_state:
        init_db()
        st.session_state.db_init = True

    # --- GESTION DES COOKIES ---
    if 'cookie_manager' not in st.session_state:
        st.session_state.cookie_manager = stx.CookieManager(key="cookie_manager_main")
    
    # --- GESTION CALLBACK GOOGLE ---
    if "code" in st.query_params:
        from services.auth_google import handle_google_callback
        handle_google_callback()

    # 1. Auto-Login via Cookie
    if not st.session_state.get('auth') and not st.session_state.get('cookie_checked') and not st.session_state.get('logout_in_progress'):
        all_cookies = st.session_state.cookie_manager.get_all()
        if all_cookies is not None:
            saved_uid = all_cookies.get('mentor_sc_uid')
            if saved_uid:
                if not st.session_state.get('cloud_synced'):
                    from core.database import pull_user_data_from_supabase
                    pull_user_data_from_supabase(saved_uid)
                    st.session_state.cloud_synced = True
                
                res = run_query('SELECT * FROM users WHERE user_id=?', (saved_uid,), fetch_one=True)
                if res:
                    st.session_state.update({
                        'auth':True, 'user_id':res[0], 'user':res[1], 'user_email': res[9], 'user_city': res[10],
                        'level':int(res[2] or 1), 'xp':int(res[3] or 0), 'total_score':int(res[4] or 0),
                        'mastery':int(res[5] or 0), 'q_count':int(res[6] or 0), 'hearts':int(res[7] or 3),
                        'active_tab': 'mission', 'cookie_checked': True, 'data': None
                    })
                    st.rerun()
            st.session_state.cookie_checked = True

    # --- PERSISTANCE DE SESSION (Auto-Login via URL) ---
    if not st.session_state.get('auth') and 'uid' in st.query_params:
        uid = st.query_params['uid']
        res = run_query('SELECT * FROM users WHERE user_id=?', (uid,), fetch_one=True)
        if not res:
            from core.database import pull_user_data_from_supabase
            if pull_user_data_from_supabase(uid):
                res = run_query('SELECT * FROM users WHERE user_id=?', (uid,), fetch_one=True)

        if res:
            from datetime import datetime, timedelta
            st.session_state.cookie_manager.set('mentor_sc_uid', uid, expires_at=datetime.now() + timedelta(days=30))
            st.session_state.update({
                'auth':True, 'user_id':res[0], 'user':res[1], 'user_email': res[9], 'user_city': res[10],
                'level':int(res[2] or 1), 'xp':int(res[3] or 0), 'total_score':int(res[4] or 0),
                'mastery':int(res[5] or 0), 'q_count':int(res[6] or 0), 'hearts':int(res[7] or 3),
                'active_tab': 'mission', 'data': None
            })
            st.query_params.clear()
            st.rerun()

    # Initialisation des variables de session si non authentifié
    if 'auth' not in st.session_state:
        st.session_state.update({
            'auth': False, 'user': '', 'user_id': '', 'level': 1, 'xp': 0, 'hearts': 5,
            'active_tab': 'mission', 'question_queue': [], 'chat_history': [], 'data': None,
            'mentor_voice': True, 'crisis_active': False, 'answered': False, 'q_count': 0, 'mastery': 0, 'total_score': 0
        })

    if not st.session_state.auth:
        render_login()
    else:
        if st.session_state.get('show_diploma'):
            show_diploma_celebration()
            return

        with st.sidebar:
            render_sidebar()

        trigger_queued_sounds()
        
        # Navigation avec EMOJIS (Restaurés)
        menu = {
            "mission": "🎯 Mission", 
            "coach": "🧠 Audit", 
            "process": "📚 MasterClass", 
            "tools": "🛠️ Outils", 
            "glossary": "📖 Glossaire", 
            "notes": "📝 Notes", 
            "profile": "📊 Profil", 
            "leaderboard": "🏆 Top"
        }
        if st.session_state.get('user_email') in os.getenv("ADMIN_EMAILS", ["r.k.badibanga@gmail.com"]):
            menu["admin"] = "👮 Admin"

        selected = st.pills("Navigation", options=list(menu.keys()), format_func=lambda x: menu[x], 
                           default=st.session_state.get('active_tab', 'mission'), 
                           label_visibility="collapsed", key="main_nav_pills_v5")
        
        if selected and selected != st.session_state.active_tab:
            st.session_state.active_tab = selected
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        tab = st.session_state.active_tab
        
        if tab == "mission": render_mission()
        elif tab == "coach": render_coach()
        elif tab == "process": render_masterclass()
        elif tab == "tools": render_tools()
        elif tab == "leaderboard":
            from ui.views.leaderboard import render_leaderboard
            render_leaderboard()
        elif tab == "notes": render_notes(st.session_state.user_id)
        elif tab == "profile": render_profile(st.session_state.user_id)
        elif tab == "glossary": render_glossary(st.session_state.user_id)
        elif tab == "admin": render_admin_dashboard()

        render_mentor_footer()

if __name__ == "__main__":
    main()