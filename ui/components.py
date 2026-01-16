# ui/components.py
import streamlit as st
import json
import time
import urllib.parse
from streamlit_lottie import st_lottie
from core.config import MENTOR_AVATARS, COLORS, LOTTIE_URLS, t, SIGNATURE
from core.database import get_leaderboard, run_query

def render_mentor_footer():
    msg = st.session_state.get('mentor_message')
    is_crisis = st.session_state.get('crisis_active')
    
    if not msg and not is_crisis: # Si pas de message et pas de crise, on n'affiche RIEN
        return

    # Message par défaut en cas de crise si pas de message IA
    if is_crisis and not msg:
        msg = "ALERTE CRISE ! Réponds vite ou perds 2 stocks !"

    mentor_state = "neutral"
    if is_crisis: mentor_state = "crisis"
    elif st.session_state.get('mentor_working'): mentor_state = "working"
    elif st.session_state.get('last_result') == "WIN": mentor_state = "happy"
    elif st.session_state.get('last_result') == "LOSS": mentor_state = "sad"
    
    emojis = {"happy": "🤩", "sad": "😤", "neutral": "🤖", "working": "🤔", "crisis": "🚨"}
    avatar = emojis.get(mentor_state, "🤖")

    # CSS dynamique pour la crise
    crisis_style = "animation: pulse-red 1s infinite;" if is_crisis else ""
    
    st.markdown(f"""
        <style>
        @keyframes pulse-red {{
            0% {{ box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); background: rgba(239, 68, 68, 0.2); }}
            70% {{ box-shadow: 0 0 0 15px rgba(239, 68, 68, 0); background: rgba(239, 68, 68, 0.4); }}
            100% {{ box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); background: rgba(239, 68, 68, 0.2); }}
        }}
        </style>
        <div class="mentor-footer" style="{crisis_style}">
            <div class="mentor-avatar">{avatar}</div>
            <div class="mentor-bubble"><b>Mentor SC :</b> {msg}</div>
        </div>
    """, unsafe_allow_html=True)

    if st.session_state.get('mentor_voice') and msg != st.session_state.get('last_spoken_msg'):
        st.session_state.last_spoken_msg = msg
        st.components.v1.html(f"<script>window.speechSynthesis.cancel(); const u=new SpeechSynthesisUtterance({json.dumps(msg)}); u.lang='fr-FR'; window.speechSynthesis.speak(u);</script>", height=0)

@st.dialog("Signaler une anomalie")
def report_anomaly_dialog():
    st.markdown("##### 🛠️ Rapport d'incident")
    st.write("Dites-nous ce qui ne va pas. Votre message sera envoyé directement à Romain.")
    
    # Nouveau champ Email
    user_email_input = st.text_input("Votre adresse email (pour vous répondre) :", value=st.session_state.get('user_email', ''))
    
    user_message = st.text_area("Précisions sur l'anomalie :", placeholder="Décrivez le problème ici...", height=150)
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    if col1.button("💾 Enregistrer localement", use_container_width=True):
        if user_message:
            from utils.maintenance import record_anomaly
            record_anomaly(f"Signalement Manuel (Email: {user_email_input}): {user_message}", context="Interface Sidebar Dialog")
            st.toast("✅ Rapport enregistré !")
        else:
            st.warning("Veuillez décrire l'anomalie.")

    if col2.button("📧 Envoyer Directement", type="primary", use_container_width=True):
        if user_message and user_email_input:
            with st.spinner("Envoi en cours..."):
                from services.email_service import send_email_notification
                subject = f"🚨 Signalement Mentor SC - {st.session_state.user}"
                body = f"""Bonjour Romain,

Un utilisateur a signalé une anomalie.

CONTACT :
- Pseudo : {st.session_state.user}
- Email saisi : {user_email_input}
- Email profil : {st.session_state.get('user_email', 'N/A')}

MESSAGE :
{user_message}

INFOS TECHNIQUES :
- Niveau : {st.session_state.level}
- XP : {st.session_state.xp}
- Onglet actif : {st.session_state.get('active_tab', 'unknown')}
"""
                success, status_msg = send_email_notification(subject, body)
                if send_email_notification(subject, body):
                    # On enregistre aussi techniquement en DB
                    run_query('INSERT INTO user_feedback (user_id, user_name, user_email, message, context) VALUES (?, ?, ?, ?, ?)', 
                             (st.session_state.user_id, st.session_state.user, user_email_input, user_message, "Sidebar Dialog"), commit=True)
                    
                    from utils.maintenance import record_anomaly
                    record_anomaly(f"Signalement Direct (Email: {user_email_input}): {user_message}", context="Sidebar Dialog")
                    st.success("✅ Message envoyé directement à Romain !")
                else:
                    st.error(f"❌ Échec de l'envoi : {status_msg}")
        elif not user_email_input:
            st.warning("Veuillez renseigner votre email pour qu'on puisse vous répondre.")
        else:
            st.warning("Veuillez décrire l'anomalie.")

