# services/ai_engine.py
import os
from typing import Optional, Tuple

class AIService:
    """Service IA optimisé pour la vitesse et la fiabilité séquentielle."""
    
    def _try_groq(self, prompt: str) -> Optional[str]:
        key = os.getenv("GROQ_API_KEY")
        if not key: return None
        try:
            import groq
            client = groq.Groq(api_key=key)
            # Timeout réduit pour éviter de bloquer l'UI trop longtemps
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                timeout=5
            )
            return res.choices[0].message.content
        except Exception as e:
            return None

    def _try_mistral(self, prompt: str) -> Optional[str]:
        key = os.getenv("MISTRAL_API_KEY")
        if not key: return None
        try:
            from mistralai import Mistral
            client = Mistral(api_key=key)
            res = client.chat.complete(
                model="mistral-large-latest", 
                messages=[{"role": "user", "content": prompt}]
            )
            return res.choices[0].message.content
        except Exception as e:
            return None

    def _try_gemini(self, prompt: str) -> Optional[str]:
        key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not key: return None
        try:
            import google.generativeai as genai
        except ImportError:
            return None

        # On tente plusieurs variantes de noms de modèles
        for model_name in ['gemini-1.5-flash', 'gemini-2.0-flash-exp', 'gemini-pro']:
            try:
                genai.configure(api_key=key)
                model = genai.GenerativeModel(model_name)
                res = model.generate_content(prompt)
                if res and res.text:
                    return res.text
            except Exception as e:
                continue # On tente le modèle suivant en cas d'erreur (404, 429, etc.)
        return None

    def get_response(self, prompt: str, preferred: str = "groq") -> Tuple[Optional[str], str]:
        """Tente les providers avec priorité absolue à Groq pour la vitesse."""
        
        # 1. Priorité Vitesse : Groq
        content = self._try_groq(prompt)
        if content: return content, "Groq"

        # 2. Fallback 1 : Gemini (souvent plus fiable que Mistral en gratuit)
        content = self._try_gemini(prompt)
        if content: return content, "Gemini"

        # 3. Fallback 2 : Mistral
        content = self._try_mistral(prompt)
        if content: return content, "Mistral"

        return None, "offline"

def get_ai_service():
    return AIService()