from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from credentials import decrypt_secret
import os

# Load the .env file
load_dotenv()

# ------------------ Alerting Config ------------------
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# ------------------ Helper for sending email alerts ------------------
def send_alert(subject: str, message: str):
    try:
        # --- Load encrypted values ---
        alert_email_enc = os.getenv("ALERT_EMAIL_ENC")
        alert_email_password_enc = os.getenv("ALERT_EMAIL_PASSWORD_ENC")
        alert_to = os.getenv("ALERT_EMAIL_TO")

         # --- Decrypt ---
        alert_email = decrypt_secret(alert_email_enc)
        alert_email_password = decrypt_secret(alert_email_password_enc)

        if not alert_email or not alert_email_password:
            raise Exception("Failed to decrypt alert email sender credentials.")
        
        if not alert_to:
            raise Exception("Email recipient was not set.")

        msg = MIMEMultipart()
        msg['From'] = alert_email
        msg['To'] = alert_to
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'plain'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(alert_email, alert_email_password)
        server.send_message(msg)
        server.quit()
        print(f"{datetime.now()} → Alert sent: {subject}")
    except Exception as e:
        print(f"{datetime.now()} → Failed to send alert: {e}")
