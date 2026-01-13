# core/config.py
import os
from pathlib import Path

# --- APP CONFIG ---
ROOT_DIR = Path(__file__).parent.parent
APP_TITLE = "Mentor SC"
APP_ICON = "📦"
DB_FILE = str(ROOT_DIR / 'mentor_sc_v8.db')
ADMIN_EMAILS = ["admin@mentor-sc.com", "test@test.com", "r.k.badibanga@gmail.com", "mentor.sc.app@gmail.com"]
LEVEL_THRESHOLDS = {1: 0, 2: 120, 3: 250, 4: 380, 5: 500}

# --- DESIGN SYSTEM ---
COLORS = {
    "primary": "#00dfd8",
    "secondary": "#007cf0",
    "background": "#0d1117",
    "card_bg": "rgba(255, 255, 255, 0.03)",
    "text": "#f1f5f9",
    "success": "#10b981",
    "error": "#ef4444"
}

LOTTIE_URLS = {
    "levelup": "https://assets5.lottiefiles.com/packages/lf20_j1adxtyb.json",
    "new_module": "https://assets2.lottiefiles.com/packages/lf20_w51pcehl.json",
    "trophy": "https://assets10.lottiefiles.com/packages/lf20_xlkxtmul.json",
    "balloons": "https://assets5.lottiefiles.com/packages/lf20_j1adxtyb.json",
    "success": "https://assets9.lottiefiles.com/packages/lf20_qpwbv5gm.json",
    "failed": "https://assets10.lottiefiles.com/packages/lf20_p49fxj.json",
    "crisis_win": "https://assets5.lottiefiles.com/packages/lf20_j1adxtyb.json"
}

# --- PERSONA ---
SYSTEM_PROMPT = """
Tu es Mentor SC, un expert vétéran de la Supply Chain (type VP Opérations) devenu coach.
Ton objectif : Faire progresser l'utilisateur.
PERSONNALITÉ : Direct, Business, Sarcastique mais bienveillant.
RÈGLES : Concision (max 2 phrases). Utilise des emojis (📦, 🚢). Si l'utilisateur échoue, chambre-le un peu. Si succès, félicite pro.
"""

MENTOR_AVATARS = {
    "happy": "https://lottie.host/f94147eb-075e-4777-bead-4573d6b05721/HuK8f57s5z.json",
    "sad": "https://lottie.host/9e019323-9658-4673-86f7-307775550176/P655606575.json",
    "neutral": "https://lottie.host/02055606-5606-4606-9606-655606660660/bot.json",
    "working": "https://lottie.host/56060606-5606-4606-9606-655606660660/loading.json"
}

MENTOR_REACTIONS = {
    "WIN": {
        "default": [
            "Propre. Efficace. Next.", "C'est validé. On avance.", "KPI au vert. Tu gères.",
            "Fluide comme un flux tendu.", "Pas de gaspillage, réponse nette.", "Validé par la Direction.",
            "Tu commences à penser comme un OPS.", "Rendement 100%.", "C'est carré.", "Lead-time respecté."
        ],
        "level_1": [ # Débutant
            "Bonne base. Continue.", "Tu as le vocabulaire, c'est un début.", "Pas mal pour un stagiaire.",
            "Tu commences à comprendre le jargon.", "Validé. Ne prends pas la grosse tête."
        ],
        "level_4": [ # Expert
            "Vision stratégique validée.", "Excellence opérationnelle atteinte.", "C'est du niveau CODIR.",
            "Optimisation de marge confirmée.", "Tu pourrais enseigner ça.", "Mastery total."
        ],
        "Achats": [
            "Fournisseur sécurisé.", "TCO optimisé.", "Négociation réussie.", "Le sourcing est bon.", "Marge sécurisée."
        ],
        "Transport": [
            "Livré à l'heure.", "Dernier kilomètre maîtrisé.", "Camion plein, rentabilité max.", "Incoterm validé."
        ],
        "Stocks": [
            "Rotation parfaite.", "Pas de dormant ici.", "Inventaire juste.", "Stock de sécu intact."
        ]
    },
    "LOSS": {
        "default": [
            "Rupture de stock sur tes connaissances.", "C'est un goulot d'étranglement.", "Non conforme.",
            "Retour fournisseur immédiat.", "Tu creuses ta marge là.", "C'est un coût caché.",
            "Refusé par le client.", "Qualité insuffisante.", "Revois tes process.", "Lead-time explosé."
        ],
        "level_1": [
            "Relis tes définitions.", "C'est la base, concentre-toi.", "Erreur de débutant acceptée (une fois).",
            "C'est flou. La Supply Chain c'est précis.", "Va falloir bosser tes fiches."
        ],
        "level_4": [
            "Inacceptable à ce niveau de salaire.", "Tu vas couler la boîte avec ça.", "Erreur stratégique majeure.",
            "Le CODIR ne validera jamais ça.", "C'est une faute professionnelle là."
        ],
        "Achats": [
            "Tu achètes trop cher.", "Le fournisseur t'a eu.", "Contrat mal blindé.", "Rupture d'approvisionnement."
        ],
        "Transport": [
            "Camion vide = argent perdu.", "Retard de livraison client.", "Litige transporteur en vue.", "Mauvais Incoterm."
        ],
        "Stocks": [
            "Surstock ! Le cash dort.", "Rupture ligne de prod.", "Écart d'inventaire.", "Obsolescence programmée."
        ]
    }
}

