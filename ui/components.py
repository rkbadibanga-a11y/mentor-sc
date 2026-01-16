# ui/components.py
import streamlit as st
import json
import urllib.parse
from core.config import MENTOR_AVATARS, COLORS, LOTTIE_URLS, t, SIGNATURE
from core.database import get_leaderboard, run_query, DatabaseManager

def render_mentor_footer():
    msg = st.session_state.get('mentor_message')
    if not msg and not st.session_state.get('crisis_active'): return

    mentor_state = "neutral"
    if st.session_state.get('crisis_active'): mentor_state = "crisis"
    elif st.session_state.get('last_result') == "WIN": mentor_state = "happy"
    elif st.session_state.get('last_result') == "LOSS": mentor_state = "sad"
    
    emojis = {"happy": "🤩", "sad": "😤", "neutral": "🤖", "crisis": "🚨"}
    avatar = emojis.get(mentor_state, "🤖")
    
    st.markdown(f"""
        <div class="mentor-footer">
            <div class="mentor-avatar">{avatar}</div>
            <div class="mentor-bubble"><b>Mentor SC :</b> {msg or 'ALERTE CRISE !'}</div>
        </div>
    """, unsafe_allow_html=True)

    if st.session_state.get('mentor_voice') and msg != st.session_state.get('last_spoken_msg'):
        st.session_state.last_spoken_msg = msg
        st.components.v1.html(f"<script>window.speechSynthesis.cancel(); const u=new SpeechSynthesisUtterance({json.dumps(msg)}); u.lang='fr-FR'; window.speechSynthesis.speak(u);</script>", height=0)

def render_sidebar():
    lang = st.session_state.get('lang', 'Français')
    
    # --- CHECK CLOUD STATUS (CACHED) ---
    @st.cache_data(ttl=60)
    def check_sb():
        try: return "Connecté" if DatabaseManager.get_supabase() else "Déconnecté"
        except: return "Déconnecté"
    
    status = check_sb()
    cloud_color = "#10b981" if status == "Connecté" else "#ef4444"

    st.markdown(f'''
        <div style="text-align:center;">
            <a href="/" target="_self" style="text-decoration: none;"><h1 style="color: #00dfd8; margin-bottom: 0px; font-weight: 800;">📦 Mentor SC</h1></a>
            <div style="font-size: 1rem; color: #f1f5f9; margin-bottom: 15px; opacity: 0.8;">👤 {st.session_state.user}</div>
            <div style="background:rgba(30, 41, 59, 0.5); padding:8px; border-radius:12px; display: flex; align-items: center; justify-content: center; gap: 10px;">
                <div style="font-size:0.6rem; color:{cloud_color}; font-weight: bold; letter-spacing: 1px;">CLOUD: {status}</div>
            </div>
        </div>
    ''', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    # --- STATS VISUELLES (RESTAURATION) ---
    hearts = st.session_state.get('hearts', 5)
    # Affichage des vies sous forme de cœurs
    hearts_html = "❤️" * hearts + "🖤" * (5 - hearts)
    
    st.markdown(f"""
        <div style="background: rgba(15, 23, 42, 0.6); padding: 15px; border-radius: 10px; border: 1px solid #334155; margin-bottom: 10px;">
            <div style="font-size: 0.8rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;">Stock de Sécurité (Vies)</div>
            <div style="font-size: 1.5rem; letter-spacing: 2px;">{hearts_html}</div>
        </div>
    """, unsafe_allow_html=True)

    # BOUTON SOIN RAPIDE (SIDEBAR)
    if hearts < 5 and st.session_state.get('xp', 0) >= 50:
        if st.button("💊 Soin (+1) - 50 XP", use_container_width=True):
            st.session_state.hearts += 1
            st.session_state.xp -= 50
            run_query('UPDATE users SET hearts=?, xp=? WHERE user_id=?', (st.session_state.hearts, st.session_state.xp, st.session_state.user_id), commit=True)
            st.rerun()

    c1, c2 = st.columns(2)
    c1.metric("🎖️ Niveau", st.session_state.level)
    c2.metric("✨ XP", st.session_state.xp)
    
    st.caption(f"Maîtrise : {st.session_state.get('mastery', 0)}%")
    st.progress(st.session_state.get('mastery', 0)/100)
    
    # Leaderboard (Local only for speed)
    with st.expander("🏆 Top 5 Experts"):
        for i, (n, s, l) in enumerate(get_leaderboard(sync=False)[:5]):
            st.caption(f"{n} ({s} pts)")

    st.markdown("---")    
    with st.expander("⚙️ Paramètres"):
        st.components.v1.html("""
            <div id="google_translate_element"></div>
            <script type="text/javascript">
                function googleTranslateElementInit() {
                    new google.translate.TranslateElement({pageLanguage: 'fr', includedLanguages: 'en,es,fr', layout: google.translate.TranslateElement.InlineLayout.SIMPLE}, 'google_translate_element');
                }
            </script>
            <script type="text/javascript" src="//translate.google.com/translate_a/element.js?cb=googleTranslateElementInit"></script>
        """, height=40)
        st.selectbox("🌐 Langue (Système)", ["Français", "English", "Español"], key='lang')
        st.toggle("🔊 Voix", key="mentor_voice")
        
        if st.button("🚪 Déconnexion", use_container_width=True):
            st.session_state.clear()
            st.query_params.clear()
            st.rerun()
    
    st.markdown(SIGNATURE, unsafe_allow_html=True)
