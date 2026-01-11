# ui/styles.py
import streamlit as st
from core.config import COLORS

def apply_styles():
    st.markdown(f"""
    <style>
        .stApp {{ 
            background: radial-gradient(circle at top right, #1e293b, #0f172a); 
            color: {COLORS['text']}; 
            padding-bottom: 120px; 
        }}
        
        /* SIDEBAR OPAQUE */
        section[data-testid="stSidebar"] {{ 
            background-color: #0f172a !important; 
            border-right: 1px solid #334155;
            z-index: 99999999 !important; 
            opacity: 1 !important;
        }}
        
        /* CARDS & BOXES */
        .question-box {{ 
            background: {COLORS['card_bg']}; 
            backdrop-filter: blur(12px); 
            padding: 30px; 
            border-radius: 15px; 
            border-left: 5px solid {COLORS['secondary']}; 
            margin-bottom: 20px; 
            font-size: 1.35rem; 
            font-weight: 600; 
            line-height: 1.5;
        }}

        /* BUTTONS STYLING */
        div.stButton > button {{
            background: rgba(30, 41, 59, 0.7); 
            border: 1px solid #334155; 
            color: #f1f5f9; 
            border-radius: 12px;
            font-weight: 500;
            transition: all 0.2s ease-in-out !important;
        }}
        
        div.stButton > button:hover {{
            border-color: {COLORS['primary']};
            color: {COLORS['primary']};
            background: rgba(0, 223, 216, 0.05);
        }}

        /* PRIMARY BUTTON (SUIVANT) */
        div.stButton > button[kind="primary"] {{
            background: linear-gradient(90deg, #00dfd8 0%, #007cf0 100%) !important;
            border: none !important;
            color: #0f172a !important; 
            font-weight: 800 !important;
            letter-spacing: 1px;
            text-transform: uppercase;
            box-shadow: 0 4px 15px rgba(0, 223, 216, 0.4);
        }}
        div.stButton > button[kind="primary"]:hover {{
            box-shadow: 0 6px 20px rgba(0, 223, 216, 0.6);
            transform: scale(1.02);
        }}

        /* PEDAGOGICAL BUTTONS IN EXPANDER */
        div[data-testid="stExpander"] div.stButton > button {{
            background: rgba(99, 102, 241, 0.15) !important;
            border: 1px solid #6366f1 !important;
            color: #a5b4fc !important;
            font-size: 0.9rem;
        }}

        /* ANIMATIONS */
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        @keyframes shake {{
            0%, 100% {{ transform: translateX(0); }}
            25% {{ transform: translateX(-10px); }}
            75% {{ transform: translateX(10px); }}
        }}
        .fade-in {{ animation: fadeIn 0.5s ease-out forwards; }}
        .shake {{ animation: shake 0.3s ease-in-out 2; border-left: 5px solid {COLORS['error']} !important; }}

        /* FOOTER */
        .mentor-footer {{
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            height: 100px;
            background: rgba(15, 23, 42, 0.9);
            border-top: 1px solid rgba(0, 223, 216, 0.3);
            z-index: 9999 !important;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 0 20px;
            backdrop-filter: blur(10px);
        }}
        .mentor-avatar {{ 
            font-size: 45px; 
            margin-right: 20px; 
            animation: bounce 2s infinite; 
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .mentor-bubble {{ 
            background: rgba(30, 41, 59, 0.8); 
            border: 1px solid rgba(51, 65, 85, 0.5); 
            padding: 12px 20px; 
            border-radius: 15px 15px 15px 0; 
            max-width: 70%; 
            color: #e2e8f0;
            font-size: 0.95rem;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }}
        @keyframes bounce {{ 0%, 100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-5px); }} }}

        /* PILLS / NAVIGATION */
        div[data-testid="stPills"] {{
            display: flex;
            justify-content: flex-start;
            gap: 8px;
        }}
        div[data-testid="stPills"] button {{
            background: rgba(30, 41, 59, 0.5) !important;
            border: 1px solid #334155 !important;
            color: #94a3b8 !important;
            transition: all 0.3s ease !important;
        }}
        div[data-testid="stPills"] button[aria-selected="true"] {{
            background: rgba(0, 223, 216, 0.1) !important;
            border: 1px solid {COLORS['primary']} !important;
            color: {COLORS['primary']} !important;
            box-shadow: 0 0 15px rgba(0, 223, 216, 0.3);
        }}

        /* HIDE AUDIO PLAYERS */
        div[data-testid="stAudio"] {{
            display: none !important;
        }}
        
        .signature {{ 
            text-align: center; 
            color: #64748b; 
            font-size: 0.75rem; 
            margin-top: 50px; 
            line-height: 1.4;
        }}
    </style>
    """, unsafe_allow_html=True)