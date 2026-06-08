import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

def send_recovery_email(to_email: str, reset_token: str, base_url: str = "http://localhost:8000"):
    if not SMTP_USER or not SMTP_PASSWORD:
        print("ADVERTENCIA: Las credenciales SMTP no están configuradas en el archivo .env. Simulando envío.")
        print(f"-> Simulando envío de email a {to_email} con el token {reset_token}")
        return True
    
    reset_url = f"{base_url}/reset-password?token={reset_token}"
    
    # Crear el mensaje HTML
    html = f"""
    <html>
      <body style="background-color: #0b1310; color: #f5f5dc; font-family: sans-serif; padding: 40px; text-align: center;">
        <h1 style="color: #398a48;">SCOREIA</h1>
        <p>Hola,</p>
        <p>Hemos recibido una solicitud para restablecer tu contraseña.</p>
        <p>Haz clic en el siguiente enlace para crear una nueva contraseña:</p>
        <a href="{reset_url}" style="background-color: #398a48; color: white; padding: 15px 25px; text-decoration: none; border-radius: 10px; display: inline-block; margin-top: 20px; font-weight: bold;">
          Restablecer Contraseña
        </a>
        <p style="margin-top: 40px; color: #f5f5dc80; font-size: 12px;">Si no solicitaste este cambio, puedes ignorar este correo.</p>
      </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Recuperación de Contraseña - SCOREIA"
    msg["From"] = SMTP_USER
    msg["To"] = to_email

    part_html = MIMEText(html, "html")
    msg.attach(part_html)

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Error enviando correo: {e}")
        return False
