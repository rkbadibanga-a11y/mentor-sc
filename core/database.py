# core/database.py
import sqlite3
import os
import json
import streamlit as st
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
        """Context manager pour assurer le commit/rollback automatique.
        Crée une nouvelle connexion à chaque fois pour éviter les conflits de threads.
        """
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
    """Exécute une requête SQL localement et synchronise avec le Cloud si nécessaire."""
    # 1. Exécution Locale (Vitesse)
    result = None
    with DatabaseManager.session() as cursor:
        cursor.execute(query, params)
        if fetch_one:
            result = cursor.fetchone()
        elif fetch_all:
            result = cursor.fetchall()
        else:
            result = True

    # 2. Synchronisation Cloud (Arrière-plan)
    # On ne synchronise que les mises à jour critiques de l'utilisateur
    if commit and "UPDATE users" in query.upper():
        st.info("☁️ Synchro Cloud...") # Optionnel : feedback visuel discret
        sync_user_to_supabase(params[-1]) # L'UID est toujours le dernier paramètre des UPDATE users
        
    return result

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
        "city": local_data[10], "crisis_wins": local_data[13], "has_diploma": local_data[15]
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
        'CREATE TABLE IF NOT EXISTS question_bank (id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT, concept TEXT, level INTEGER, question TEXT, options TEXT, correct TEXT, explanation TEXT, theory TEXT, example TEXT, tip TEXT, triad_id TEXT, triad_position INTEGER DEFAULT 0)'
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

    # Nettoyage automatique des termes parasites du glossaire
    run_query("DELETE FROM glossary WHERE definition LIKE '%Définition%' OR definition LIKE '%Déf%' OR definition LIKE '%?%' OR term = 'Terme' OR term = 'Objet';", commit=True)

def get_leaderboard():
    return run_query('SELECT name, total_score, level FROM users ORDER BY total_score DESC LIMIT 5', fetch_all=True)