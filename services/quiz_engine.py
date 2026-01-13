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
from core.database import run_query
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

    def _generate_single_batch(self, lvl, mod_n, user, mastery, streak):
        # Définition de la difficulté pour le prompt
        difficulty_guideline = ""
        if lvl == 1:
            difficulty_guideline = "Niveau DÉBUTANT : Focus sur les définitions, le vocabulaire de base et les concepts intuitifs. PAS de calculs complexes, uniquement de la logique simple."
        elif lvl == 4:
            difficulty_guideline = "Niveau EXPERT : Cas pratiques complexes, arbitrage de coûts (Trade-offs), stratégie CODIR et KPI avancés."
        else:
            difficulty_guideline = "Niveau INTERMÉDIAIRE : Application des formules standards et gestion opérationnelle."

        prompt = f"""Rôle: Expert Supply Chain Pédagogue. Concept module: {mod_n}. Niveau {lvl}/4.
        CONSIGNE DE DIFFICULTÉ : {difficulty_guideline}
        
        Crée une Triade de 3 QCM progressifs : 1.Savoir (Définition), 2.Comprendre (Pourquoi ?), 3.Appliquer (Cas pratique).
        JSON strict: [{{"question":"...", "options":{{"A":"..","B":"..","C":"..","D":".."}},"correct":"A","explanation":"...","category":"{mod_n}","concept_key":"..."}}]"""
        raw, engine = self.ai.get_response(prompt)
        if not raw: return [], engine
        try:
            start = raw.find('['); end = raw.rfind(']') + 1
            batch = json.loads(raw[start:end])
            return (batch if isinstance(batch, list) else [batch]), engine
        except: return [], "error"

    def trigger_refill(self):
        now = time.time()
        if st.session_state.get('refill_in_progress') and (now - st.session_state.get('last_refill_time', 0)) < 5: return
        lvl = st.session_state.level
        fresh = run_query("SELECT COUNT(*) FROM question_bank WHERE level=? AND triad_id NOT LIKE 'GOLDEN%'", (lvl,), fetch_one=True)[0]
        if fresh > 20: return
        st.session_state.refill_in_progress = True; st.session_state.last_refill_time = now
        mn, _, _, _ = self.get_current_module_info(st.session_state.q_count)
        def task():
            try:
                batch, _ = self._generate_single_batch(lvl, mn, st.session_state.user, 0, 0)
                if batch:
                    triad_id = f"IA_{int(time.time())}"
                    for i, q in enumerate(batch):
                        run_query('INSERT INTO question_bank (category, concept, level, question, options, correct, explanation, triad_id, triad_position) VALUES (?,?,?,?,?,?,?,?,?)',
                                 (q.get('category', mn), q.get('concept_key',''), lvl, q['question'], json.dumps(q['options']), q['correct'], q['explanation'], triad_id, i+1), commit=True)
            finally: st.session_state.refill_in_progress = False
        thread = threading.Thread(target=task); add_script_run_ctx(thread); thread.start()

    def get_question_from_db(self, level_filter=1):
        uid = st.session_state.user_id; force_fresh = (random.random() < 0.4)
        for pos in [1, 2, 3, None]:
            q = self._fetch_specific(level_filter, pos, uid, force_fresh)
            if q: return q
        return self._fetch_specific(level_filter, None, uid, False)

    def _fetch_specific(self, lvl, pos, uid, fresh):
        clause = f"WHERE level={lvl}"
        if pos: clause += f" AND triad_position={pos}"
        if fresh: clause += " AND triad_id NOT LIKE 'GOLDEN%'"
        
        # On tire un lot de questions potentielles en une seule requête (VITESSE)
        query = f"""
            SELECT id, category, concept, level, question, options, correct, explanation, theory, example, tip 
            FROM question_bank 
            {clause} 
            ORDER BY RANDOM() LIMIT 20
        """
        res_list = run_query(query, fetch_all=True)
        if not res_list: return None

        for res in res_list:
            q_id = res[0]
            h = hashlib.md5(res[4].encode()).hexdigest()
            
            # Vérification historique permanent (réussies)
            if run_query('SELECT 1 FROM history WHERE user_id=? AND question_hash=?', (uid, h), fetch_one=True):
                continue
                
            # Vérification échecs récents
            if run_query('SELECT 1 FROM recent_failures WHERE user_id=? AND question_id=?', (uid, q_id), fetch_one=True):
                continue
            
            return {"id":q_id,"category":res[1],"concept_key":res[2],"question":res[4],"options":json.loads(res[5]),"correct":res[6],"explanation":res[7],"theory":res[8],"example":res[9],"tip":res[10]}
        
        return None

    def record_difficulty_vote(self, q_id, vote_type):
        """Enregistre un vote 'Trop dur' ou 'Trop facile'."""
        col = "hard_votes" if vote_type == "hard" else "easy_votes"
        run_query(f"INSERT INTO difficulty_feedback (question_id, {col}) VALUES (?, 1) ON CONFLICT(question_id) DO UPDATE SET {col} = {col} + 1", (q_id,), commit=True)
        
        # Logique d'auto-régulation
        if vote_type == "hard":
            votes = run_query("SELECT hard_votes FROM difficulty_feedback WHERE question_id=?", (q_id,), fetch_one=True)
            if votes and votes[0] >= 5: # Si 5 votes 'Trop dur'
                run_query("UPDATE question_bank SET level = MIN(4, level + 1) WHERE id=?", (q_id,), commit=True)

    def prefetch_next_question(self):
        if st.session_state.get('prefetched_data') is None:
            q = self.get_question_from_db(st.session_state.level)
            if q: st.session_state.prefetched_data = q

    def manage_queue(self):
        if st.session_state.get('prefetched_data'):
            q = st.session_state.prefetched_data; st.session_state.prefetched_data = None
            st.session_state.current_engine = "Buffer RAM ⚡"; self._check_crisis_trigger()
            thread = threading.Thread(target=self.prefetch_next_question); add_script_run_ctx(thread); thread.start()
            return q
        q = self.get_question_from_db(st.session_state.level)
        if q:
            st.session_state.current_engine = "Base de données"; self.trigger_refill(); self._check_crisis_trigger()
            thread = threading.Thread(target=self.prefetch_next_question); add_script_run_ctx(thread); thread.start()
            return q
        return None

    def _check_crisis_trigger(self):
        if st.session_state.user == "Crise": st.session_state.crisis_active = True; st.session_state.crisis_start_time = time.time(); return
        if st.session_state.level >= 3 and st.session_state.hearts >= 3:
            if random.random() < 0.10 or (st.session_state.level == 3 and st.session_state.q_count > 370 and st.session_state.get('crisis_wins', 0) == 0):
                st.session_state.crisis_active = True; st.session_state.crisis_start_time = time.time(); play_sfx("alert")

    def validate_answer(self, choice, q_data):
        uid = st.session_state.user_id
        is_crisis = st.session_state.get('crisis_active', False)
        
        # 1. SÉCURITÉ SERVEUR : VÉRIFICATION TIMEOUT CRISE (Strict)
        if is_crisis:
            elapsed = time.time() - st.session_state.crisis_start_time
            if elapsed >= 30.1: # Strict timeout
                st.session_state.update({
                    'crisis_active': False,
                    'answered': True,
                    'result': 'LOSS',
                    'last_result': 'LOSS',
                    'show_crisis_failure_dialog_trigger': True,
                    'hearts': max(0, st.session_state.hearts - 2)
                })
                st.toast("💀 TEMPS ÉCOULÉ !", icon="⏰")
                run_query('UPDATE users SET hearts=?, crisis_active=0 WHERE user_id=?', (st.session_state.hearts, uid), commit=True)
                return 

        # 2. Comparaison Sécurisée (Strip & Upper)
        clean_choice = str(choice).strip().upper()
        clean_correct = str(q_data['correct']).strip().upper()
        
        # DEBUG LOG
        print(f"DEBUG VALIDATION: User Choice='{clean_choice}', Expected='{clean_correct}'")
        
        is_correct = (clean_choice == clean_correct)
        
        st.session_state.answered = True
        out = "WIN" if is_correct else "LOSS"
        st.session_state.result = out
        st.session_state.last_result = out
        
        # Fin de crise (Réponse donnée à temps)
        st.session_state.crisis_active = False

        pool = MENTOR_REACTIONS[out]['default'].copy()
        st.session_state.mentor_message = random.choice(pool)

        if is_correct:
            h = hashlib.md5(q_data['question'].encode()).hexdigest()
            run_query('INSERT OR IGNORE INTO history (user_id, question_hash) VALUES (?, ?)', (uid, h), commit=True)
            run_query('INSERT INTO stats (user_id, category, correct_count) VALUES (?, ?, 1) ON CONFLICT(user_id, category) DO UPDATE SET correct_count = correct_count + 1', (uid, q_data.get("category", "Général")), commit=True)
            
            # Enrichissement du Glossaire
            concept = q_data.get('concept_key') or q_data.get('concept')
            if concept and len(str(concept)) > 2:
                run_query('INSERT OR IGNORE INTO glossary (user_id, term, definition, category) VALUES (?, ?, ?, ?)',
                         (uid, concept, q_data.get('explanation', ''), q_data.get('category', 'Général')), commit=True)

            # Badge Detection
            old_c = run_query('SELECT correct_count FROM stats WHERE user_id=? AND category=?', (uid, q_data.get("category", "Général")), fetch_one=True)
            old_val = old_c[0] if old_c else 0
            if q_data.get('category') in ["Achats", "Stocks", "Transport", "IA & Data", "Stratégie Lean"]:
                if old_val == 10:
                    st.session_state.pending_badge = {"emoji": "🏅", "title": q_data['category'], "desc": "Expertise validée !"}

            st.session_state.xp += 20; st.session_state.total_score += 20; st.session_state.q_count += 1; st.session_state.consecutive_wins += 1
            
            # --- CALCUL DU NIVEAU ET DE LA MAÎTRISE ---
            new_qc = st.session_state.q_count
            new_lvl = 1
            for l, thresh in sorted(LEVEL_THRESHOLDS.items(), reverse=True):
                if new_qc >= thresh:
                    new_lvl = l
                    break
            st.session_state.level = new_lvl
            
            # Calcul de la maîtrise du niveau actuel (0-100%)
            current_thresh = LEVEL_THRESHOLDS.get(new_lvl, 0)
            next_thresh = LEVEL_THRESHOLDS.get(new_lvl + 1, 500)
            range_len = next_thresh - current_thresh
            if range_len > 0:
                st.session_state.mastery = min(100, int(((new_qc - current_thresh) / range_len) * 100))
            else:
                st.session_state.mastery = 100

            # --- PERSISTANCE EN BASE DE DONNÉES ---
            now_ts = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
            run_query('''
                UPDATE users 
                SET xp = ?, total_score = ?, q_count = ?, level = ?, mastery = ?, hearts = ?, crisis_wins = ?, last_seen = ? 
                WHERE user_id = ?
            ''', (
                st.session_state.xp, 
                st.session_state.total_score, 
                st.session_state.q_count, 
                st.session_state.level, 
                st.session_state.mastery,
                st.session_state.hearts,
                st.session_state.get('crisis_wins', 0),
                now_ts,
                uid
            ), commit=True)
            
            if is_crisis:
                st.session_state.hearts = 5
                if st.session_state.get('crisis_wins', 0) == 0:
                    st.session_state.pending_badge = {"emoji": "🔥", "title": "MAÎTRE DU CHAOS", "desc": "1ère crise maîtrisée !"}
                st.session_state.crisis_wins = st.session_state.get('crisis_wins', 0) + 1
            
            if st.session_state.q_count == 5:
                st.session_state.pending_badge = {"emoji": "🔰", "title": "OPÉRATEUR SC", "desc": "Début de carrière !"}
            
            if st.session_state.consecutive_wins >= 5:
                st.session_state.hearts = min(5, st.session_state.hearts + 1); st.session_state.consecutive_wins = 0
        else:
            # DÉFAITE
            if is_crisis:
                st.session_state.hearts = max(0, st.session_state.hearts - 2)
                st.session_state.show_crisis_failure_dialog_trigger = True
                st.toast("💀 ÉCHEC CRITIQUE !", icon="💥")
            else:
                st.session_state.hearts = max(0, st.session_state.hearts - 1)
            
            st.session_state.consecutive_wins = 0
            # Synchro des cœurs et activité en cas de défaite
            now_ts = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
            run_query('UPDATE users SET hearts=?, last_seen=? WHERE user_id=?', (st.session_state.hearts, now_ts, uid), commit=True)
            
            # Enregistrer l'échec pour éviter de revoir la question pendant 24h
            run_query('INSERT OR IGNORE INTO recent_failures (user_id, question_id) VALUES (?, ?)', (uid, q_data['id']), commit=True)
            play_sfx("error")

def get_quiz_engine(): return QuizEngine()