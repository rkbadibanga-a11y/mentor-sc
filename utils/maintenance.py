# utils/maintenance.py
import json
import os
import traceback
import datetime
import streamlit as st
import sys
import time

REPORT_FILE = "GEMINI_FIX_REQUEST.json"

def record_anomaly(error, context="Crash Global"):
    """Enregistre les détails techniques d'une anomalie pour Gemini."""
    report = {
        "timestamp": str(datetime.datetime.now()),
        "error_message": str(error),
        "traceback": traceback.format_exc(),
        "active_tab": st.session_state.get('active_tab', 'unknown'),
        "env": {
            "python_version": sys.version,
            "streamlit_version": st.__version__,
            "cwd": os.getcwd()
        },
        "user_context": {
            "user": st.session_state.get('user', 'anonymous'),
            "level": st.session_state.get('level', 0),
            "xp": st.session_state.get('xp', 0),
            "hearts": st.session_state.get('hearts', 0)
        },
        "location": context
    }
    
    try:
        with open(REPORT_FILE, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=4, ensure_ascii=False)
        return True
    except:
        return False

def auto_repair_session():
    """Tente de restaurer les variables manquantes sans intervention humaine."""
    defaults = {
        'auth': False, 'user': '', 'level': 1, 'xp': 0, 'hearts': 5,
        'q_count': 0, 'mastery': 0, 'total_score': 0, 'active_tab': 'mission',
        'question_queue': [], 'chat_history': [], 'data': None,
        'mentor_message': '', 'last_result': None, 'mentor_voice': True,
        'crisis_active': False, 'consecutive_wins': 0,
        'redemption_mode': False, 'redemption_count': 0
    }
    repaired = False
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
            repaired = True
    return repaired

def render_error_screen(error):
    """Affiche un écran d'erreur élégant avec bouton de réparation."""
    # Attempt auto-repair first
    if auto_repair_session():
        st.success("🛠️ Session auto-réparée. Redémarrage...")
        time.sleep(1)
        st.rerun()

    st.markdown(f"""
        <div style="background: rgba(239, 68, 68, 0.1); border: 2px solid #ef4444; padding: 30px; border-radius: 15px; text-align: center;">
            <h1 style="font-size: 4rem; margin: 0;">🚧</h1>
            <h2 style="color: #ef4444;">Oups ! Un goulot d'étranglement imprévu.</h2>
            <p style="color: #f1f5f9;">Une erreur technique est survenue dans l'application.</p>
            <code style="background: #000; padding: 5px 10px; border-radius: 5px; color: #ff9e9e;">{str(error)}</code>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("🔧 GÉNÉRER UN TICKET DE RÉPARATION POUR GEMINI", type="primary", use_container_width=True):
        file = record_anomaly(error)
        st.success(f"✅ Rapport généré ({file}).")
        st.info("💡 Échangez avec votre Agent Gemini et dites-lui simplement : **'Répare l'application'**.")
    
    if st.button("🔄 Tenter de rafraîchir", use_container_width=True):
        st.components.v1.html("<script>window.parent.location.reload();</script>", height=0)
