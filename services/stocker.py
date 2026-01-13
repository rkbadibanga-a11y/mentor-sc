# services/stocker.py
import os
import sys
from pathlib import Path

# Ajouter le chemin racine pour l'import des modules
root_path = str(Path(__file__).parent.parent)
if root_path not in sys.path:
    sys.path.append(root_path)

import streamlit as st
import json
import time
from services.quiz_engine import QuizEngine
from core.config import CURRICULUM
from core.database import run_query

def stock_database():
    engine = QuizEngine()
    print("🚀 Démarrage du stockage massif de questions (X3)...")
    
    # On boucle sur tous les niveaux et modules
    for lvl, modules in CURRICULUM.items():
        for mod_name, _ in modules:
            print(f"📦 Module: {mod_name} (Niveau {lvl})")
            
            # On génère 5 triades (15 questions) par module pour commencer
            for i in range(5):
                print(f"  - Génération triade {i+1}/5...")
                batch, status = engine._generate_single_batch(lvl, mod_name, "Admin", 0, 0)
                
                if batch and status != "error":
                    triad_id = f"STOCK_{int(time.time())}_{i}"
                    for pos, q in enumerate(batch):
                        run_query(
                            'INSERT INTO question_bank (category, concept, level, question, options, correct, explanation, triad_id, triad_position) VALUES (?,?,?,?,?,?,?,?,?)',
                            (q.get('category', mod_name), q.get('concept_key',''), lvl, q['question'], json.dumps(q['options']), q['correct'], q['explanation'], triad_id, pos+1), 
                            commit=True
                        )
                    print(f"  ✅ Triade insérée.")
                else:
                    print(f"  ❌ Erreur génération : {status}")
                
                time.sleep(1) # Sécurité API

    print("🎯 Stockage terminé !")

if __name__ == "__main__":
    stock_database()
