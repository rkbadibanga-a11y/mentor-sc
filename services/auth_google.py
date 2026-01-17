# services/auth_google.py
import os
import streamlit as st
import time
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.oauth2 import id_token
from core.database import run_query, pull_user_data_from_supabase

# Config
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = "https://mentorsc.streamlit.app/"

def get_google_auth_url():
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [REDIRECT_URI],
            }
        },
        scopes=["openid", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile"],
    )
    flow.redirect_uri = REDIRECT_URI
    authorization_url, _ = flow.authorization_url(prompt='select_account')
    return authorization_url

def handle_google_callback():
    if "code" in st.query_params:
        try:
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": CLIENT_ID,
                        "client_secret": CLIENT_SECRET,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [REDIRECT_URI],
                    }
                },
                scopes=["openid", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile"],
            )
            flow.redirect_uri = REDIRECT_URI
            flow.fetch_token(code=st.query_params["code"])
            
            credentials = flow.credentials
            info = id_token.verify_oauth2_token(credentials.id_token, Request(), CLIENT_ID)
            
            email = info.get("email")
            name = info.get("given_name", info.get("name", "Expert SC"))
            
            if email:
                # Login or Register
                res = run_query('SELECT * FROM users WHERE email=?', (email,), fetch_one=True)
                if res:
                    user_id = res[0]
                    pull_user_data_from_supabase(user_id)
                    res = run_query('SELECT * FROM users WHERE user_id=?', (user_id,), fetch_one=True)
                else:
                    import uuid
                    user_id = str(uuid.uuid4())
                    run_query('INSERT INTO users (user_id, name, email, hearts, joker_5050, joker_hint) VALUES (?,?,?,3,3,3)', 
                             (user_id, name, email), commit=True)
                    res = run_query('SELECT * FROM users WHERE user_id=?', (user_id,), fetch_one=True)

                # Set Session
                st.session_state.update({
                    'auth':True, 'user_id':user_id, 'user':res[1], 'user_email': email, 'user_city': res[10] if len(res)>10 else "",
                    'level':int(res[2] or 1), 'xp':int(res[3] or 0), 'total_score':int(res[4] or 0),
                    'mastery':int(res[5] or 0), 'q_count':int(res[6] or 0), 'hearts':int(res[7] or 5),
                    'active_tab': 'mission'
                })
                
                # Persistance par URL (uid)
                st.query_params["uid"] = user_id
                
                # Clean URL code
                if "code" in st.query_params:
                    del st.query_params["code"]
                st.rerun()
        except Exception as e:
            st.error(f"Erreur d'authentification Google : {str(e)}")
            if "code" in st.query_params:
                del st.query_params["code"]
            time.sleep(2)
            st.rerun()
