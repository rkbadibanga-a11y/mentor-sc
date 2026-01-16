# core/database.py
import sqlite3
import os
import json
import streamlit as st
import threading
from pathlib import Path
from contextlib import contextmanager
from core.config import DB_FILE, ROOT_DIR
from supabase import create_client, Client

@st.cache_resource
def get_supabase_client():
    """Initialise et met en cache le client Supabase."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        return None
    try:
        return create_client(url, key)
    except Exception as e:
        print(f"Supabase Init Error: {e}")
        return None

class DatabaseManager:
    @staticmethod
    def get_supabase() -> Client:
        return get_supabase_client()

    @classmethod
    @contextmanager
    def session(cls):
        """Context manager pour assurer le commit/rollback automatique."""
        conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

def run_query(query: str, params: tuple = (), fetch_one=False, fetch_all=False, commit=True):
    """Exécute une requête SQL localement."""
    result = None
    with DatabaseManager.session() as cursor:
        cursor.execute(query, params)
        if fetch_one:
            result = cursor.fetchone()
        elif fetch_all:
            result = cursor.fetchall()
        else:
            result = True

    # Synchronisation Cloud en arrière-plan
    if commit:
        q_upper = query.upper()
        uid = st.session_state.get('user_id') or (params[0] if params else None)
        if uid and ("UPDATE USERS" in q_upper or "INSERT INTO HISTORY" in q_upper or "STATS" in q_upper):
            threading.Thread(target=sync_user_to_supabase, args=(uid,), daemon=True).start()
            
    return result

def sync_table_to_supabase(table, user_id, data):
    """Synchronise une ligne spécifique vers une table Supabase."""
    sb = DatabaseManager.get_supabase()
    if not sb: return
    try:
        sb.table(table).upsert(data).execute()
    except Exception as e:
        print(f"Supabase Sync Error ({table}): {e}")

def pull_user_data_from_supabase(user_id):
    """Récupère toutes les données d'un utilisateur depuis Supabase et les injecte en local."""
    sb = DatabaseManager.get_supabase()
    if not sb: return False
    
    try:
        # 1. Table USERS
        res = sb.table("users").select("*").eq("user_id", user_id).execute()
        if res.data:
            u = res.data[0]
            run_query("""
                INSERT OR REPLACE INTO users 
                (user_id, name, level, xp, total_score, mastery, q_count, hearts, email, city, crisis_wins, has_diploma, joker_5050, joker_hint)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                u['user_id'], u['name'], u.get('level', 1), u.get('xp', 0), 
                u.get('total_score', 0), u.get('mastery', 0), u.get('q_count', 0), 
                u.get('hearts', 5), u.get('email'), u.get('city', ''), u.get('crisis_wins', 0),
                u.get('has_diploma', 0), u.get('joker_5050', 3), u.get('joker_hint', 3)
            ), commit=False)

        # 2. Table HISTORY
        res = sb.table("history").select("*").eq("user_id", user_id).execute()
        for h in res.data:
            run_query("INSERT OR IGNORE INTO history (user_id, question_hash) VALUES (?, ?)", 
                     (h['user_id'], h['question_hash']), commit=False)

        # 3. Table STATS
        res = sb.table("stats").select("*").eq("user_id", user_id).execute()
        for s in res.data:
            run_query("INSERT OR REPLACE INTO stats (user_id, category, correct_count) VALUES (?, ?, ?)", 
                     (s['user_id'], s['category'], s['correct_count']), commit=False)

        return True
    except Exception as e:
        print(f"Supabase Pull Error: {e}")
        return False

def sync_user_to_supabase(user_id):
    """Envoie une copie complète des données utilisateur vers Supabase."""
    sb = DatabaseManager.get_supabase()
    if not sb: return
    
    with DatabaseManager.session() as cursor:
        cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        local_data = cursor.fetchone()
    
    if not local_data: return
    
    data = {
        "user_id": str(local_data[0]), "name": str(local_data[1]), 
        "level": int(local_data[2] or 1), "xp": int(local_data[3] or 0), 
        "total_score": int(local_data[4] or 0), "mastery": int(local_data[5] or 0),
        "q_count": int(local_data[6] or 0), "hearts": int(local_data[7] or 5), 
        "email": str(local_data[9] or ""), "city": str(local_data[10] or ""), 
        "crisis_wins": int(local_data[13] or 0), "has_diploma": int(local_data[15] or 0),
        "joker_5050": int(local_data[17] if len(local_data)>17 else 3),
        "joker_hint": int(local_data[18] if len(local_data)>18 else 3),
        "last_seen": str(local_data[8] or "")
    }
    
    try:
        sb.table("users").upsert(data).execute()
    except Exception as e:
        print(f"Supabase Sync Error: {e}")

@st.cache_resource
def init_db():
    """Initialise les tables locales une seule fois."""
    queries = [
        'CREATE TABLE IF NOT EXISTS users (user_id TEXT PRIMARY KEY, name TEXT, level INTEGER DEFAULT 1, xp INTEGER DEFAULT 0, total_score INTEGER DEFAULT 0, mastery INTEGER DEFAULT 0, q_count INTEGER DEFAULT 0, hearts INTEGER DEFAULT 5, last_seen TEXT, email TEXT UNIQUE, city TEXT, referred_by TEXT, xp_checkpoint INTEGER DEFAULT 0, crisis_wins INTEGER DEFAULT 0, redemptions INTEGER DEFAULT 0, has_diploma INTEGER DEFAULT 0, current_run_xp INTEGER DEFAULT 0, joker_5050 INTEGER DEFAULT 3, joker_hint INTEGER DEFAULT 3)',
        'CREATE TABLE IF NOT EXISTS history (user_id TEXT, question_hash TEXT, UNIQUE(user_id, question_hash))',
        'CREATE TABLE IF NOT EXISTS glossary (user_id TEXT, term TEXT, definition TEXT, category TEXT, use_case TEXT, business_impact TEXT, short_definition TEXT, UNIQUE(user_id, term))',
        'CREATE TABLE IF NOT EXISTS stats (user_id TEXT, category TEXT, correct_count INTEGER, UNIQUE(user_id, category))',
        'CREATE TABLE IF NOT EXISTS notes (user_id TEXT, note_id TEXT PRIMARY KEY, title TEXT, content TEXT, timestamp TEXT)',
        'CREATE TABLE IF NOT EXISTS ai_queue (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, question_json TEXT, category TEXT)',
        'CREATE TABLE IF NOT EXISTS question_bank (id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT, concept TEXT, level INTEGER, question TEXT, options TEXT, correct TEXT, explanation TEXT, theory TEXT, example TEXT, tip TEXT, triad_id TEXT, triad_position INTEGER DEFAULT 0)',
        'CREATE TABLE IF NOT EXISTS recent_failures (user_id TEXT, question_id INTEGER, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(user_id, question_id))',
        'CREATE TABLE IF NOT EXISTS user_feedback (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, user_name TEXT, user_email TEXT, message TEXT, context TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)'
    ]
    with DatabaseManager.session() as cursor:
        for q in queries:
            cursor.execute(q)
    
    # Peuplement initial si nécessaire
    seed_questions()
    return True

def seed_questions():
    """Importe les questions depuis le fichier JSON."""
    seed_file = Path(ROOT_DIR) / "questions_seed.json"
    if not seed_file.exists(): return
    
    with DatabaseManager.session() as cursor:
        cursor.execute("SELECT COUNT(*) FROM question_bank")
        if cursor.fetchone()[0] == 0:
            try:
                with open(seed_file, "r", encoding="utf-8") as f:
                    questions = json.load(f)
                    for q in questions:
                        cursor.execute("""
                            INSERT INTO question_bank 
                            (category, concept, level, question, options, correct, explanation, triad_id, triad_position) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            q.get('category'), q.get('concept'), q.get('level'), 
                            q.get('question'), json.dumps(q.get('options')), q.get('correct'), 
                            q.get('explanation'), q.get('triad_id'), q.get('triad_position')
                        ))
            except Exception as e:
                print(f"Seed Error: {e}")

@st.cache_data(ttl=600)
def get_leaderboard_local():
    """Récupère le classement local mis en cache."""
    return run_query('SELECT name, total_score, level FROM users ORDER BY level DESC, total_score DESC LIMIT 10', fetch_all=True)

def sync_leaderboard_from_supabase(limit=100):
    """Synchronise les meilleurs utilisateurs."""
    try:
        sb = DatabaseManager.get_supabase()
        if not sb: return False
        res = sb.table("users").select("user_id, name, level, total_score, city, last_seen").order("level", desc=True).order("total_score", desc=True).limit(limit).execute()
        if res.data:
            with DatabaseManager.session() as cursor:
                for u in res.data:
                    cursor.execute("""
                        INSERT OR REPLACE INTO users (user_id, name, level, total_score, city, last_seen)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (u['user_id'], u['name'], u.get('level', 1), u.get('total_score', 0), u.get('city', ''), u.get('last_seen')))
            st.cache_data.clear() # Invalider le cache après synchro
            return True
    except: pass
    return False

def get_leaderboard(sync=False):
    """Récupère le leaderboard. Synchro Cloud optionnelle."""
    if sync:
        sync_leaderboard_from_supabase(limit=10)
    return get_leaderboard_local()