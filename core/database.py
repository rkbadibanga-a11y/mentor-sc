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
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key: return None
    try: return create_client(url, key)
    except: return None

class DatabaseManager:
    @staticmethod
    def get_supabase() -> Client:
        return get_supabase_client()

    @classmethod
    @contextmanager
    def session(cls):
        conn = sqlite3.connect(DB_FILE, check_same_thread=False, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except:
            conn.rollback()
            raise
        finally:
            conn.close()

def run_query(query: str, params: tuple = (), fetch_one=False, fetch_all=False, commit=True):
    result = None
    with DatabaseManager.session() as cursor:
        cursor.execute(query, params)
        if fetch_one: result = cursor.fetchone()
        elif fetch_all: result = cursor.fetchall()
        else: result = True

    if commit:
        q_upper = query.upper()
        uid = st.session_state.get('user_id') or (params[0] if params else None)
        if uid:
            if "UPDATE USERS" in q_upper:
                threading.Thread(target=sync_user_to_supabase, args=(uid,), daemon=True).start()
            elif "INSERT" in q_upper or "UPDATE" in q_upper:
                table = None
                if "HISTORY" in q_upper: table = "history"
                elif "GLOSSARY" in q_upper: table = "glossary"
                elif "NOTES" in q_upper: table = "notes"
                elif "STATS" in q_upper: table = "stats"
                elif "QUESTION_BANK" in q_upper: table = "question_bank"
                if table:
                    threading.Thread(target=sync_generic_table, args=(table, uid, params, q_upper), daemon=True).start()
                    if table == "question_bank":
                        enforce_question_limit(2000)
    return result

def enforce_question_limit(limit=2000):
    try:
        with DatabaseManager.session() as cursor:
            cursor.execute("SELECT COUNT(*) FROM question_bank")
            count = cursor.fetchone()[0]
            if count > limit:
                to_delete = count - limit
                cursor.execute(f"DELETE FROM question_bank WHERE id IN (SELECT id FROM question_bank ORDER BY id ASC LIMIT {to_delete})")
    except: pass

def sync_generic_table(table, uid, params, query_type):
    try:
        sb = DatabaseManager.get_supabase()
        if not sb: return
        data = {}
        if table == "history":
            data = {"user_id": uid, "question_hash": params[1] if len(params) > 1 else ""}
        elif table == "question_bank":
            data = {"category": params[0], "level": params[1], "question": params[2], "options": params[3], "correct": params[4], "explanation": params[5]}
        elif table == "glossary":
            term = params[1] if len(params) > 1 else ""
            with DatabaseManager.session() as cursor:
                cursor.execute("SELECT * FROM glossary WHERE user_id=? AND term=?", (uid, term))
                res = cursor.fetchone()
            if res:
                data = {"user_id": res[0], "term": res[1], "definition": res[2], "category": res[3], "use_case": res[4], "business_impact": res[5], "short_definition": res[6]}
        if data:
            sb.table(table).upsert(data).execute()
    except: pass

def pull_shared_questions():
    import time
    time.sleep(5)
    try:
        sb = DatabaseManager.get_supabase()
        if not sb: return
        res = sb.table("question_bank").select("*").order("id", desc=True).limit(50).execute()
        if res.data:
            with DatabaseManager.session() as cursor:
                for q in res.data:
                    cursor.execute("INSERT OR IGNORE INTO question_bank (category, level, question, options, correct, explanation) VALUES (?,?,?,?,?,?)",
                                 (q['category'], q['level'], q['question'], q['options'], q['correct'], q['explanation']))
    except: pass

@st.cache_data(ttl=3600)
def pull_user_data_from_supabase(user_id):
    sb = DatabaseManager.get_supabase()
    if not sb: return False
    try:
        res = sb.table("users").select("*").eq("user_id", user_id).execute()
        if res.data:
            u = res.data[0]
            run_query("INSERT OR REPLACE INTO users (user_id, name, level, xp, total_score, mastery, q_count, hearts, email, city, crisis_wins, has_diploma, joker_5050, joker_hint) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", 
                     (u['user_id'], u['name'], u.get('level', 1), u.get('xp', 0), u.get('total_score', 0), u.get('mastery', 0), u.get('q_count', 0), u.get('hearts', 5), u.get('email'), u.get('city', ''), u.get('crisis_wins', 0), u.get('has_diploma', 0), u.get('joker_5050', 3), u.get('joker_hint', 3)), commit=False)
            res_g = sb.table("glossary").select("*").eq("user_id", user_id).execute()
            for g in res_g.data:
                run_query("INSERT OR REPLACE INTO glossary (user_id, term, definition, category, use_case, business_impact, short_definition) VALUES (?,?,?,?,?,?,?)",
                         (g['user_id'], g['term'], g['definition'], g['category'], g.get('use_case'), g.get('business_impact'), g.get('short_definition')), commit=False)
            return True
    except: pass
    return False

def sync_user_to_supabase(user_id):
    sb = DatabaseManager.get_supabase()
    if not sb: return
    try:
        with DatabaseManager.session() as cursor:
            cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
            ld = cursor.fetchone()
        if ld:
            data = {"user_id": str(ld[0]), "name": str(ld[1]), "level": int(ld[2] or 1), "xp": int(ld[3] or 0), "total_score": int(ld[4] or 0), "mastery": int(ld[5] or 0), "q_count": int(ld[6] or 0), "hearts": int(ld[7] or 5), "email": str(ld[9] or ""), "city": str(ld[10] or ""), "crisis_wins": int(ld[13] or 0), "has_diploma": int(ld[15] or 0), "joker_5050": int(ld[17] if len(ld)>17 else 3), "joker_hint": int(ld[18] if len(ld)>18 else 3)}
            sb.table("users").upsert(data).execute()
    except: pass

@st.cache_resource
def init_db():
    threading.Thread(target=pull_shared_questions, daemon=True).start()
    queries = [
        'CREATE TABLE IF NOT EXISTS users (user_id TEXT PRIMARY KEY, name TEXT, level INTEGER DEFAULT 1, xp INTEGER DEFAULT 0, total_score INTEGER DEFAULT 0, mastery INTEGER DEFAULT 0, q_count INTEGER DEFAULT 0, hearts INTEGER DEFAULT 5, last_seen TEXT, email TEXT UNIQUE, city TEXT, referred_by TEXT, xp_checkpoint INTEGER DEFAULT 0, crisis_wins INTEGER DEFAULT 0, redemptions INTEGER DEFAULT 0, has_diploma INTEGER DEFAULT 0, current_run_xp INTEGER DEFAULT 0, joker_5050 INTEGER DEFAULT 3, joker_hint INTEGER DEFAULT 3)',
        'CREATE TABLE IF NOT EXISTS history (user_id TEXT, question_hash TEXT, UNIQUE(user_id, question_hash))',
        'CREATE TABLE IF NOT EXISTS stats (user_id TEXT, category TEXT, correct_count INTEGER, UNIQUE(user_id, category))',
        'CREATE TABLE IF NOT EXISTS question_bank (id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT, concept TEXT, level INTEGER, question TEXT, options TEXT, correct TEXT, explanation TEXT, theory TEXT, example TEXT, tip TEXT, triad_id TEXT, triad_position INTEGER DEFAULT 0)',
        'CREATE TABLE IF NOT EXISTS glossary (user_id TEXT, term TEXT, definition TEXT, category TEXT, use_case TEXT, business_impact TEXT, short_definition TEXT, UNIQUE(user_id, term))',
        'CREATE TABLE IF NOT EXISTS notes (user_id TEXT, note_id TEXT PRIMARY KEY, title TEXT, content TEXT, timestamp TEXT)',
        'CREATE TABLE IF NOT EXISTS difficulty_feedback (question_id INTEGER, hard_votes INTEGER DEFAULT 0, easy_votes INTEGER DEFAULT 0, PRIMARY KEY(question_id))',
        'CREATE TABLE IF NOT EXISTS user_feedback (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, message TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)',
        'CREATE TABLE IF NOT EXISTS ai_queue (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, question_json TEXT, category TEXT)'
    ]
    with DatabaseManager.session() as cursor:
        for q in queries: cursor.execute(q)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_user ON history(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_qhash ON history(question_hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_composite ON history(user_id, question_hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_qbank_lvl_cat ON question_bank(level, category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_stats_user ON stats(user_id)")
        cursor.execute("SELECT COUNT(*) FROM question_bank")
        if cursor.fetchone()[0] == 0:
            seed_file = Path(ROOT_DIR) / "questions_seed.json"
            if seed_file.exists():
                with open(seed_file, "r", encoding="utf-8") as f:
                    qs = json.load(f)
                    for q in qs:
                        cursor.execute("INSERT INTO question_bank (category, concept, level, question, options, correct, explanation, triad_id, triad_position) VALUES (?,?,?,?,?,?,?,?,?)", (q.get('category'), q.get('concept'), q.get('level'), q.get('question'), json.dumps(q.get('options')), q.get('correct'), q.get('explanation'), q.get('triad_id'), q.get('triad_position')))
    return True

def sync_leaderboard_from_supabase(limit=20):
    sb = DatabaseManager.get_supabase()
    if not sb: return
    try:
        res = sb.table("users").select("user_id, name, level, total_score, city").order("level", desc=True).limit(limit).execute()
        if res.data:
            with DatabaseManager.session() as cursor:
                for u in res.data: cursor.execute("INSERT OR REPLACE INTO users (user_id, name, level, total_score, city) VALUES (?, ?, ?, ?, ?)", (u['user_id'], u['name'], u.get('level', 1), u.get('total_score', 0), u.get('city', '')))
    except: pass

def get_leaderboard(sync=False):
    if sync: threading.Thread(target=sync_leaderboard_from_supabase, daemon=True).start()
    return run_query('SELECT name, total_score, level FROM users ORDER BY level DESC, total_score DESC LIMIT 10', fetch_all=True)