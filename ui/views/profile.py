# ui/views/profile.py
import streamlit as st
import json
import plotly.graph_objects as go
import datetime
from core.database import run_query
from services.ai_engine import get_ai_service
from services.certificate_factory import generate_certificate_pdf, get_base64_image, get_certificate_html
from core.config import t, ADMIN_EMAILS
from core.badges import calculate_badges, get_badge_groups

def get_earned_badges_list(uid):
    """Calcule la liste des badges acquis via le service centralisé."""
    earned, metadata = calculate_badges(uid)
    icons = {title: data['emoji'] for title, data in metadata.items()}
    return earned, icons

def render_profile(uid: str):
    st.markdown("### 📊 Analyse des Compétences")
    
    # 1. Stats Data Retrieval
    stats_dict = dict(run_query('SELECT category, correct_count FROM stats WHERE user_id = ?', (uid,), fetch_all=True))

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
    
    groups = get_badge_groups()
    
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
            pdf_data = generate_certificate_pdf(name, date_str, f"{base_path}/fond-certificat-pdf.webp")
            if pdf_data:
                st.download_button("📥 Télécharger mon Diplôme (PDF)", data=pdf_data, file_name=f"Certificat_SC_{name}.pdf", mime="application/pdf", use_container_width=True)
        
        with c2:
            img_b64 = get_base64_image(f"{base_path}/fond-certificat.webp")
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