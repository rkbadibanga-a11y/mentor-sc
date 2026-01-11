# services/document_parser.py
import os
import docx
import streamlit as st
from typing import Optional, Dict

@st.cache_data(ttl=3600)
def load_master_class(file_path: str, version: float = 1.0) -> Optional[Dict[str, Dict[str, str]]]:
    """Charge et parse le document Word avec filtrage strict 3.0 (Handling buffer_text)."""
    if not os.path.exists(file_path): return None
    
    try:
        doc = docx.Document(file_path)
        tree = {}
        cur_sess = "🚀 Introduction"
        cur_chap = "Sommaire"
        buffer_text = [] 
        
        for p in doc.paragraphs:
            text = p.text.strip()
            if not text: continue
            
            style = p.style.name
            upper = text.upper()
            
            # 1. DÉTECTION SESSION
            if style == "Heading 1" or "MASTER CLASS - SESSION" in upper:
                cur_sess = f"🎓 {text.replace('🎓', '').strip()}"
                cur_chap = "" 
                if cur_sess not in tree: tree[cur_sess] = {}
                continue

            # 2. DÉTECTION CHAPITRE (STRICT 3.0)
            elif upper.startswith("CHAPITRE"):
                is_pure_chapter = not any(word in upper for word in ["SOMMAIRE", "INTRODUCTION", "EXERCICE", "OBJECTIF", "CORRECTION", "PRÉSENTATION"])
                
                if is_pure_chapter:
                    cur_chap = text.replace(" :", " -").replace(":", " -").strip()
                    if cur_sess not in tree: tree[cur_sess] = {}
                    tree[cur_sess][cur_chap] = ""
                    
                    if buffer_text:
                        tree[cur_sess][cur_chap] += "\n\n".join(buffer_text) + "\n\n"
                        buffer_text = []
                else:
                    buffer_text.append(f"#### {text}")

            # 3. CONTENU
            else:
                if cur_sess and cur_chap:
                    prefix = "#### " if style.startswith("Heading") else ""
                    tree[cur_sess][cur_chap] += f"{prefix}{text}\n\n"
                else:
                    buffer_text.append(text)
        
        # Cleanup
        final_tree = {}
        for s, chaps in tree.items():
            valid = {k: v.strip() for k, v in chaps.items() if v.strip()}
            if valid: final_tree[s] = valid
        return final_tree
    except Exception as e:
        return ""