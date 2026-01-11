# services/news_service.py
import random
import streamlit as st
from duckduckgo_search import DDGS
from pathlib import Path
import pypdf
import docx

@st.cache_data(ttl=3600)
def get_supply_chain_news():
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text("Supply Chain Logistics News 2024", max_results=3))
        if results:
            return "\n".join([f"- {i['title']}" for i in results])
    except: return ""
    return ""

def process_uploaded_file(uploaded_file) -> str:
    """Extrait le texte d'un fichier téléchargé (PDF, CSV, TXT)."""
    if uploaded_file is None: return ""
    try:
        if uploaded_file.type == "application/pdf":
            reader = pypdf.PdfReader(uploaded_file)
            return "\n".join([page.extract_text() for page in reader.pages[:10]])
        elif uploaded_file.type == "text/csv":
            import pandas as pd
            df = pd.read_csv(uploaded_file)
            return df.head(50).to_markdown()
        else:
            return uploaded_file.read().decode("utf-8")
    except Exception as e:
        return f"Erreur lecture fichier : {str(e)}"

@st.cache_data(ttl=3600)
def get_local_pedagogical_context():
    """Scanne les fichiers PDF/Docx locaux pour nourrir l'IA."""
    base_dir = Path("Formation Supply Chain")
    if not base_dir.exists(): return ""
    txt = ""; files = list(base_dir.rglob("*.pdf")) + list(base_dir.rglob("*.docx"))
    if not files: return ""
    # On prend un échantillon plus large pour plus de pertinence
    for f in random.sample(files, min(len(files), 3)):
        try:
            if f.suffix == ".pdf": 
                txt += "\n".join([p.extract_text() for p in pypdf.PdfReader(f).pages[:5]])
            elif f.suffix == ".docx": 
                txt += "\n".join([p.text for p in docx.Document(f).paragraphs[:30]])
        except: pass
    return txt[:8000]
