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
        # SQL RANDOM() : 100x plus rapide que charger toute la table
        query = """
            SELECT id, question, options, correct, explanation, theory, example, tip, category, concept 
            FROM question_bank 
            WHERE level=? AND question NOT IN (SELECT question_hash FROM history WHERE user_id=?)
            ORDER BY RANDOM() LIMIT 1
        """
        q_res = run_query(query, (lvl, uid), fetch_one=True)
        
        if q_res:
            return {
                "id": q_res[0], "question": q_res[1], "options": json.loads(q_res[2]),
                "correct": q_res[3], "explanation": q_res[4], "theory": q_res[5],
                "example": q_res[6], "tip": q_res[7], "category": q_res[8], "concept": q_res[9]
            }
        return None

    def manage_queue(self):
        return self.get_question_from_db(st.session_state.level)

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

def get_quiz_engine(): return QuizEngine()