# services/email_service.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

def send_email_notification(subject, body):
    """Envoie un email via SMTP Gmail."""
    sender_email = "r.k.badibanga@gmail.com"
    # Le mot de passe sera récupéré depuis les variables d'environnement
    app_password = os.getenv("GMAIL_APP_PASSWORD")
    if app_password:
        app_password = app_password.replace(" ", "")
    
    receiver_email = "r.k.badibanga@gmail.com"

    if not app_password:
        print("Erreur: GMAIL_APP_PASSWORD non configuré.")
        return False

    message = MIMEMultipart()
    message["From"] = f"Mentor SC Bot <{sender_email}>"
    message["To"] = receiver_email
    message["Subject"] = subject

    message.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, app_password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        return True
    except Exception as e:
        print(f"Erreur d'envoi email: {e}")
        return False
