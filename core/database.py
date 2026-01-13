# core/database.py
import sqlite3
import os
import json
import streamlit as st
from pathlib import Path
from contextlib import contextmanager
from core.config import DB_FILE, ROOT_DIR
from supabase import create_client, Client

import sqlite3
import os
import json
import streamlit as st
import threading
from pathlib import Path
from contextlib import contextmanager
from core.config import DB_FILE, ROOT_DIR
from supabase import create_client, Client

class DatabaseManager:
    @staticmethod
    def get_supabase() -> Client:
        """Initialise le client Supabase pour la persistance Cloud."""
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if url and key:
            try:
                return create_client(url, key)
            except:
                return None
        return None

    @classmethod
    @contextmanager
    def session(cls):
        """Context manager pour assurer le commit/rollback automatique."""
        conn = sqlite3.connect(DB_FILE)
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
    """Exécute une requête SQL localement et synchronise avec le Cloud de manière asynchrone."""
    # 1. Exécution Locale (Vitesse Maximale)
    result = None
    with DatabaseManager.session() as cursor:
        cursor.execute(query, params)
        if fetch_one:
            result = cursor.fetchone()
        elif fetch_all:
            result = cursor.fetchall()
        else:
            result = True

    # 2. Synchronisation Cloud (VRAI Arrière-plan via Threading)
    if commit:
        q_upper = query.upper()
        uid = st.session_state.get('user_id') or (params[0] if params else None)
        if uid:
            # On lance la synchro dans un thread séparé pour ne pas bloquer l'UI
            def sync_task():
                try:
                    if "UPDATE USERS" in q_upper:
                        sync_user_to_supabase(uid)
                    elif "HISTORY" in q_upper and "INSERT" in q_upper:
                        sync_table_to_supabase("history", uid, {"user_id": uid, "question_hash": params[1] if len(params)>1 else ""})
                    elif "STATS" in q_upper and ("INSERT" in q_upper or "UPDATE" in q_upper):
                        # Récupérer la valeur à jour (interne au thread pour être sûr)
                        with DatabaseManager.session() as thread_cursor:
                            cat = params[1] if len(params)>1 else "Général"
                            thread_cursor.execute("SELECT correct_count FROM stats WHERE user_id=? AND category=?", (uid, cat))
                            st_res = thread_cursor.fetchone()
                            if st_res:
                                sync_table_to_supabase("stats", uid, {"user_id": uid, "category": cat, "correct_count": st_res[0]})
                    elif "GLOSSARY" in q_upper and ("INSERT" in q_upper or "UPDATE" in q_upper):
                        term = params[1] if "INSERT" in q_upper else (params[5] if len(params)>5 else params[0])
                        with DatabaseManager.session() as thread_cursor:
                            thread_cursor.execute("SELECT * FROM glossary WHERE user_id=? AND term=?", (uid, term))
                            g_res = thread_cursor.fetchone()
                            if g_res:
                                sync_table_to_supabase("glossary", uid, {
                                    "user_id": g_res[0], "term": g_res[1], "definition": g_res[2], 
                                    "category": g_res[3], "use_case": g_res[4], "business_impact": g_res[5], "short_definition": g_res[6]
                                })
                    elif "NOTES" in q_upper and ("INSERT" in q_upper or "UPDATE" in q_upper):
                        nid = params[1] if "INSERT" in q_upper else (params[2] if len(params)>2 else params[0])
                        with DatabaseManager.session() as thread_cursor:
                            thread_cursor.execute("SELECT * FROM notes WHERE user_id=? AND note_id=?", (uid, nid))
                            n_res = thread_cursor.fetchone()
                            if n_res:
                                sync_table_to_supabase("notes", uid, {
                                    "user_id": n_res[0], "note_id": n_res[1], "title": n_res[2], "content": n_res[3], "timestamp": n_res[4]
                                })
                except Exception as e:
                    print(f"Async Sync Error: {e}")

            threading.Thread(target=sync_task).start()
            
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
                u.get('hearts', 5), u['email'], u.get('city', ''), u.get('crisis_wins', 0),
                u.get('has_diploma', 0), u.get('joker_5050', 3), u.get('joker_hint', 3)
            ), commit=False)

        # 2. Table HISTORY (Crucial pour les questions répétées)
        res = sb.table("history").select("*").eq("user_id", user_id).execute()
        for h in res.data:
            run_query("INSERT OR IGNORE INTO history (user_id, question_hash) VALUES (?, ?)", 
                     (h['user_id'], h['question_hash']), commit=False)

        # 3. Table STATS
        res = sb.table("stats").select("*").eq("user_id", user_id).execute()
        for s in res.data:
            run_query("INSERT OR REPLACE INTO stats (user_id, category, correct_count) VALUES (?, ?, ?)", 
                     (s['user_id'], s['category'], s['correct_count']), commit=False)

        # 4. Table NOTES
        res = sb.table("notes").select("*").eq("user_id", user_id).execute()
        for n in res.data:
            run_query("INSERT OR REPLACE INTO notes (user_id, note_id, title, content, timestamp) VALUES (?, ?, ?, ?, ?)", 
                     (n['user_id'], n['note_id'], n['title'], n['content'], n['timestamp']), commit=False)

        # 5. Table GLOSSARY
        res = sb.table("glossary").select("*").eq("user_id", user_id).execute()
        for g in res.data:
            run_query("""
                INSERT OR REPLACE INTO glossary 
                (user_id, term, definition, category, use_case, business_impact, short_definition) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                g['user_id'], g['term'], g['definition'], g['category'], 
                g.get('use_case'), g.get('business_impact'), g.get('short_definition')
            ), commit=False)

        return True
    except Exception as e:
        print(f"Supabase Pull Error: {e}")
        return False

def sync_user_to_supabase(user_id):
    """Envoie une copie des données utilisateur vers Supabase."""
    sb = DatabaseManager.get_supabase()
    if not sb: return
    
    # On récupère les données locales fraîches
    local_data = run_query("SELECT * FROM users WHERE user_id=?", (user_id,), fetch_one=True)
    if not local_data: return
    
    # Mapping des données pour Supabase
    data = {
        "user_id": local_data[0], "name": local_data[1], "level": local_data[2],
        "xp": local_data[3], "total_score": local_data[4], "mastery": local_data[5],
        "q_count": local_data[6], "hearts": local_data[7], "email": local_data[9],
        "city": local_data[10], "crisis_wins": local_data[13], "has_diploma": local_data[15],
        "joker_5050": local_data[17], "joker_hint": local_data[18]
    }
    
    try:
        # Upsert (Insert ou Update) sur Supabase
        sb.table("users").upsert(data).execute()
    except Exception as e:
        print(f"Supabase Sync Error: {e}")

def seed_questions():
    """Importe les questions depuis le fichier JSON si la base est vide."""
    count = run_query("SELECT COUNT(*) FROM question_bank", fetch_one=True)[0]
    if count > 0:
        return # La base est déjà peuplée

    seed_file = Path(ROOT_DIR) / "questions_seed.json"
    if not seed_file.exists():
        return # Pas de fichier seed disponible

    try:
        with open(seed_file, "r", encoding="utf-8") as f:
            questions = json.load(f)
            for q in questions:
                run_query("""
                    INSERT INTO question_bank 
                    (category, concept, level, question, options, correct, explanation, theory, example, tip, triad_id, triad_position) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    q.get('category'), q.get('concept'), q.get('level'), 
                    q.get('question'), q.get('options'), q.get('correct'), 
                    q.get('explanation'), q.get('theory'), q.get('example'), 
                    q.get('tip'), q.get('triad_id'), q.get('triad_position')
                ), commit=True)
        st.success(f"🌱 {len(questions)} questions importées avec succès !")
    except Exception as e:
        st.error(f"Erreur lors de l'import des questions : {e}")

