# ui/views/glossary.py
import streamlit as st
import pandas as pd
import json
import time
from core.database import run_query
from services.ai_engine import get_ai_service
from utils.assets import play_sfx

def render_glossary(uid: str):
    st.markdown("### 📖 Glossaire Visionnaire")
    
    # 1. Fetch data
    all_terms = run_query('SELECT term, definition, category, use_case, business_impact, short_definition FROM glossary WHERE user_id = ? ORDER BY term ASC', (uid,), fetch_all=True)
    
    if not all_terms:
        st.info("Validez des concepts en répondant aux questions pour bâtir votre glossaire.")
        return

    # Export
    col_t, col_ex = st.columns([0.7, 0.3])
    df_gl = pd.DataFrame(all_terms, columns=['Terme', 'Définition', 'Domaine', 'Cas Usage', 'Impact', 'Résumé'])
    csv = df_gl.to_csv(index=False, sep=';').encode('utf-8')
    col_ex.download_button("📥 Export CSV", data=csv, file_name="glossaire_sc.csv", mime="text/csv", use_container_width=True)

    # 2. Filters
    c1, c2 = st.columns([0.6, 0.4])
    cats = sorted(list(set([row[2] for row in all_terms if row[2]])))
    sel_cat = c1.selectbox("📁 Filtrer par Domaine", ["Tous"] + cats)
    search_term = c2.text_input("🔍 Rechercher", placeholder="Ex: Bullwhip...")

    # Filter logic
    filtered = [row for row in all_terms if (sel_cat == "Tous" or row[2] == sel_cat)]
    if search_term:
        filtered = [row for row in filtered if search_term.lower() in row[0].lower() or search_term.lower() in row[1].lower()]

    st.markdown(f"<small>{len(filtered)} concepts experts répertoriés</small>", unsafe_allow_html=True)
    st.markdown("---")

    # 3. List terms
    for term, definition, cat, use_case, impact, short_def in filtered:
        with st.container():
            col_main, col_actions = st.columns([0.8, 0.2])
            with col_main:
                cat_label = cat if cat else "GÉNÉRAL"
                st.markdown(f"""
                    <div style="margin-bottom: 5px;">
                        <span style="font-size: 0.6rem; background: rgba(0, 124, 240, 0.2); color: #007cf0; padding: 2px 6px; border-radius: 4px; font-weight: bold;">{cat_label}</span>
                        <b style="color: #00dfd8; font-size: 1.1rem; margin-left: 8px;">{term}</b>
                    </div>
                """, unsafe_allow_html=True)
                
                with st.expander(short_def if short_def else "Voir les détails"):
                    st.write(definition)
                    if use_case: st.info(f"**🏢 Usage :** {use_case}")
                    if impact: st.warning(f"**💰 Impact :** {impact}")
            
            with col_actions:
                ca, ce, cd = st.columns(3)
                
                # TTS
                if ca.button("🔊", key=f"tts_{term}", help="Écouter"):
                    play_sfx("click")
                    st.components.v1.html(f"<script>const u=new SpeechSynthesisUtterance({json.dumps(term+'. '+definition)}); u.lang='fr-FR'; window.speechSynthesis.speak(u);</script>", height=0)
                
                # EDIT
                with ce.popover("✏️"):
                    with st.form(key=f"edit_gl_{term}"):
                        new_term = st.text_input("Terme", value=term)
                        new_short = st.text_input("Résumé", value=short_def if short_def else "")
                        new_def = st.text_area("Définition", value=definition, height=80)
                        new_case = st.text_area("Cas", value=use_case if use_case else "")
                        new_imp = st.text_area("Impact", value=impact if impact else "")
                        if st.form_submit_button("OK"):
                            run_query('UPDATE glossary SET term=?, definition=?, use_case=?, business_impact=?, short_definition=? WHERE term=? AND user_id=?', 
                                     (new_term, new_def, new_case, new_imp, new_short, term, uid), commit=True)
                            st.rerun()

                # DELETE
                if cd.button("✕", key=f"del_{term}", help="Supprimer"):
                    run_query('DELETE FROM glossary WHERE term = ? AND user_id = ?', (term, uid), commit=True)
                    st.rerun()

            st.markdown("<hr style='margin: 10px 0; opacity: 0.1;'>", unsafe_allow_html=True)

    # 4. Advanced Tools
    with st.expander("⚙️ Outils avancés"):
        if st.button("✨ ENRICHIR TOUS LES CONCEPTS VIDES (Batch de 5)", use_container_width=True):
            missing = run_query("SELECT term FROM glossary WHERE (use_case IS NULL OR use_case = '') AND user_id = ? LIMIT 5", (uid,), fetch_all=True)
            if missing:
                count = len(missing)
                progress_bar = st.progress(0)
                for i, (m_term,) in enumerate(missing):
                    with st.spinner(f"Analyse IA : {m_term}..."):
                        prompt = f"Rédige une définition technique, un résumé de 5 mots, un cas d'usage et l'impact business pour le terme SC : {m_term}. Répond au format JSON: {{\"short_def\": \"...\", \"def\": \"...\", \"use_case\": \"...\", \"impact\": \"...\"}}"
                        res, _ = get_ai_service().get_response(prompt)
                        if res:
                            try:
                                clean_res = res.strip()
                                if "```" in clean_res: clean_res = clean_res.split("```")[1].replace("json", "").strip()
                                d = json.loads(clean_res)
                                run_query('UPDATE glossary SET definition=?, use_case=?, business_impact=?, short_definition=? WHERE term=? AND user_id=?', 
                                         (d.get('def', ''), d.get('use_case', ''), d.get('impact', ''), d.get('short_def', ''), m_term, uid), commit=True)
                            except: pass
                    progress_bar.progress((i + 1) / count)
                st.success("Batch terminé !")
                st.rerun()
            else:
                st.info("Tous les termes sont déjà enrichis.")
