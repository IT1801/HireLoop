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

# Serve the static frontend
import os
os.makedirs("src/static", exist_ok=True)
app.mount("/static", StaticFiles(directory="src/static"), name="static")

graph = build_graph()

# Set up scheduler for 7-day waits
scheduler = BackgroundScheduler()
scheduler.start()

class StartRequest(BaseModel):
    role: str
    experience: str
    salary: str
    location: str

class ResumeRequest(BaseModel):
    action: str
    data: dict[str, Any]

@app.get("/")
def serve_frontend():
    return FileResponse("src/static/index.html")

@app.post("/start")
def start_pipeline(req: StartRequest):
    """
    Start a new hiring pipeline for a specific role.
    """
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    state = {
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

@app.get("/status/{thread_id}")
def get_status(thread_id: str):
    """
    Get the current state and pending interrupts for a thread.
    """
    config = {"configurable": {"thread_id": thread_id}}
    state_snap = graph.get_state(config)
    
    if not state_snap:
        raise HTTPException(status_code=404, detail="Thread not found")
        
    return {
        "values": state_snap.values,
        "next": state_snap.next,
        "tasks": [t.interrupts for t in state_snap.tasks if t.interrupts]
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.components.main:app", host="0.0.0.0", port=settings.APP_PORT, reload=True)