def init_db():
    """Initialise les tables locales et tente de créer les tables Cloud."""
    queries = [
        'CREATE TABLE IF NOT EXISTS users (user_id TEXT PRIMARY KEY, name TEXT, level INTEGER DEFAULT 1, xp INTEGER DEFAULT 0, total_score INTEGER DEFAULT 0, mastery INTEGER DEFAULT 0, q_count INTEGER DEFAULT 0, hearts INTEGER DEFAULT 5, last_seen TEXT, email TEXT UNIQUE, city TEXT, referred_by TEXT, xp_checkpoint INTEGER DEFAULT 0, crisis_wins INTEGER DEFAULT 0, redemptions INTEGER DEFAULT 0, has_diploma INTEGER DEFAULT 0, current_run_xp INTEGER DEFAULT 0, joker_5050 INTEGER DEFAULT 3, joker_hint INTEGER DEFAULT 3)',
        'CREATE TABLE IF NOT EXISTS history (user_id TEXT, question_hash TEXT, UNIQUE(user_id, question_hash))',
        'CREATE TABLE IF NOT EXISTS glossary (user_id TEXT, term TEXT, definition TEXT, category TEXT, use_case TEXT, business_impact TEXT, short_definition TEXT, UNIQUE(user_id, term))',
        'CREATE TABLE IF NOT EXISTS stats (user_id TEXT, category TEXT, correct_count INTEGER, UNIQUE(user_id, category))',
        'CREATE TABLE IF NOT EXISTS notes (user_id TEXT, note_id TEXT PRIMARY KEY, title TEXT, content TEXT, timestamp TEXT)',
        'CREATE TABLE IF NOT EXISTS ai_queue (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, question_json TEXT, category TEXT)',
        'CREATE TABLE IF NOT EXISTS question_bank (id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT, concept TEXT, level INTEGER, question TEXT, options TEXT, correct TEXT, explanation TEXT, theory TEXT, example TEXT, tip TEXT, triad_id TEXT, triad_position INTEGER DEFAULT 0)',
        'CREATE TABLE IF NOT EXISTS recent_failures (user_id TEXT, question_id INTEGER, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(user_id, question_id))',
        'CREATE TABLE IF NOT EXISTS difficulty_feedback (question_id INTEGER PRIMARY KEY, hard_votes INTEGER DEFAULT 0, easy_votes INTEGER DEFAULT 0)',
        'CREATE TABLE IF NOT EXISTS user_feedback (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, user_name TEXT, user_email TEXT, message TEXT, context TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)'
    ]
    for q in queries:
        run_query(q)
    
    # Migrations pour les JOKERS
    try: run_query("ALTER TABLE users ADD COLUMN joker_5050 INTEGER DEFAULT 3")
    except: pass
    try: run_query("ALTER TABLE users ADD COLUMN joker_hint INTEGER DEFAULT 3")
    except: pass
    
    # Index
    run_query("CREATE INDEX IF NOT EXISTS idx_triad ON question_bank(triad_id, triad_position)")
    
    # Peuplement initial si nécessaire
    seed_questions()

    # Nettoyage automatique des termes parasites du glossaire et des vieux échecs (Performance)
    run_query("DELETE FROM glossary WHERE definition LIKE '%Définition%' OR definition LIKE '%Déf%' OR definition LIKE '%?%' OR term = 'Terme' OR term = 'Objet';", commit=True)
    run_query("DELETE FROM recent_failures WHERE timestamp < datetime('now', '-1 day')", commit=True)

def get_leaderboard():

    """Récupère les meilleurs utilisateurs triés par Niveau puis par Score."""

    return run_query('SELECT name, total_score, level FROM users ORDER BY level DESC, total_score DESC LIMIT 10', fetch_all=True)
