# ui/views/coach.py
import streamlit as st
import uuid
import datetime
import time
import json
from services.ai_engine import get_ai_service
from services.news_service import get_supply_chain_news
from core.database import run_query
from core.config import SYSTEM_PROMPT

def render_coach():
    uid = st.session_state.user_id
    ai_service = get_ai_service()
    
    st.markdown("### 💬 Bureau du Mentor SC")
    
    # 1. ZONE D'ANALYSE DOCUMENTAIRE (PRO)
    with st.expander("📂 Analyser un document professionnel (PDF, CSV, TXT)", expanded=False):
        uploaded_file = st.file_uploader("Glissez votre rapport ici", type=['pdf', 'csv', 'txt'])
        doc_context = ""
        if uploaded_file:
            from services.news_service import process_uploaded_file
            doc_context = process_uploaded_file(uploaded_file)
            if doc_context:
                st.success(f"✅ Document '{uploaded_file.name}' analysé avec succès.")

    # 2. CONFIGURATION COACHING
    c1, c2 = st.columns([0.7, 0.3])
    tone = c1.radio("Style :", ["🎩 Stratège", "🔥 Drill Sergeant", "💡 Socratique"], horizontal=True, label_visibility="collapsed")
    if c2.button("🗑️ Effacer l'historique", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

    # 3. QUICK PROMPTS (CHIPS)
    quick_prompts = ["Analyse ma progression", "Conseil carrière", "Quiz flash"]
    cols_q = st.columns(len(quick_prompts))
    selected_quick = None
    for i, q in enumerate(quick_prompts):
        if cols_q[i].button(q, key=f"btn_q_{i}", use_container_width=True):
            selected_quick = q
            st.session_state.active_tab = "coach" # Lock current tab

    # 4. CHAT INPUT (FORM AT TOP)
    with st.form("mentor_chat_form", clear_on_submit=True):
        user_input = st.text_input("Posez votre question ici...", placeholder="Ex: Comment optimiser mes stocks ?")
        submit_btn = st.form_submit_button("Envoyer au Mentor 🚀", use_container_width=True)
    
    final_prompt = selected_quick if selected_quick else (user_input if submit_btn else None)

    st.markdown("---")

    # 5. NEW INTERACTION (Typing effect on top)
    if final_prompt:
        st.session_state.chat_history.append({"role": "user", "content": final_prompt})
        
        tone_prompts = {
            "🎩 Stratège": "Tu es un stratège visionnaire. Tes réponses sont structurées, orientées long terme et ROI.",
            "🔥 Drill Sergeant": "Tu es un instructeur militaire impitoyable mais juste. Ton sec et direct.",
            "💡 Socratique": "Tu es un philosophe maïeuticien. Pose des questions pour guider la réflexion."
        }
        
        with st.chat_message("user"): st.write(final_prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Le Mentor analyse..."):
                current_persona = tone_prompts.get(tone, tone_prompts["🎩 Stratège"])
                actus = get_supply_chain_news()
                
                # Construction de la mémoire conversationnelle (5 derniers échanges)
                memory_block = ""
                recent_history = st.session_state.chat_history[-5:] if len(st.session_state.chat_history) > 5 else st.session_state.chat_history
                for msg in recent_history:
                    role_label = "MENTOR" if msg["role"] == "assistant" else "USER"
                    memory_block += f"{role_label}: {msg['content']}\n"

                full_prompt = f"""
                {SYSTEM_PROMPT}
                {current_persona}
                
                CONTEXTE :
                - User: {st.session_state.user}
                - Actualités SC: {actus}
                - Doc Analysé: {doc_context}
                
                HISTORIQUE RÉCENT :
                {memory_block}
                
                NOUVELLE QUESTION USER :
                {final_prompt}
                """
                
                response, engine_name = ai_service.get_response(full_prompt, preferred="groq")
                if not response: response = "Désolé, je suis en réunion codir. Réessaie plus tard."
                
                # Mise à jour du statut IA pour la sidebar
                st.session_state.current_engine = engine_name
                
                # Effet Machine à écrire
                resp_box = st.empty()
                displayed_text = ""
                for char in response:
                    displayed_text += char
                    resp_box.markdown(displayed_text + "▌")
                    time.sleep(0.03) # Vitesse de frappe ralentie
                resp_box.markdown(displayed_text)
                
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                time.sleep(1) 
                st.rerun()

    # 6. CHAT HISTORY DISPLAY (Reversed)
    # We use reversed list to show newest on top
    for i, msg in reversed(list(enumerate(st.session_state.chat_history))):
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if msg["role"] == "assistant":
                if st.button("💾 Sauver", key=f"save_chat_{i}"):
                    note_id = str(uuid.uuid4())
                    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    run_query('INSERT INTO notes (user_id, note_id, title, content, timestamp) VALUES (?, ?, ?, ?, ?)', 
                             (uid, note_id, f"Conseil Mentor ({now})", msg['content'], now), commit=True)
                    st.toast("✅ Sauvegardé !")