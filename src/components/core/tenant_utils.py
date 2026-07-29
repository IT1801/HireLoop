from src.components.core.tenant_db import SessionLocal, Company
import json

def get_company_credentials(company_id: str) -> dict:
    """
    Fetches the OAuth and API credentials for a given company ID.
    """
    db = SessionLocal()
    try:
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            return {}
            
        google_creds = {}
        if company.google_credentials:
            try:
                google_creds = json.loads(company.google_credentials)
            except:
                pass
                
        return {
            "linkedin_access_token": company.linkedin_access_token,
            "linkedin_org_id": company.linkedin_org_id,
            "google_credentials": google_creds
        }
    finally:
        db.close()
