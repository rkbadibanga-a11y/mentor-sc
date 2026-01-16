# services/quiz_engine.py
import random
import json
import hashlib
import time
import datetime
import threading
from typing import List, Dict, Tuple, Optional
import streamlit as st
from streamlit.runtime.scriptrunner import add_script_run_ctx
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

    def trigger_refill(self):
        # Refill léger asynchrone
        if st.session_state.get('refill_in_progress'): return
        st.session_state.refill_in_progress = True
        mn, _, _, lvl = self.get_current_module_info(st.session_state.q_count)
        
        def task():
            try:
                # Génération simplifiée
                prompt = f"Expert SC. Crée 3 QCM progressifs (JSON list) sur {mn} niveau {lvl}/4."
                raw, _ = self.ai.get_response(prompt)
                if raw:
                    start = raw.find('['); end = raw.rfind(']') + 1
                    batch = json.loads(raw[start:end])
                    tid = f"IA_{int(time.time())}"
                    for i, q in enumerate(batch):
                        run_query('INSERT INTO question_bank (category, concept, level, question, options, correct, explanation, triad_id, triad_position) VALUES (?,?,?,?,?,?,?,?,?)',
                                 (mn, q.get('concept',''), lvl, q['question'], json.dumps(q['options']), q['correct'], q['explanation'], tid, i+1), commit=True)
            finally: st.session_state.refill_in_progress = False
        
        thread = threading.Thread(target=task); add_script_run_ctx(thread); thread.start()

    def get_question_from_db(self, level_filter=1):
        uid = st.session_state.user_id
        
        # --- OPTIMISATION : FÉDÉRER LES INFOS D'ÉTAT ---
        if 'solved_hashes' not in st.session_state:
            with DatabaseManager.session() as cursor:
                cursor.execute('SELECT question_hash FROM history WHERE user_id=?', (uid,))
                st.session_state.solved_hashes = {r[0] for r in cursor.fetchall()}
        
        # 1. Récupération optimisée du niveau
        query = "SELECT id, question, options, correct, explanation, theory, example, tip, category, concept, triad_id, triad_position FROM question_bank WHERE level=?"
        all_q = run_query(query, (level_filter,), fetch_all=True)
        if not all_q: return None
        
        random.shuffle(all_q)
        for q_res in all_q:
            q_text = q_res[1]
            h = hashlib.md5(q_text.encode()).hexdigest()
            if h not in st.session_state.solved_hashes:
                return {
                    "id": q_res[0], "category": q_res[8], "concept_key": q_res[9],
                    "question": q_text, "options": json.loads(q_res[2]),
                    "correct": q_res[3], "explanation": q_res[4],
                    "theory": q_res[5], "example": q_res[6], "tip": q_res[7]
                }
        return None

    def manage_queue(self):
        # Priorité au Buffer
        if st.session_state.get('prefetched_data'):
            q = st.session_state.prefetched_data; st.session_state.prefetched_data = None
            return q
        
        q = self.get_question_from_db(st.session_state.level)
        if q:
            # On lance le prefetch pour la suite
            threading.Thread(target=self.prefetch_worker, args=(st.session_state.level,), daemon=True).start()
            return q
        return None

    def prefetch_worker(self, lvl):
        q = self.get_question_from_db(lvl)
        if q: st.session_state.prefetched_data = q

    def validate_answer(self, choice, q_data):
        uid = st.session_state.user_id
        is_correct = (str(choice).strip().upper() == str(q_data['correct']).strip().upper())
        
        st.session_state.answered = True
        out = "WIN" if is_correct else "LOSS"
        st.session_state.result = out
        st.session_state.last_result = out
        st.session_state.mentor_message = random.choice(MENTOR_REACTIONS[out]['default'])

        if is_correct:
            h = hashlib.md5(q_data['question'].encode()).hexdigest()
            st.session_state.solved_hashes.add(h)
            run_query('INSERT OR IGNORE INTO history (user_id, question_hash) VALUES (?, ?)', (uid, h), commit=True)
            
            st.session_state.xp += 20; st.session_state.total_score += 20; st.session_state.q_count += 1
            
            # Recalcul niveau
            new_lvl = 1
            for l, thresh in sorted(LEVEL_THRESHOLDS.items(), reverse=True):
                if st.session_state.q_count >= thresh: new_lvl = l; break
            st.session_state.level = new_lvl
            
            # Synchro DB
            run_query('UPDATE users SET xp=?, total_score=?, q_count=?, level=? WHERE user_id=?', 
                     (st.session_state.xp, st.session_state.total_score, st.session_state.q_count, st.session_state.level, uid), commit=True)
        else:
            st.session_state.hearts = max(0, st.session_state.hearts - 1)
            run_query('UPDATE users SET hearts=? WHERE user_id=?', (st.session_state.hearts, uid), commit=True)
            play_sfx("error")

def get_quiz_engine(): return QuizEngine()
