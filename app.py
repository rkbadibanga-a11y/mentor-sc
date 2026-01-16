# app.py
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv
import os

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
    apply_styles()
    
    # 1. INITIALISATION CRITIQUE (Exhaustive)
    if 'auth' not in st.session_state:
        st.session_state.update({
            'auth': False, 'user': '', 'user_id': '', 'level': 1, 'xp': 0, 'hearts': 5,
            'q_count': 0, 'mastery': 0, 'total_score': 0, 'active_tab': 'mission',
            'question_queue': [], 'chat_history': [], 'data': None,
            'mentor_voice': True, 'crisis_active': False, 'answered': False
        })
        init_db()

    if 'cookie_manager' not in st.session_state:
        st.session_state.cookie_manager = stx.CookieManager(key="cookie_manager_v7")
    
    # --- CALLBACK GOOGLE ---
    if "code" in st.query_params:
        from services.auth_google import handle_google_callback
        handle_google_callback()

    # --- AUTO LOGIN ---
    if not st.session_state.auth and not st.session_state.get('cookie_checked') and not st.session_state.get('logout_in_progress'):
        all_cookies = st.session_state.cookie_manager.get_all()
        if all_cookies:
            saved_uid = all_cookies.get('mentor_sc_uid')
            if saved_uid:
                from core.database import pull_user_data_from_supabase
                pull_user_data_from_supabase(saved_uid)
                res = run_query('SELECT * FROM users WHERE user_id=?', (saved_uid,), fetch_one=True)
                if res:
                    st.session_state.update({
                        'auth':True, 'user_id':res[0], 'user':res[1], 'user_email': res[9], 'user_city': res[10],
                        'level':int(res[2] or 1), 'xp':int(res[3] or 0), 'total_score':int(res[4] or 0),
                        'mastery':int(res[5] or 0), 'q_count':int(res[6] or 0), 'hearts':int(res[7] or 3),
                        'active_tab': 'mission', 'cookie_checked': True
                    })
                    st.rerun()
            st.session_state.cookie_checked = True

    if not st.session_state.auth:
        render_login()
    else:
        with st.sidebar:
            render_sidebar()

        trigger_queued_sounds()
        
        menu = {
            "mission": "🎯 Mission", "coach": "🧠 Audit", "process": "📚 MasterClass", 
            "tools": "🛠️ Outils", "glossary": "📖 Glossaire", "notes": "📝 Notes", 
            "profile": "📊 Profil", "leaderboard": "🏆 Top"
        }
        if st.session_state.get('user_email') in os.getenv("ADMIN_EMAILS", ["r.k.badibanga@gmail.com"]):
            menu["admin"] = "👮 Admin"

        selected = st.pills("Nav", options=list(menu.keys()), format_func=lambda x: menu[x], 
                           default=st.session_state.active_tab, label_visibility="collapsed", key="nav_pills_final")
        
        if selected and selected != st.session_state.active_tab:
            st.session_state.active_tab = selected
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        tab = st.session_state.active_tab
        uid = st.session_state.user_id
        
        if tab == "mission": render_mission()
        elif tab == "coach": render_coach()
        elif tab == "process": render_masterclass()
        elif tab == "tools": render_tools()
        elif tab == "leaderboard":
            from ui.views.leaderboard import render_leaderboard
            render_leaderboard()
        elif tab == "notes": render_notes(uid)
        elif tab == "profile": render_profile(uid)
        elif tab == "glossary": render_glossary(uid)
        elif tab == "admin": render_admin_dashboard()

        render_mentor_footer()

if __name__ == "__main__":
    main()