# services/certificate_factory.py
import io
import base64
import datetime
from pathlib import Path
import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageChops
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

@st.cache_data
def get_base64_image(img_path):
    try:
        with open(img_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return ""

@st.cache_data
def generate_certificate_image(name, date_str, template_path):
    try:
        base_img = Image.open(template_path).convert("RGB")
        W, H = base_img.size
        text_layer = Image.new("RGB", base_img.size, (255, 255, 255))
        draw = ImageDraw.Draw(text_layer)
        sepia_ink = (62, 39, 35)
        
        try:
            base_path = Path(__file__).parent.parent / "certificat"
            font_path = str(base_path / "GreatVibes-Regular.ttf")
            font_name = ImageFont.truetype(font_path, 260) 
            
            # Utilisation de polices standard ou fallbacks pour Linux/Cloud
            try:
                font_body = ImageFont.truetype("DejaVuSans-Bold.ttf", 65)
                font_small = ImageFont.truetype("DejaVuSans.ttf", 45)
            except:
                font_body = ImageFont.truetype("LiberationSans-Bold.ttf", 65)
                font_small = ImageFont.truetype("LiberationSans.ttf", 45)
        except:
            font_name = font_body = font_small = ImageFont.load_default()

        draw.text((W * 0.5, H * 0.45), name, fill=sepia_ink, font=font_name, anchor="mm")
        draw.text((W * 0.5, H * 0.673), "Score global : EXCELLENT", fill=(0,0,0), font=font_body, anchor="mm")
        draw.text((W * 0.227, H * 0.85), date_str, fill=(0,0,0), font=font_small, anchor="ls")
        
        final_img = ImageChops.multiply(base_img, text_layer)
        
        # Effet incliné pour la version écran
        final_img = final_img.convert("RGBA").rotate(7.4, resample=Image.BICUBIC, center=(W/2, H/2)).convert("RGB")
        
        buf = io.BytesIO()
        final_img.save(buf, format="JPEG", quality=95)
        return buf.getvalue()
    except Exception as e:
        st.error(f"Erreur image : {e}")
        return None

@st.cache_data
def generate_certificate_pdf(name, date_str, template_path):
    try:
        packet = io.BytesIO()
        c = canvas.Canvas(packet, pagesize=landscape(A4))
        width, height = landscape(A4)
        c.drawImage(template_path, 0, 0, width=width, height=height)

        try:
            base_path = Path(__file__).parent.parent / "certificat"
            font_path = str(base_path / "GreatVibes-Regular.ttf")
            pdfmetrics.registerFont(TTFont('ScriptFont', font_path))
            font_nom = "ScriptFont"
        except:
            font_nom = "Helvetica-Bold"

        c.setFont(font_nom, 65) 
        c.setFillColorRGB(0.25, 0.15, 0.10)
        c.drawCentredString(width / 2, height - 268, name)
        
        c.setFont("Helvetica-Bold", 14)
        c.setFillColorRGB(0, 0, 0)
        c.drawCentredString(width / 2, height - 400, "Score global : EXCELLENT")
        
        c.setFont("Helvetica-Bold", 13)
        c.drawString(191, 81, date_str)
        
        c.save()
        return packet.getvalue()
    except Exception as e:
        st.error(f"Erreur PDF : {e}")
        return None

def get_certificate_html(name, date_str, img_b64):
    return f"""
    <style>
        .certificate-wrapper {{ position: relative; width: 100%; display: flex; justify-content: center; padding: 20px; box-sizing: border-box; }}
        .inner-container {{ position: relative; width: 100%; max-width: 800px; box-shadow: 0 15px 40px rgba(0,0,0,0.6); border-radius: 15px; overflow: hidden; }}
        .certificate-img {{ width: 100%; height: auto; display: block; }}
        .name-overlay {{ position: absolute; top: 40%; left: 50%; width: 90%; text-align: center; transform: translate(-50%, -50%) rotate(7.4deg); font-family: cursive; font-size: 4.5vw; color: #3E2723; mix-blend-mode: multiply; pointer-events: none; }}
        .date-overlay {{ position: absolute; bottom: 30%; left: 30%; transform: translate(-50%, 0) rotate(7.4deg); font-weight: bold; font-size: 1.1vw; color: #2F1B10; mix-blend-mode: multiply; pointer-events: none; }}
    </style>
    <div class="certificate-wrapper">
        <div class="inner-container">
            <img src="data:image/jpeg;base64,{img_b64}" class="certificate-img">
            <div class="name-overlay">{name}</div>
            <div class="date-overlay">{date_str}</div>
        </div>
    </div>
    """

@st.dialog("FÉLICITATIONS ! 🎓", width="large")
def show_diploma_celebration():
    from utils.assets import play_sfx
    st.balloons()
    play_sfx("victory")
    
    name = st.session_state.user
    date_str = datetime.datetime.now().strftime("%d/%m/%Y")
    base_path = Path(__file__).parent.parent / "certificat"
    
    st.markdown(f"""
        <div style='text-align: center; margin-bottom: 20px;'>
            <h2 style='color: #00dfd8;'>Légendaire, {name} ! 🏆</h2>
            <p>Vous rejoignez le cercle des Visionnaires Supply Chain.</p>
        </div>
    """, unsafe_allow_html=True)
    
    img_b64 = get_base64_image(str(base_path / "fond-certificat.jpg"))
    st.components.v1.html(get_certificate_html(name, date_str, img_b64), height=600)
    
    pdf_data = generate_certificate_pdf(name, date_str, str(base_path / "fond-certificat-pdf.jpg"))
    if pdf_data:
        st.download_button("TÉLÉCHARGER MON DIPLÔME (PDF) 📥", data=pdf_data, file_name=f"Certificat_SC_{name}.pdf", use_container_width=True)
    
    if st.button("Continuer vers mon profil 🚀", type="secondary", use_container_width=True):
        st.session_state.show_diploma = False
        st.session_state.active_tab = "profile"
        st.rerun()
