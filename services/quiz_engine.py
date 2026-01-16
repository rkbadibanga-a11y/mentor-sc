# services/quiz_engine.py
import random
import json
import hashlib
import time
import threading
import streamlit as st
from services.ai_engine import get_ai_service
from core.database import run_query, DatabaseManager
from core.config import CURRICULUM, MENTOR_REACTIONS, LEVEL_THRESHOLDS
from utils.assets import play_sfx

class QuizEngine:
    def __init__(self):
        self.ai = get_ai_service()

    def get_current_module_info(self, qc: int):
        lvl = 1
        for l, thresh in sorted(LEVEL_THRESHOLDS.items(), reverse=True):
            if qc >= thresh: lvl = l; break
        lstart = LEVEL_THRESHOLDS.get(lvl, 0)
        local_q = qc - lstart
        if local_q <= 0: local_q = 1
        cum = 0
        for m_n, m_c in CURRICULUM.get(lvl, CURRICULUM[1]):
            if local_q <= cum + m_c: return m_n, local_q - cum, m_c, lvl
            cum += m_c
        return CURRICULUM[lvl][-1][0], 1, 1, lvl

    def get_question_from_db(self, lvl):
        uid = st.session_state.user_id
        
        # 1. Identifier le module en cours (Pédagogie)
        current_module, _, _, _ = self.get_current_module_info(st.session_state.q_count)
        
        # 2. Chercher une question de ce module spécifique
        query_module = """
            SELECT id, question, options, correct, explanation, theory, example, tip, category, concept 
            FROM question_bank 
            WHERE level=? AND category=? AND question NOT IN (SELECT question_hash FROM history WHERE user_id=?)
            ORDER BY RANDOM() LIMIT 1
        """
        q_res = run_query(query_module, (lvl, current_module, uid), fetch_one=True)
        
        # 3. Si aucune question du module, fallback sur le niveau global (Révision)
        if not q_res:
            query_global = """
                SELECT id, question, options, correct, explanation, theory, example, tip, category, concept 
                FROM question_bank 
                WHERE level=? AND question NOT IN (SELECT question_hash FROM history WHERE user_id=?)
                ORDER BY RANDOM() LIMIT 1
            """
            q_res = run_query(query_global, (lvl, uid), fetch_one=True)
        
        if q_res:
            return {
                "id": q_res[0], "question": q_res[1], "options": json.loads(q_res[2]),
                "correct": q_res[3], "explanation": q_res[4], "theory": q_res[5],
                "example": q_res[6], "tip": q_res[7], "category": q_res[8], "concept": q_res[9]
            }
        return None

    def manage_queue(self):
        # 1. Tenter la DB
        q = self.get_question_from_db(st.session_state.level)
        if q: return q
        
        # 2. Si vide, on génère à la volée (Fallback IA)
        mn, _, _, lvl = self.get_current_module_info(st.session_state.q_count)
        prompt = f"Génère 1 QCM Supply Chain sur '{mn}' niveau {lvl}/4. JSON: {{'question':'...', 'options':{{'A':'..','B':'..','C':'..','D':'..'}}, 'correct':'A', 'explanation':'...', 'category':'{mn}'}}"
        raw, _ = self.ai.get_response(prompt)
        
        if raw:
            try:
                # Nettoyage JSON
                raw = raw.replace("```json", "").replace("```", "").strip()
                q_data = json.loads(raw)
                # Sauvegarde immédiate pour la prochaine fois
                run_query('INSERT INTO question_bank (category, level, question, options, correct, explanation) VALUES (?,?,?,?,?,?)',
                         (mn, lvl, q_data['question'], json.dumps(q_data['options']), q_data['correct'], q_data['explanation']), commit=True)
                return {
                    "id": None, # Pas d'ID encore
                    "question": q_data['question'], "options": q_data['options'],
                    "correct": q_data['correct'], "explanation": q_data['explanation'],
                    "category": mn
                }
            except: pass
            
        # 3. ULTIMATE FAILSAFE (Si DB vide et IA HS)
        # On renvoie une question statique pour débloquer l'utilisateur
        return {
            "id": None,
            "question": "Question de secours : Quel est le flux qui remonte du client vers le fournisseur ?",
            "options": {"A": "Flux Financier", "B": "Flux Physique", "C": "Flux d'Information", "D": "Flux Logistique Inverse (Reverse)"},
            "correct": "D",
            "explanation": "C'est la Logistique Inverse (Reverse Logistics), qui gère les retours, le SAV et le recyclage.",
            "category": "Fondamentaux",
            "concept": "Reverse Logistics"
        }

    def validate_answer(self, choice, q_data):
        uid = st.session_state.user_id
        is_correct = (str(choice).strip().upper() == str(q_data['correct']).strip().upper())
        
        st.session_state.answered = True
        st.session_state.result = "WIN" if is_correct else "LOSS"
        st.session_state.last_result = st.session_state.result
        st.session_state.mentor_message = random.choice(MENTOR_REACTIONS[st.session_state.result]['default'])

        if is_correct:
            run_query('INSERT OR IGNORE INTO history (user_id, question_hash) VALUES (?, ?)', (uid, q_data['question']), commit=True)
            st.session_state.xp += 20; st.session_state.total_score += 20; st.session_state.q_count += 1
            
            new_lvl = 1
            for l, thresh in sorted(LEVEL_THRESHOLDS.items(), reverse=True):
                if st.session_state.q_count >= thresh: new_lvl = l; break
            st.session_state.level = new_lvl
            
            run_query('UPDATE users SET xp=?, total_score=?, q_count=?, level=? WHERE user_id=?', 
                     (st.session_state.xp, st.session_state.total_score, st.session_state.q_count, st.session_state.level, uid), commit=True)
        else:
            st.session_state.hearts = max(0, st.session_state.hearts - 1)
            run_query('UPDATE users SET hearts=? WHERE user_id=?', (st.session_state.hearts, uid), commit=True)
            play_sfx("error")

    def record_difficulty_vote(self, q_id, vote_type):
        if not q_id: return
        col = "hard_votes" if vote_type == "hard" else "easy_votes"
        run_query(f"INSERT INTO difficulty_feedback (question_id, {col}) VALUES (?, 1) ON CONFLICT(question_id) DO UPDATE SET {col}={col}+1", (q_id,), commit=True)

def get_quiz_engine(): return QuizEngine()