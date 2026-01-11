import streamlit as st
from core.masterclass_content import MASTERCLASS_DATA

def render_masterclass():
    st.markdown("### 📚 Master Class Supply Chain")
    st.markdown("Le manuel de référence du Directeur. Contenu statique pour consultation rapide.")
    
    # Navigation par Session
    session_names = list(MASTERCLASS_DATA.keys())
    # On utilise des tabs pour les sessions principales
    tabs = st.tabs([MASTERCLASS_DATA[s]["title"] for s in session_names])
    
    for i, session_key in enumerate(session_names):
        with tabs[i]:
            data = MASTERCLASS_DATA[session_key]
            
            # Sous-navigation (Modules)
            for module_title, content in data["modules"].items():
                with st.expander(f"📘 {module_title}", expanded=True):
                    st.markdown(content)