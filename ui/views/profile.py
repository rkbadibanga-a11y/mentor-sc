# ui/views/profile.py
import streamlit as st
import json
import plotly.graph_objects as go
import datetime
from core.database import run_query
from services.ai_engine import get_ai_service
from services.certificate_factory import generate_certificate_pdf, get_base64_image, get_certificate_html
from core.config import t, ADMIN_EMAILS

def get_earned_badges_list(uid):
    """Calcule la liste des badges acquis selon les critères actuels."""
    qc = st.session_state.q_count
    lvl = st.session_state.level
    wins = st.session_state.get('consecutive_wins', 0)
    cw = st.session_state.get('crisis_wins', 0)
    rd = st.session_state.get('redemptions', 0)
    
    # Stats par catégorie
    d = dict(run_query('SELECT category, correct_count FROM stats WHERE user_id = ?', (uid,), fetch_all=True))
    
    # Nombre de termes dans le glossaire
    glossary_count_res = run_query('SELECT COUNT(*) FROM glossary WHERE user_id = ?', (uid,), fetch_one=True)
    glossary_count = glossary_count_res[0] if glossary_count_res else 0
    
    # Heure actuelle pour "Oiseau de Nuit"
    current_hour = datetime.datetime.now().hour
    is_night_owl = current_hour >= 22 or current_hour <= 6

    # Définition des badges et critères
    badges_criteria = [
        ("🔰", "Opérateur SC", qc >= 5),
        ("📦", "Resp. Exploitation", qc >= 120),
        ("🚚", "Coordinateur Flux", lvl >= 2),
        ("📊", "Planificateur Confirmé", qc >= 250),
        ("⚙️", "Ingénieur SC", lvl >= 3),
        ("🔮", "Data Strategist SC", qc >= 380),
        ("🏭", "COO (Directeur Ops)", lvl >= 4),
        ("👑", "Visionnaire SC", qc >= 500),
        ("💸", "Le Négociateur", d.get('Achats', 0) >= 10),
        ("🧊", "Gardien du Stock", d.get('Stocks', 0) >= 20),
        ("🚢", "Globe-Trotter", d.get('Transport', 0) >= 15),
        ("🤖", "Oracle Digital", d.get('IA & Data', 0) >= 15),
        ("🥋", "Sensei Lean", d.get('Stratégie Lean', 0) >= 15),
        ("🔥", "Maître du Chaos", cw >= 1),
        ("🔥", "On Fire", wins >= 10),
        ("🧟", "Le Survivant", rd >= 1),
        ("📚", "L'Encyclopédie", glossary_count >= 50),
        ("🦉", "Oiseau de Nuit", is_night_owl)
    ]
    
    earned = [title for (emoji, title, condition) in badges_criteria if condition]
    icons = {title: emoji for (emoji, title, condition) in badges_criteria}
    return earned, icons

