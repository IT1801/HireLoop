import smtplib
from email.message import EmailMessage
from src.components.core.config import settings
from src.components.core.logger import logger
from src.components.core.exception import EmailAPIError, CustomException
import sys

def send_email(to_email: str, subject: str, body: str) -> bool:
    """
    Send an email using SendGrid SMTP or generic SMTP.
    Requires SMTP configuration or SendGrid API key.
    """
    api_key = settings.SENDGRID_API_KEY
    if not api_key:
        logger.warning(f"SENDGRID_API_KEY not set. Simulating email to {to_email}")
        logger.info(f"Email Content:\nSubject: {subject}\n{body}")
        return True
        
    try:
        msg = EmailMessage()
        msg.set_content(body)
        msg['Subject'] = subject
        msg['From'] = "hello@hireloop.com"
        msg['To'] = to_email

        # SendGrid standard SMTP setup
        server = smtplib.SMTP('smtp.sendgrid.net', 587)
        server.starttls()
        server.login('apikey', api_key)
        server.send_message(msg)
        server.quit()
        logger.info(f"Successfully sent email to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {CustomException(e, sys)}")
        raise EmailAPIError(f"Email sending failed: {e}", sys)