def render_sidebar():
    lang = st.session_state.get('lang', 'Français')
    
    # --- CHECK CLOUD STATUS ---
    from core.database import DatabaseManager
    sb = DatabaseManager.get_supabase()
    cloud_status = "🟢 Connecté" if sb else "🔴 Déconnecté"
    cloud_color = "#10b981" if sb else "#ef4444"

    # 1. Engine Display
    engine_display = st.session_state.get('current_engine', 'Auto')
        
    # Logique de couleur et texte
    if engine_display in ["Groq", "Gemini", "Mistral", "Base de données", "Buffer RAM ⚡"]:
        status_color = "#10b981" # Vert : IA ou Base Active
        status_text = engine_display
    elif "Secours" in engine_display:
        status_color = "#f59e0b" # Orange : Mode dégradé
        status_text = "Mode Secours"
    elif "Connexion" in engine_display or engine_display == "Auto":
        status_color = "#94a3b8" # Gris : En cours
        status_text = "Recherche..."
    else:
        status_color = "#ef4444" # Rouge : Offline
        status_text = "Déconnecté"
    
    st.markdown(f'''
        <div style="text-align:center;">
            <h1 style="color: #00dfd8; margin-bottom: 0px; font-weight: 800; font-size: 2.2rem;">📦 Mentor SC</h1>
            <div style="font-size: 1rem; font-weight: 500; color: #f1f5f9; margin-bottom: 15px; opacity: 0.8;">👤 {st.session_state.user}</div>
            <div style="background:rgba(30, 41, 59, 0.5); padding:8px; border-radius:12px; margin-top:5px; border:1px solid #334155; display: flex; align-items: center; justify-content: center; gap: 15px;">
                <div style="text-align: left; border-right: 1px solid #334155; padding-right: 10px;">
                    <div style="font-size:0.6rem; color:#64748b; font-weight: bold; letter-spacing: 1px;">STATUT IA</div>
                    <div style="font-size:0.75rem; font-family:monospace; color:{status_color}; font-weight: bold;">{status_text}</div>
                </div>
                <div style="text-align: left;">
                    <div style="font-size:0.6rem; color:#64748b; font-weight: bold; letter-spacing: 1px;">CLOUD SYNC</div>
                    <div style="font-size:0.75rem; font-family:monospace; color:{cloud_color}; font-weight: bold;">{cloud_status}</div>
                </div>
            </div>
        </div>
    ''', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 2. Stats
    col1, col2 = st.columns([0.3, 0.7])
    col1.markdown(f"<div style='border:1px solid #334155; border-radius:8px; padding:5px; text-align:center'>Niv<br><b>{st.session_state.level}</b></div>", unsafe_allow_html=True)
    col2.progress(st.session_state.mastery/100, t('mastery', lang))
    
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1: st.markdown(f"<div style='text-align:center; background:rgba(239, 68, 68, 0.1); border-radius:8px; padding:8px;'>❤️ {t('lives', lang)}<br><b>{st.session_state.hearts}</b></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div style='text-align:center; background:rgba(16, 185, 129, 0.1); border-radius:8px; padding:8px;'>💰 XP<br><b>{st.session_state.xp}</b></div>", unsafe_allow_html=True)
    
    st.markdown(f"<div style='text-align:center; margin-top:10px; color:#94a3b8; font-size:0.9rem;'>🏆 Score Prestige : <b>{st.session_state.total_score}</b></div>", unsafe_allow_html=True)
    st.markdown("---")
    
    # 3. Challenge Vie (Skill Based)
    if st.session_state.hearts < 3:
        streak = st.session_state.consecutive_wins
        st.markdown(f"""
            <div style='text-align:center; padding:10px; background:rgba(239, 68, 68, 0.1); border-radius:8px; border:1px dashed #ef4444;'>
                <div style='font-size:0.8rem; color:#ef4444; font-weight:bold;'>💔 Stock Critique</div>
                <div style='margin-top:5px; font-size:0.75rem;'>Réussis {5-streak} questions de suite pour récupérer 1 ❤️</div>
                <div style='background:#334155; height:6px; border-radius:3px; margin-top:5px; overflow:hidden;'>
                    <div style='background:#ef4444; width:{streak*20}%; height:100%;'></div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    # 4. Referral
    u = f"https://mentor-sc.streamlit.app/?ref={st.session_state.get('user_email', '')}"
    enc = urllib.parse.quote(f"Rejoins Mentor SC : {u}")
    st.markdown(f'<a href="mailto:?body={enc}" target="_blank" style="text-decoration:none;"><div style="border: 1px solid #00dfd8; color: #00dfd8; background: rgba(0, 223, 216, 0.05); padding: 12px; border-radius: 12px; text-align: center; font-size: 0.85rem; font-weight: 600; margin-top: 10px;">🤝 Inviter un collègue (+50 XP)</div></a>', unsafe_allow_html=True)

    # 5. Leaderboard (Top 5)
    with st.expander("🏆 Top 5 Experts"):
        leaders = get_leaderboard()[:5] # Sécurité Top 5
        for i, (n, s, l) in enumerate(leaders):
            st.caption(f"{('🥇' if i==0 else '🥈' if i==1 else '🥉' if i==2 else '•')} {n} ({s} pts)")
        st.markdown("<small><i>Voir le classement complet dans l'onglet dédié.</i></small>", unsafe_allow_html=True)

    st.markdown("---")    
    # 6. Settings
    with st.expander(t('settings', lang)):
        st.selectbox(t('language', lang), ["Français", "English", "Español"], key='lang')
        st.toggle("🔊 Voix du Mentor", key="mentor_voice")
        
        st.markdown(f"##### ✏️ {t('my_profile', lang)}")
        new_name = st.text_input("Pseudo", value=st.session_state.user)
        new_email = st.text_input("Email", value=st.session_state.get('user_email', ''))
        new_city = st.text_input("Ville", value=st.session_state.get('user_city', ''))
        
        if st.button(t('validate', lang), use_container_width=True):
            if new_name and new_email:
                run_query("UPDATE users SET name=?, email=?, city=? WHERE user_id=?", (new_name, new_email, new_city, st.session_state.user_id), commit=True)
                st.session_state.user = new_name
                st.session_state.user_email = new_email
                st.session_state.user_city = new_city
                st.success("Profil mis à jour !")
                time.sleep(1)
                st.rerun()

        st.markdown("---")
        if st.button(t('logout', lang), use_container_width=True):
            cm = st.session_state.get('cookie_manager')
            if cm: cm.delete('mentor_sc_uid')
            st.session_state.clear()
            st.query_params.clear() # Nettoyer l'URL
            st.rerun()            
        
        st.markdown("---")
        st.markdown("##### 🛠️ Maintenance")
        if st.button("🚨 Signaler une anomalie", use_container_width=True):
            report_anomaly_dialog()


        if st.button(t('purge', lang), type="primary", use_container_width=True):
            cm = st.session_state.get('cookie_manager')
            if cm: cm.delete('mentor_sc_uid')
            run_query("DELETE FROM users WHERE user_id=?", (st.session_state.user_id,), commit=True)
            st.session_state.clear()
            st.rerun()
    
    st.markdown(SIGNATURE, unsafe_allow_html=True)