def render_profile(uid: str):
    st.markdown("### 📊 Analyse des Compétences")
    
    # 1. Coaching IA
    stats_dict = dict(run_query('SELECT category, correct_count FROM stats WHERE user_id = ?', (uid,), fetch_all=True))
    
    if stats_dict:
        if 'daily_coaching' not in st.session_state:
            prompt = f"Rédige un diagnostic de carrière court (3 phrases) pour {st.session_state.user} basé sur ces stats: {json.dumps(stats_dict)}. Ton pro et visionnaire."
            res, _ = get_ai_service().get_response(prompt, preferred="mistral")
            st.session_state.daily_coaching = res
        
        st.markdown(f"""
            <div style='background: rgba(0, 124, 240, 0.05); border-left: 4px solid #007cf0; padding: 20px; border-radius: 10px; margin-bottom: 25px;'>
                <h4 style='color: #007cf0; margin-top: 0;'>🧠 Diagnostic du Mentor SC</h4>
                <p style='font-style: italic; color: #f1f5f9; line-height: 1.5;'>"{st.session_state.daily_coaching}"</p>
            </div>
        """, unsafe_allow_html=True)

    # 2. Radar
    # Mapping modules to core categories for the radar
    mapping = {
        'Achats': 'Achats',
        'Logistique': 'Logistique',
        'Transport': 'Transport',
        'Stocks': 'Stocks',
        'Digitalisation': 'Digitalisation',
        'Flux Connectés': 'Digitalisation',
        'IA & Data': 'Digitalisation',
        'Stratégie Lean': 'Stratégie',
        'Excellence Op': 'Stratégie',
        'Management': 'Stratégie'
    }
    
    radar_stats = {'Achats': 0, 'Logistique': 0, 'Transport': 0, 'Stocks': 0, 'Digitalisation': 0, 'Stratégie': 0}
    for cat, count in stats_dict.items():
        mapped_cat = mapping.get(cat, 'Logistique') # Default to Logistique if unknown
        if mapped_cat in radar_stats:
            radar_stats[mapped_cat] += count

    cats = list(radar_stats.keys())
    vals = list(radar_stats.values())
    
    if sum(vals) > 0:
        fig = go.Figure(data=go.Scatterpolar(r=vals, theta=cats, fill='toself', line_color='#00dfd8'))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, gridcolor="#334155"), angularaxis=dict(gridcolor="#334155")),
            showlegend=False, 
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)', 
            font_color="white", 
            height=350,
            margin=dict(l=80, r=80, t=40, b=40)
        )
        st.plotly_chart(fig, use_container_width=True)

    # 3. Badges
    st.markdown("---")
    st.markdown("### 🏅 Vos Badges Experts")
    earned_titles, icons = get_earned_badges_list(uid)
    
    groups = [
        ("📈 Rangs de Carrière", [
            ("🔰", "Opérateur SC", "5 questions"), ("📦", "Resp. Exploitation", "Niv 1"),
            ("🚚", "Coordinateur Flux", "Niv 2 atteint"), ("📊", "Planificateur Confirmé", "Niv 2 fini"),
            ("⚙️", "Ingénieur SC", "Niv 3 atteint"), ("🔮", "Data Strategist SC", "Niv 3 fini"),
            ("🏭", "COO (Directeur Ops)", "Niv 4 atteint"), ("👑", "Visionnaire SC", "Titre Ultime")
        ]),
        ("🎯 Spécialisations", [
            ("💸", "Le Négociateur", "10 Achats"), ("🧊", "Gardien du Stock", "20 Stocks"),
            ("🚢", "Globe-Trotter", "Expert Transport"), ("🤖", "Oracle Digital", "Maître IA"),
            ("🥋", "Sensei Lean", "Expert Lean"), ("🔥", "Maître du Chaos", "1ère Crise maîtrisée")
        ]),
        ("🎮 Gameplay", [
            ("🔥", "On Fire", "10 victoires"), ("🧟", "Le Survivant", "1 Rédemption"),
            ("📚", "L'Encyclopédie", "50 termes"), ("🦉", "Oiseau de Nuit", "Session nocturne")
        ])
    ]
    
    for section_title, badge_list in groups:
        st.markdown(f"#### {section_title}")
        cols = st.columns(4)
        for i, (emoji, title, desc) in enumerate(badge_list):
            is_earned = title in earned_titles
            with cols[i % 4]:
                if is_earned:
                    st.markdown(f"""
                        <div style='text-align:center; padding:10px; border:2px solid #00dfd8; border-radius:12px; background:rgba(0,223,216,0.1); margin-bottom:10px;'>
                            <h3 style='margin:0;'>{emoji}</h3>
                            <b style='font-size:0.8rem;'>{title}</b><br>
                            <small style='color:#94a3b8;'>{desc}</small>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                        <div style='text-align:center; padding:10px; border:1px solid #334155; border-radius:12px; opacity:0.2; margin-bottom:10px;'>
                            <h3 style='margin:0;'>{emoji}</h3>
                            <b style='font-size:0.8rem;'>{title}</b><br>
                            <small>{desc}</small>
                        </div>
                    """, unsafe_allow_html=True)

    # 4. Diplôme (Si acquis)
    if st.session_state.get('has_diploma'):
        st.markdown("---")
        st.markdown("### 🎓 Votre Certification")
        c1, c2 = st.columns([0.6, 0.4])
        
        name = st.session_state.user
        date_str = datetime.datetime.now().strftime("%d/%m/%Y")
        base_path = "certificat"
        
        with c1:
            st.success("Vous avez complété l'intégralité du cursus Elite Supply Chain.")
            pdf_data = generate_certificate_pdf(name, date_str, f"{base_path}/fond-certificat-pdf.jpg")
            if pdf_data:
                st.download_button("📥 Télécharger mon Diplôme (PDF)", data=pdf_data, file_name=f"Certificat_SC_{name}.pdf", mime="application/pdf", use_container_width=True)
        
        with c2:
            img_b64 = get_base64_image(f"{base_path}/fond-certificat.jpg")
            st.components.v1.html(get_certificate_html(name, date_str, img_b64), height=300)

    # Zone de test pour forcer l'obtention (Réservé Admin)
    # Liste des pseudos admins
    ADMIN_PSEUDOS = ["Diplome", "Mentor", "Admin"]
    
    if st.session_state.user in ADMIN_PSEUDOS:
        with st.expander("🛠️ Zone Admin (Test)"):
            if st.button("Débloquer Certificat (Test)"):
                # Simulation de l'attente / calcul
                with st.spinner("Vérification des accréditations académiques en cours... (5s)"):
                    time.sleep(5)
                
                st.session_state.has_diploma = True
                st.session_state.show_diploma = True # Déclenche l'animation
                run_query("UPDATE users SET has_diploma=1 WHERE user_id=?", (st.session_state.user_id,), commit=True)
                st.rerun()