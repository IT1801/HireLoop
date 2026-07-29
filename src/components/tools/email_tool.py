import base64
import requests
from email.message import EmailMessage
from src.components.core.config import settings
from src.components.core.logger import logger
from src.components.core.exception import EmailAPIError, CustomException
import sys

def send_email(to_email: str, subject: str, body: str, company_id: str) -> bool:
    """
    Send an email using Google Workspace Gmail API.
    Requires Google OAuth credentials.
    """
    from src.components.core.tenant_utils import get_company_credentials
    creds = get_company_credentials(company_id)
    google_creds = creds.get("google_credentials", {})
    
    access_token = google_creds.get("access_token") if isinstance(google_creds, dict) else None
    
    if not access_token:
        logger.warning(f"Google Workspace not connected for this company. Simulating email to {to_email}")
        logger.info(f"Email Content:\nSubject: {subject}\n{body}")
        return True
        
    try:
        msg = EmailMessage()
        msg.set_content(body)
        msg['Subject'] = subject
        msg['From'] = "me"
        msg['To'] = to_email

        raw_msg = base64.urlsafe_b64encode(msg.as_bytes()).decode()

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "raw": raw_msg
        }

        # Gmail API to send email
        url = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        response.raise_for_status()
        
        logger.info(f"Successfully sent email to {to_email} via Gmail API")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send email to {to_email} via Gmail API: {CustomException(e, sys)}")
        if e.response is not None:
            logger.error(f"Response: {e.response.text}")
        logger.warning(f"Email failed to send, but proceeding anyway.")
        return False
    except Exception as e:
        logger.error(f"Failed to build email to {to_email}: {CustomException(e, sys)}")
        logger.warning(f"Email failed to send, but proceeding anyway.")
        return False
