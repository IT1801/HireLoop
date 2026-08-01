import uuid
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Any
from src.components.graphs.builder import build_graph
from src.components.core.logger import logger
from src.components.core.config import settings
from apscheduler.schedulers.background import BackgroundScheduler
from langgraph.types import Command

app = FastAPI(title="HireLoop Orchestrator API")

# No static files mounted on backend, use the Flask app on port 5001

graph = build_graph()

# Set up scheduler for 7-day waits
scheduler = BackgroundScheduler()
scheduler.start()

class StartRequest(BaseModel):
    role: str
    experience: str
    salary: str
    location: str
    company_id: str

class ResumeRequest(BaseModel):
    action: str
    data: dict[str, Any]

@app.get("/")
def health_check():
    return {"status": "HireLoop Backend is running. Please access the UI on port 5001."}

import re
from pydantic import BaseModel, field_validator

class LoginRequest(BaseModel):
    email: str
    password: str
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", v):
            raise ValueError("Must be a valid email address")
        return v

@app.post("/api/auth/login")
def login(req: LoginRequest):
    from src.components.core.tenant_db import SessionLocal, User, Company
    from src.components.core.auth import verify_password, get_password_hash
    import uuid
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == req.email).first()
        
        if not user:
            # Auto-Signup Flow: Create a new company and user
            company = Company(
                id=str(uuid.uuid4()),
                name=req.email.split('@')[1] if '@' in req.email else "New Company",
                domain=req.email.split('@')[1] if '@' in req.email else "",
                linkedin_access_token="",
                linkedin_org_id=""
            )
            db.add(company)
            
            user = User(
                id=str(uuid.uuid4()),
                company_id=company.id,
                email=req.email,
                password_hash=get_password_hash(req.password),
                role="admin"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"Auto-created new user and company for {req.email}")
            
        elif not verify_password(req.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid password")
            
        return {
            "status": "success",
            "user_id": user.id,
            "company_id": user.company_id,
            "role": user.role,
            "name": user.name,
            "phone": user.phone,
            "setup_complete": user.setup_complete
        }
    finally:
        db.close()

class SetupRequest(BaseModel):
    user_id: str
    name: str
    phone: str
    company_name: Optional[str] = None
    
@app.post("/api/user/setup")
def setup_user(req: SetupRequest):
    from src.components.core.tenant_db import SessionLocal, User, Company
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == req.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user.name = req.name
        user.phone = req.phone
        user.setup_complete = True

        if req.company_name:
            company = db.query(Company).filter(Company.id == user.company_id).first()
            if company:
                company.name = req.company_name
        
        db.commit()
        
        return {"status": "success", "message": "Setup completed successfully"}
    finally:
        db.close()


@app.post("/start")
def start_pipeline(req: StartRequest):
    """
    Start a new hiring pipeline for a specific role and company.
    """
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    # Save the job to the database
    from src.components.core.tenant_db import SessionLocal, Job
    db = SessionLocal()
    try:
        new_job = Job(
            id=thread_id,
            company_id=req.company_id,
            job_title=req.role,
            status="INITIALIZING"
        )
        db.add(new_job)
        db.commit()
    finally:
        db.close()
    
    state = {
        "job_id": thread_id,
        "company_id": req.company_id,
        "status": "INITIALIZING",
        "role": req.role,
        "experience": req.experience,
        "salary": req.salary,
        "location": req.location,
        "linkedin_post": None,
        "post_approved": False,
        "days_waited": 0,
        "applications": [],
        "jd_approved": False,
        "shortlist_approved": False,
        "interviews_concluded": False,
        "final_results_approved": False,
        "emails_sent": False
    }
    
    logger.info(f"Starting pipeline {thread_id} for role: {req.role}")
    
    # Run the graph until the first interrupt (JD approval)
    for event in graph.stream(state, config=config):
        logger.info(event)
        
    return {"thread_id": thread_id, "status": "PENDING_JD_APPROVAL"}

@app.get("/api/jobs/{company_id}")
def get_jobs(company_id: str):
    from src.components.core.tenant_db import SessionLocal, Job
    db = SessionLocal()
    try:
        jobs = db.query(Job).filter(Job.company_id == company_id).order_by(Job.created_at.desc()).all()
        return {
            "status": "success",
            "jobs": [
                {
                    "id": j.id,
                    "job_title": j.job_title,
                    "status": j.status,
                    "created_at": j.created_at.isoformat()
                } for j in jobs
            ]
        }
    finally:
        db.close()

@app.delete("/api/jobs/{job_id}")
def delete_job(job_id: str):
    from src.components.core.tenant_db import SessionLocal, Job, Application
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Delete associated applications
        db.query(Application).filter(Application.job_id == job_id).delete()
        # Delete the job
        db.delete(job)
        db.commit()
        return {"status": "success", "message": "Job deleted"}
    except Exception as e:
        logger.error(f"Error deleting job: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()

class SettingsRequest(BaseModel):
    linkedin_org_id: str = None
    linkedin_access_token: str = None
    google_credentials: str = None
    user_id: str = None
    name: str = None
    phone: str = None

@app.get("/api/settings/{company_id}")
def get_settings(company_id: str, user_id: str = None):
    from src.components.core.tenant_db import SessionLocal, Company, User
    db = SessionLocal()
    try:
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
            
        user_name = ""
        user_phone = ""
        if user_id:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user_name = user.name or ""
                user_phone = user.phone or ""
        
        return {
            "status": "success",
            "has_linkedin": bool(company.linkedin_access_token),
            "has_google": bool(company.google_credentials),
            "name": user_name,
            "phone": user_phone
        }
    finally:
        db.close()

@app.post("/api/settings/{company_id}")
def update_settings(company_id: str, req: SettingsRequest):
    from src.components.core.tenant_db import SessionLocal, Company, User
    db = SessionLocal()
    try:
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
            
        if req.linkedin_org_id is not None:
            company.linkedin_org_id = req.linkedin_org_id
        if req.linkedin_access_token is not None:
            company.linkedin_access_token = req.linkedin_access_token
        if req.google_credentials is not None:
            company.google_credentials = req.google_credentials
            
        if req.user_id:
            user = db.query(User).filter(User.id == req.user_id).first()
            if user:
                if req.name is not None:
                    user.name = req.name
                if req.phone is not None:
                    user.phone = req.phone
                    
        db.commit()
        return {"status": "success"}
    finally:
        db.close()

@app.get("/status/{thread_id}")
def get_status(thread_id: str):
    """
    Get the current state and pending interrupts for a thread.
    """
    config = {"configurable": {"thread_id": thread_id}}
    state_snap = graph.get_state(config)
    
    if not state_snap:
        raise HTTPException(status_code=404, detail="Thread not found")
        
    values = state_snap.values
    interrupts = [t.interrupts for t in state_snap.tasks if t.interrupts]
    
    current_step = values.get("status", "INITIALIZING")
    required_action = None
    action_data = None
    
    if interrupts and len(interrupts) > 0 and len(interrupts[0]) > 0:
        intr = interrupts[0][0].value
        if isinstance(intr, dict):
            required_action = intr.get("action")
            action_data = intr
            
    return {
        "current_step": current_step,
        "required_action": required_action,
        "action_data": action_data,
        "values": values,
        "next": state_snap.next
    }

@app.post("/resume/{thread_id}")
def resume_pipeline(thread_id: str, req: ResumeRequest):
    """
    Resume a halted pipeline by providing the required approval or data.
    """
    config = {"configurable": {"thread_id": thread_id}}
    state_snap = graph.get_state(config)
    
    if not state_snap.tasks:
        raise HTTPException(status_code=400, detail="No pending interrupts to resume")
        
    # In LangGraph 0.2, to resume from an interrupt, we pass a Command(resume=value)
    # The value is what the interrupt() call returns.
    
    logger.info(f"Resuming thread {thread_id} with action {req.action}")
    
    command = Command(resume=req.data)
    
    for event in graph.stream(command, config=config):
        logger.info(event)
        
    return {"status": "Resumed"}

@app.post("/trigger_scheduler/{thread_id}")
def trigger_scheduler(thread_id: str):
    """
    Helper endpoint to artificially trigger the 7-day wait.
    In a real system, APScheduler would call this or the resume function directly.
    """
    req = ResumeRequest(action="wait_7_days", data={"waited": True})
    return resume_pipeline(thread_id, req)

# --- OAuth 2.0 Endpoints ---

import urllib.parse
from fastapi.responses import RedirectResponse

@app.get("/auth/google/login")
def google_login(company_id: str):
    client_id = settings.GOOGLE_CLIENT_ID
    if not client_id:
        return RedirectResponse(url=f"http://127.0.0.1:5001/settings?error=Google+Client+ID+not+configured")
    
    redirect_uri = f"http://127.0.0.1:8000/auth/google/callback"
    state = company_id
    
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={client_id}&"
        f"redirect_uri={urllib.parse.quote(redirect_uri)}&"
        f"response_type=code&"
        f"scope=https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/calendar.events&"
        f"access_type=offline&"
        f"prompt=consent&"
        f"state={state}"
    )
    return RedirectResponse(auth_url)

@app.get("/auth/google/callback")
def google_callback(code: str, state: str):
    import requests
    company_id = state
    redirect_uri = f"http://127.0.0.1:8000/auth/google/callback"
    
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }
    
    resp = requests.post(token_url, data=data)
    if resp.status_code != 200:
        logger.error(f"Google OAuth Error: {resp.text}")
        return RedirectResponse(url=f"http://127.0.0.1:5001/settings?error=Google+OAuth+Failed")
        
    tokens = resp.json()
    import json
    
    from src.components.core.tenant_db import SessionLocal, Company
    db = SessionLocal()
    try:
        company = db.query(Company).filter(Company.id == company_id).first()
        if company:
            company.google_credentials = json.dumps(tokens)
            db.commit()
    finally:
        db.close()
        
    return RedirectResponse(url=f"http://127.0.0.1:5001/settings?success=Google+Connected")

