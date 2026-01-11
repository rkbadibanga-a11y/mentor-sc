# ui/views/notes.py
import streamlit as st
import uuid
import datetime
import pandas as pd
from core.database import run_query

def render_notes(uid: str):
    st.markdown("### 📝 Mes Notes Personnalisées")
    
    col_t, col_ex = st.columns([0.7, 0.3])
    
    # Fetch notes
    user_notes = run_query('SELECT note_id, title, content, timestamp FROM notes WHERE user_id = ? ORDER BY timestamp DESC', (uid,), fetch_all=True)
    
    # Export
    if user_notes:
        df_notes = pd.DataFrame(user_notes, columns=['ID', 'Titre', 'Contenu', 'Date'])
        csv = df_notes.to_csv(index=False).encode('utf-8')
        col_ex.download_button("📥 Exporter CSV", data=csv, file_name="mes_notes_sc.csv", mime="text/csv", use_container_width=True)

    # Add new note
    with st.expander("➕ Ajouter une nouvelle note", expanded=False):
        title = st.text_input("Titre")
        content = st.text_area("Contenu")
        if st.button("Enregistrer"):
            if title and content:
                nid = str(uuid.uuid4())
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                run_query('INSERT INTO notes (user_id, note_id, title, content, timestamp) VALUES (?, ?, ?, ?, ?)', 
                         (uid, nid, title, content, now))
                st.success("Note enregistrée !")
                st.rerun()

    st.markdown("---")
    
    if not user_notes:
        st.info("Utilisez le formulaire ci-dessus pour créer votre première note.")
        return

    for nid, title, content, ts in user_notes:
        with st.container():
            c_main, c_actions = st.columns([0.8, 0.2])
            with c_main:
                st.markdown(f"#### {title}")
                st.caption(f"📅 {ts}")
                with st.expander("📄 Lire la note"):
                    st.write(content)
            
            with c_actions:
                col_del, col_edit = st.columns(2)
                if col_del.button("🗑️", key=f"del_{nid}"):
                    run_query('DELETE FROM notes WHERE note_id = ?', (nid,))
                    st.rerun()
                edit_mode = col_edit.toggle("✏️", key=f"tog_{nid}")

            if edit_mode:
                with st.form(f"edit_{nid}"):
                    new_title = st.text_input("Titre", value=title)
                    new_content = st.text_area("Contenu", value=content)
                    if st.form_submit_button("Mettre à jour"):
                        run_query('UPDATE notes SET title=?, content=?, timestamp=? WHERE note_id=?', 
                                 (new_title, new_content, datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), nid))
                        st.success("Note mise à jour !")
                        st.rerun()
            st.markdown("<br>", unsafe_allow_html=True)
