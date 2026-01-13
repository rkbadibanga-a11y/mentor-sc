# services/email_service.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

def send_email_notification(subject, body):
    """Envoie un email via SMTP Gmail."""
    # Rechargement forcé pour être sûr
    from dotenv import load_dotenv
    load_dotenv(override=True)
        
    sender_email = "r.k.badibanga@gmail.com"
    app_password = os.getenv("GMAIL_APP_PASSWORD")
    
    if app_password:
        app_password = app_password.replace(" ", "").strip()
    
    receiver_email = "r.k.badibanga@gmail.com"

    if not app_password:
        return False, "Clé GMAIL_APP_PASSWORD manquante dans le fichier .env"

    message = MIMEMultipart()
    message["From"] = f"Mentor SC Bot <{sender_email}>"
    message["To"] = receiver_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    try:
        # Tentative sur port 587
        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=10)
        server.starttls()
        server.login(sender_email, app_password)
        server.sendmail(sender_email, receiver_email, message.as_string())
        server.quit()
        return True, "Succès"
    except Exception as e:
        error_msg = str(e)
        # Si échec sur 587, tentative désespérée sur 465
        try:
            server = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10)
            server.login(sender_email, app_password)
            server.sendmail(sender_email, receiver_email, message.as_string())
            server.quit()
            return True, "Succès (via SSL)"
        except Exception as e2:
            return False, f"Erreur SMTP: {error_msg} | Erreur SSL: {str(e2)}"