@app.get("/auth/linkedin/login")
def linkedin_login(company_id: str):
    client_id = settings.LINKEDIN_CLIENT_ID
    if not client_id:
        return RedirectResponse(url=f"http://127.0.0.1:5001/settings?error=LinkedIn+Client+ID+not+configured")
        
    redirect_uri = f"http://127.0.0.1:8000/auth/linkedin/callback"
    state = company_id
    
    auth_url = (
        f"https://www.linkedin.com/oauth/v2/authorization?"
        f"response_type=code&"
        f"client_id={client_id}&"
        f"redirect_uri={urllib.parse.quote(redirect_uri)}&"
        f"state={state}&"
        f"scope=openid%20profile%20email%20w_member_social"
    )
    return RedirectResponse(auth_url)

@app.get("/auth/linkedin/callback")
def linkedin_callback(state: str, code: Optional[str] = None, error: Optional[str] = None, error_description: Optional[str] = None):
    if error or not code:
        logger.error(f"LinkedIn OAuth Error: {error} - {error_description}")
        return RedirectResponse(url=f"http://127.0.0.1:5001/settings?error=LinkedIn+OAuth+Failed")

    import requests
    company_id = state
    redirect_uri = f"http://127.0.0.1:8000/auth/linkedin/callback"
    
    token_url = "https://www.linkedin.com/oauth/v2/accessToken"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": settings.LINKEDIN_CLIENT_ID,
        "client_secret": settings.LINKEDIN_CLIENT_SECRET
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    
    resp = requests.post(token_url, data=data, headers=headers)
    if resp.status_code != 200:
        logger.error(f"LinkedIn OAuth Error: {resp.text}")
        return RedirectResponse(url=f"http://127.0.0.1:5001/settings?error=LinkedIn+OAuth+Failed")
        
    tokens = resp.json()
    
    from src.components.core.tenant_db import SessionLocal, Company
    db = SessionLocal()
    try:
        company = db.query(Company).filter(Company.id == company_id).first()
        if company:
            company.linkedin_access_token = tokens.get("access_token")
            db.commit()
    finally:
        db.close()
        
    return RedirectResponse(url=f"http://127.0.0.1:5001/settings?success=LinkedIn+Connected")

class ApplicationRequest(BaseModel):
    name: str
    email: str
    contact_number: Optional[str] = None
    resume_text: str

@app.post("/api/apply/{job_id}")
def apply_for_job(job_id: str, req: ApplicationRequest):
    from src.components.core.tenant_db import SessionLocal, Application, Job
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
            
        app_id = str(uuid.uuid4())
        new_app = Application(
            id=app_id,
            job_id=job_id,
            name=req.name,
            email=req.email,
            contact_number=req.contact_number,
            resume_text=req.resume_text,
            status="new"
        )
        db.add(new_app)
        db.commit()
        return {"status": "success", "application_id": app_id}
    except Exception as e:
        logger.error(f"Error submitting application: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.components.main:app", host="0.0.0.0", port=settings.APP_PORT, reload=True)
