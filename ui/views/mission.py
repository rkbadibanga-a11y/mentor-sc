# ui/views/mission.py
import streamlit as st
import time
import hashlib
import random
import json
from streamlit_lottie import st_lottie
from services.quiz_engine import get_quiz_engine
from core.config import COLORS, t, CURRICULUM, LOTTIE_URLS
from ui.components import render_mentor_footer
from core.database import run_query
from services.ai_engine import get_ai_service

@st.dialog("⌛ TEMPS ÉCOULÉ !")
def show_crisis_failure_dialog():
    st.markdown("""
        <div style='text-align: center;'>
            <div style='font-size: 5rem; margin-bottom: 10px;'>💀</div>
            <h2 style='color: #ef4444;'>ÉCHEC CRITIQUE</h2>
            <p>La crise a paralysé vos opérations.<br>Le bilan est lourd : <b>-2 Stocks</b>.</p>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("CONTINUER 🚀", type="primary", use_container_width=True):
        st.session_state.crisis_active = False
        st.session_state.answered = True
        st.session_state.result = "LOSS"
        st.session_state.last_result = "LOSS"
        st.session_state.hearts = max(0, st.session_state.hearts - 2)
        uid = st.session_state.user_id
        run_query('UPDATE users SET hearts=? WHERE user_id=?', (st.session_state.hearts, uid), commit=True)
        st.rerun()

def tts_button(text, label="🔊"):
    import json
    safe_text = json.dumps(text.replace("\n", " "))
    st.components.v1.html(f'''
        <button id="tts-btn" style="background: linear-gradient(90deg, #007cf0, #00dfd8); color: white; border: none; padding: 5px 10px; border-radius: 15px; cursor: pointer; font-weight: bold;">{label}</button>
        <script>
            var ttsBtn = document.getElementById('tts-btn');
            ttsBtn.onclick = function() {{
                if (window.speechSynthesis.speaking) {{ window.speechSynthesis.cancel(); }} 
                else {{
                    const u = new SpeechSynthesisUtterance({safe_text});
                    u.lang = 'fr-FR'; u.rate = 1.0; window.speechSynthesis.speak(u);
                }}
            }};
        </script>
    ''', height=40)

@st.dialog("NOUVEAU BADGE BLOQUÉ ! 🏅", width="small")
def show_badge_dialog(badge_data):
    emoji = badge_data.get('emoji', '🏅')
    title = badge_data.get('title', 'Expert')
    desc = badge_data.get('desc', 'Félicitations !')
    
    st.markdown(f"""
        <div style='text-align: center;'>
            <div style='font-size: 5rem; margin-bottom: 10px;'>{emoji}</div>
            <h3 style='color: #00dfd8;'>{title}</h3>
            <p>{desc}<br>Badge débloqué dans votre profil.</p>
        </div>
    """, unsafe_allow_html=True)
    try:
        st_lottie(LOTTIE_URLS['trophy'], height=120, key=f'anim_badge_{title}', loop=False)
    except: pass
    
    if st.button("CONTINUER 🚀", type="primary", use_container_width=True):
        st.session_state.pending_badge = None
        st.rerun()

def render_stock_out():
    st.markdown(f"""
        <div style='text-align: center; background: rgba(239, 68, 68, 0.1); padding: 40px; border-radius: 20px; border: 2px solid #ef4444;'>
            <div style='font-size: 6rem; margin-bottom: 20px;'>🚫</div>
            <h1 style='color: #ef4444;'>RUPTURE DE STOCK !</h1>
            <p style='font-size: 1.2rem;'>Vous n'avez plus de vies disponibles pour continuer la mission.</p>
            <p>La Supply Chain est à l'arrêt.</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("❤️ Réapprovisionner (100 XP)", use_container_width=True, type="primary"):
            if st.session_state.xp >= 100:
                st.session_state.xp -= 100
                st.session_state.hearts = 3
                uid = st.session_state.user_id
                run_query('UPDATE users SET hearts=3, xp=xp-100 WHERE user_id=?', (uid,), commit=True)
                st.success("Réapprovisionnement effectué ! +3 Vies")
                time.sleep(1)
                st.rerun()
            else:
                st.error("XP Insuffisante !")
    
    with c2:
        if st.button("🙏 Demander une grâce au Mentor", use_container_width=True):
            st.session_state.hearts = 1
            st.session_state.redemptions = st.session_state.get('redemptions', 0) + 1
            uid = st.session_state.user_id
            run_query('UPDATE users SET hearts=1, redemptions=redemptions+1 WHERE user_id=?', (uid,), commit=True)
            st.warning("Le Mentor vous accorde une dernière vie... Ne la gâchez pas.")
            time.sleep(1)
            st.rerun()

def render_mission():
    # --- CHECK STOCK OUT ---
    if st.session_state.hearts <= 0:
        render_stock_out()
        return

    engine = get_quiz_engine()
    uid = st.session_state.user_id
    qc = st.session_state.q_count
    lang = st.session_state.get('lang', 'Français')
    
    # --- 0. INITIALISATION SÉCURISÉE ---
    if 'crisis_active' not in st.session_state: st.session_state.crisis_active = False
    if 'crisis_start_time' not in st.session_state: st.session_state.crisis_start_time = 0
    if 'result' not in st.session_state: st.session_state.result = None # Sécurité additionnelle
    if 'crisis_dialog_shown' not in st.session_state: st.session_state.crisis_dialog_shown = False
    if 'pending_badge' not in st.session_state: st.session_state.pending_badge = None

    # --- 1. CÉLÉBRATION BADGE UNIFIÉE ---
    if st.session_state.pending_badge:
        show_badge_dialog(st.session_state.pending_badge)

    # --- 1. DÉTECTION ÉCHEC CRISE (Affichage du Badge) ---
    if st.session_state.get('show_crisis_failure_dialog_trigger'):
        if not st.session_state.get('crisis_dialog_shown', False):
            # On ne l'affiche que si on n'a pas encore répondu à la question suivante
            if st.session_state.get('data'): 
                st.session_state.crisis_dialog_shown = True
                show_crisis_failure_dialog()

    # --- 2. CHARGEMENT QUESTION ---
    if st.session_state.data is None:
        st.session_state.mentor_working = True
        with st.spinner("📦 Préparation..."):
            try: st.session_state.data = engine.manage_queue()
            except: st.session_state.data = None
        st.session_state.answered = False
        st.session_state.crisis_dialog_shown = False # Reset
        st.session_state.show_crisis_failure_dialog_trigger = False # Reset le trigger
        st.rerun() 
    
    q = st.session_state.data
    if q is None: return

    # --- 3. GESTION DU TIMER JS (REDIRECTION À 0s) ---
    if st.session_state.crisis_active and not st.session_state.answered:
        end_ts = (st.session_state.crisis_start_time + 30) * 1000
        fail_url = f"/?uid={uid}&status=crisis_fail"

        st.components.v1.html(f"""
            <div id="timer-box" style="background: linear-gradient(90deg, #ef4444, #7f1d1d); color: white; text-align: center; padding: 12px; border-radius: 10px; font-weight: bold; font-size: 22px; border: 2px solid white; font-family: sans-serif;">🚨 CHARGEMENT...</div>
            <script>
                const target = {end_ts};
                function update() {{
                    const now = new Date().getTime();
                    const diff = target - now;
                    const sec = Math.ceil(diff / 1000);
                    const el = document.getElementById('timer-box');
                    if (sec <= 0) {{
                        el.innerHTML = "💀 TEMPS ÉCOULÉ !";
                        // INFAILLIBLE : Redirige toute la fenêtre parente
                        window.parent.location.href = "{fail_url}";
                    }} else {{
                        el.innerHTML = "🚨 CRISE : " + sec + "s 🚨";
                    }}
                }}
                setInterval(update, 1000); update();
            </script>
        """, height=80)

    # --- 4. UI HEADER (Module + Jokers) ---
    mn, mp, mt, lvl = engine.get_current_module_info(qc)
    c_head, c_jokers = st.columns([0.55, 0.45])
    with c_head: st.markdown(f"#### 📦 {mn} ({mp}/{mt})")
    with c_jokers:
        if not st.session_state.answered:
            cj1, cj2 = st.columns(2)
            j5 = int(st.session_state.get('joker_5050') or 0)
            if cj1.button(f"🔍 50/50 ({j5})", key="j50", disabled=bool(j5 <= 0 or st.session_state.get('active_joker_5050')), type="primary", use_container_width=True):
                st.session_state.joker_5050 -= 1; st.session_state.active_joker_5050 = True
                run_query("UPDATE users SET joker_5050=joker_5050-1 WHERE user_id=?", (uid,), commit=True); st.rerun()
            jh = int(st.session_state.get('joker_hint') or 0)
            if cj2.button(f"📞 Indice ({jh})", key="jh", disabled=bool(jh <= 0 or st.session_state.get('active_joker_hint')), type="primary", use_container_width=True):
                st.session_state.joker_hint -= 1; st.session_state.active_joker_hint = True
                with st.spinner("..."):
                    p = f"Indice court pour : {q['question']}"
                    hint, en = get_ai_service().get_response(p)
                    st.session_state.current_hint, st.session_state.current_engine = hint, en
                run_query("UPDATE users SET joker_hint=joker_hint-1 WHERE user_id=?", (uid,), commit=True); st.rerun()

    # --- 5. AFFICHAGE QUESTION ---
    st.markdown("<br>", unsafe_allow_html=True)
    c_q, c_s = st.columns([0.85, 0.15])
    with c_q:
        box = "question-box fade-in"
        if st.session_state.get('answered') and st.session_state.get('result') == "LOSS": box = "question-box shake"
        st.markdown(f'<div class="{box}">{q["question"]}</div>', unsafe_allow_html=True)
    with c_s: tts_button(q["question"], "q_voice")
    if st.session_state.get('active_joker_hint'): st.info(f"💡 Indice : {st.session_state.get('current_hint')}")

    # --- 6. OPTIONS ---
    cols = st.columns(2)
    # Sécurisation : on s'assure que options est un dictionnaire
    opts_raw = q.get('options', {})
    if isinstance(opts_raw, str):
        try: opts = json.loads(opts_raw)
        except: opts = {}
    else:
        opts = opts_raw.copy()

    if st.session_state.get('active_joker_5050'):
        wrong = [k for k in opts.keys() if k != q['correct']]
        for k in random.sample(wrong, 2): opts[k] = "---"
    for i, (k, v) in enumerate(opts.items()):
        if cols[i%2].button(f"{k}) {v}", key=f"q_{k}", disabled=st.session_state.answered or v=="---", use_container_width=True):
            engine.validate_answer(k, q); st.session_state.active_joker_5050 = st.session_state.active_joker_hint = False
            st.session_state.current_hint = None; st.rerun()

    # --- 7. FEEDBACK ---
    if st.session_state.answered:
        try:
            if st.session_state.result == "WIN": st_lottie(LOTTIE_URLS['success'], height=150, key='win')
            else: st_lottie(LOTTIE_URLS['failed'], height=150, key='loss')
        except: pass
        if st.session_state.result == "WIN": st.success(f"✅ CORRECT ! {q['explanation']}")
        else: st.error(f"❌ ERREUR. Réponse : {q['correct']}. {q['explanation']}")
            
        def get_c(qd, ct):
            if qd.get(ct): return qd[ct]
            with st.spinner("IA..."):
                ck = qd.get('correct', 'A'); ctx = qd.get('options', {}).get(ck, "")
                p_map = {"theory": "Fiche Réflexe 4-5 phrases.", "example": "Scénario 4-5 lignes.", "tip": "Règle d'Or."}
                p = f"Q: {qd['question']} T: {p_map[ct]}"
                res, en = get_ai_service().get_response(p); st.session_state.current_engine = en
                if res:
                    res = res.replace("```", "").strip()
                    if qd.get('id'):
                        # Sécurisation : On valide le nom de la colonne
                        valid_cols = {"theory": "theory", "example": "example", "tip": "tip"}
                        col_name = valid_cols.get(ct)
                        if col_name:
                            run_query(f"UPDATE question_bank SET {col_name}=? WHERE id=?", (res, qd['id']), commit=True)
                    st.session_state.data[ct] = res; return res
            return "Indisponible."

        qh = hashlib.md5(q['question'].encode()).hexdigest()[:8]
        if st.button(t('next', lang), type="primary", use_container_width=True, key=f"nxt_{qh}"):
            st.session_state.data = None; st.session_state.mentor_message = ""; st.rerun()
        st.markdown("---")
        with st.expander("🛠️ Outils pédagogiques", expanded=True):
            c1, c2, c3 = st.columns(3)
            if f"st_{qh}" not in st.session_state: st.session_state[f"st_{qh}"] = st.session_state[f"se_{qh}"] = st.session_state[f"si_{qh}"] = False
            if c1.button("📘 Théorie", key=f"bt_{qh}", use_container_width=True): st.session_state[f"st_{qh}"] = not st.session_state[f"st_{qh}"]
            if c2.button("🏢 Exemple", key=f"be_{qh}", use_container_width=True): st.session_state[f"se_{qh}"] = not st.session_state[f"se_{qh}"]
            if c3.button("💡 Astuce", key=f"bi_{qh}", use_container_width=True): st.session_state[f"si_{qh}"] = not st.session_state[f"si_{qh}"]
            if st.session_state[f"st_{qh}"]: st.info(get_c(q, 'theory'))
            if st.session_state[f"se_{qh}"]: st.success(get_c(q, 'example'))
            if st.session_state[f"si_{qh}"]: st.warning(get_c(q, 'tip'))
        
        # --- NOUVEAU : VOTES DIFFICULTÉ ---
        st.write("<small>Cette question est :</small>", unsafe_allow_html=True)
        cv1, cv2, cv3 = st.columns([0.3, 0.3, 0.4])
        if cv1.button("🔥 Trop dure", key=f"hard_{qh}", use_container_width=True):
            engine.record_difficulty_vote(q['id'], "hard")
            st.toast("Merci ! L'IA va s'adapter.", icon="🧠")
        if cv2.button("✅ Trop facile", key=f"easy_{qh}", use_container_width=True):
            engine.record_difficulty_vote(q['id'], "easy")
            st.toast("Noté ! On va monter le niveau.", icon="📈")
            