MENTOR_QUOTES = MENTOR_REACTIONS # Alias pour compatibilité

CURRICULUM = {
    1: [("Fondamentaux", 40), ("Logistique", 40), ("Achats", 40)],
    2: [("Planification", 40), ("Stocks", 40), ("Transport", 50)],
    3: [("Digitalisation", 40), ("Flux Connectés", 40), ("IA & Data", 50)],
    4: [("Stratégie Lean", 40), ("Excellence Op", 40), ("Management", 40)]
}

TRANSLATIONS = {
    "Français": {
        "settings": "⚙️ Paramètres", "my_profile": "👤 Mon Profil", "appearance": "🎨 Apparence", "language": "🌐 Langue", 
        "ai_level": "🧠 IA", "welcome": "Votre accélérateur Supply Chain IA. 🚀", "login_btn": "CONNEXION 🔒", 
        "new_account": "🆕 Nouveau compte", "validate": "VALIDER ✨", "mission": "🎯 Mission", "profile": "📊 Profil", 
        "glossary": "📖 Glossaire", "notes": "📝 Notes", "badges": "🏅 Badges", "mastery": "Maîtrise", "lives": "Stock", 
        "heal": "❤️ Réapprovisionnement (100 XP)", "experts": "🏆 Top Experts", "logout": "🚪 Déconnexion", 
        "purge": "🗑️ Purge", "next": "SUIVANT ➡️", "theory": "📘 Théorie", "example": "🏢 Exemple", 
        "trick": "💡 Astuce", "joker": "⏭️ JOKER", "joker_out": "⏭️ VIDE", "correct": "✅ CORRECT !", "wrong": "❌ ERREUR."
    },
    "English": {
        "settings": "⚙️ Settings", "my_profile": "👤 My Profile", "appearance": "🎨 Appearance", "language": "🌐 Language", 
        "ai_level": "🧠 AI Level", "welcome": "Your AI Supply Chain Accelerator. 🚀", "login_btn": "SECURE LOGIN 🔒", 
        "new_account": "🆕 New Account", "validate": "VALIDATE ✨", "mission": "🎯 Mission", "profile": "📊 Profile", 
        "glossary": "📖 Glossary", "notes": "📝 Notes", "badges": "🏅 Badges", "mastery": "Mastery", "lives": "Stock", 
        "heal": "❤️ Restock (100 XP)", "experts": "🏆 Top Experts", "logout": "🚪 Logout", 
        "purge": "🗑️ Purge", "next": "NEXT ➡️", "theory": "📘 Theory", "example": "🏢 Example", 
        "trick": "💡 Tip", "joker": "⏭️ SKIP", "joker_out": "⏭️ EMPTY", "correct": "✅ CORRECT!", "wrong": "❌ WRONG."
    },
    "Español": {
        "settings": "⚙️ Ajustes", "my_profile": "👤 Mi Perfil", "appearance": "🎨 Apariencia", "language": "🌐 Idioma", 
        "ai_level": "🧠 Nivel IA", "welcome": "Tu acelerador Supply Chain IA. 🚀", "login_btn": "LOGIN SEGURO 🔒", 
        "new_account": "🆕 Nueva cuenta", "validate": "VALIDAR ✨", "mission": "🎯 Misión", "profile": "📊 Perfil", 
        "glossary": "📖 Glosario", "notes": "📝 Notas", "badges": "🏅 Insignias", "mastery": "Maîtrise", "lives": "Stock", 
        "heal": "❤️ Reabastecimiento (100 XP)", "experts": "🏆 Top Expertos", "logout": "🚪 Salir", 
        "purge": "🗑️ Borrar", "next": "SIGUIENTE ➡️", "theory": "📘 Teoría", "example": "🏢 Ejemplo", 
        "trick": "💡 Truco", "joker": "⏭️ COMODÍN", "joker_out": "⏭️ VACÍO", "correct": "✅ ¡CORRECTO!", "wrong": "❌ ERROR."
    }
}

def t(key, lang="Français"):
    return TRANSLATIONS.get(lang, TRANSLATIONS['Français']).get(key, key)

SIGNATURE = """
<div class='signature'>
    Developed with ❤️<br>
    by <a href='https://www.linkedin.com/in/romainbadibanga/' style='color:#007cf0; text-decoration: none;'>Romain Badibanga</a>
</div>
"""
