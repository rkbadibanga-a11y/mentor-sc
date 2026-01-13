# ui/views/auth.py
import streamlit as st
import uuid
import time
from core.database import run_query
from core.config import t, SIGNATURE

def render_login():
    login_placeholder = st.empty()
    lang = st.session_state.get('lang', 'Français')
    
    with login_placeholder.container():
        st.title("📦 Mentor SC")
        st.caption(t('welcome', lang))
        
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("📧 Email", placeholder="exemple@supply.com")
            submit_login = st.form_submit_button(t('login_btn', lang), type="primary", use_container_width=True)
            
            if submit_login:
                if not email or "@" not in email:
                    st.warning("Veuillez entrer une adresse email valide.")
                else:
                    res = run_query('SELECT * FROM users WHERE email=?', (email,), fetch_one=True)
                    if res:
                        user_id = res[0]
                        # Restaurer les données depuis le Cloud pour être sûr d'avoir l'historique
                        from core.database import pull_user_data_from_supabase
                        pull_user_data_from_supabase(user_id)
                        
                        # Re-fetch local après le pull
                        res = run_query('SELECT * FROM users WHERE user_id=?', (user_id,), fetch_one=True)
                        
                        st.query_params["uid"] = user_id # Sauvegarder dans l'URL
                        
                        # --- MODERNE : COOKIE ---
                        import extra_streamlit_components as stx
                        cm = stx.CookieManager()
                        cm.set('mentor_sc_uid', user_id, expires_at=None) # Expire dans 30 jours par défaut
                        
                        st.session_state.update({
                            'auth':True, 'user_id':user_id, 'user':res[1], 'user_email': email, 'user_city': res[10],
                            'level':int(res[2] or 1), 'xp':int(res[3] or 0), 'total_score':int(res[4] or 0),
                            'mastery':int(res[5] or 0), 'q_count':int(res[6] or 0), 'hearts':int(res[7] or 5),
                            'xp_checkpoint':int(res[12] or 0), 'crisis_wins': int(res[13] or 0),
                            'redemptions': int(res[14] or 0), 'has_diploma': bool(res[15] or 0),
                            'current_run_xp': int(res[16] or 0),
                            'joker_5050': int(res[17] if len(res)>17 else 0), 
                            'joker_hint': int(res[18] if len(res)>18 else 0),
                            'data': None, 'question_queue': [], 'consecutive_wins': 0,
                            'active_tab': 'mission' # Force l'onglet Mission par défaut
                        })
                        st.toast(f"Ravi de vous revoir, {res[1]} !")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.session_state.temp_email = email
                        st.session_state.show_reg = True
                        st.rerun()

        # --- NOUVEAU : LIEN MAGIQUE ---
        with st.expander("🔗 J'ai déjà un compte mais je n'ai pas mon lien"):
            email_magic = st.text_input("📧 Votre email de compte", key="magic_email")
            if st.button("M'envoyer mon lien magique", use_container_width=True):
                res = run_query('SELECT user_id, name FROM users WHERE email=?', (email_magic,), fetch_one=True)
                if res:
                    from services.email_service import send_email_notification
                    magic_link = f"https://mentor-sc.streamlit.app/?uid={res[0]}"
                    subject = "📦 Votre Lien Magique Mentor SC"
                    body = f"Bonjour {res[1]},\n\nVoici votre accès direct à Mentor SC :\n{magic_link}\n\nEnregistrez ce lien dans vos favoris pour ne plus jamais perdre votre progression !"
                    
                    success, _ = send_email_notification(subject, body)
                    if success: st.success("Lien envoyé ! Vérifiez votre boîte mail.")
                    else: st.error("Erreur d'envoi. Contactez mentor.sc.app@gmail.com")
                else:
                    st.error("Aucun compte trouvé avec cet email.")
        
        if st.session_state.get('show_reg'):
            with st.form("reg"):
                st.subheader("🆕 Créer votre profil")
                name = st.text_input("Prénom")
                city = st.text_input("Ville")
                if st.form_submit_button(t('validate', lang)):
                    if name and city:
                        uid = str(uuid.uuid4())
                        # Initialisation : 3 Vies, 3 Jokers 50/50, 3 Jokers Indices
                        run_query('INSERT INTO users (user_id, name, email, city, hearts, joker_5050, joker_hint) VALUES (?,?,?,?,3,3,3)', 
                                 (uid, name, st.session_state.temp_email, city), commit=True)
                        st.session_state.update({'auth':True, 'user_id':uid, 'user':name, 'user_email':st.session_state.temp_email, 'user_city': city, 'hearts': 3, 'joker_5050': 3, 'joker_hint': 3})
                        login_placeholder.empty()
                        st.rerun()
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(SIGNATURE, unsafe_allow_html=True)
        
        