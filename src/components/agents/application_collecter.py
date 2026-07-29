import uuid
from src.components.graphs.state import HireLoopState
from src.components.core.logger import logger

def application_collector(state: HireLoopState) -> HireLoopState:
    """
    Simulates polling an inbox or ATS for incoming applications.
    """
    logger.info("Polling for incoming applications...")
    
    logger.info("Fetching real applications from database...")
    
    from src.components.core.tenant_db import SessionLocal, Application
    db = SessionLocal()
    
    try:
        job_id = state.get("job_id")
        apps = db.query(Application).filter(Application.job_id == job_id).all()
        
        real_apps = []
        for app in apps:
            real_apps.append({
                "id": app.id,
                "name": app.name,
                "email": app.email,
                "resume_text": app.resume_text,
                "score": app.ai_score,
                "decision": None,
                "interview_slot": app.interview_slot,
                "outcome": None
            })
            
        state["applications"] = real_apps
        logger.info(f"Collected {len(real_apps)} applications from database.")
    except Exception as e:
        logger.error(f"Error fetching applications: {e}")
        state["applications"] = []
    finally:
        db.close()
        
    from src.components.core.config import settings
    if settings.FAST_FORWARD_WAITS and len(state["applications"]) < 3:
        logger.info("FAST_FORWARD_WAITS is true and <3 apps found. Injecting mock applications...")
        mock_resumes = [
            "Highly experienced Machine Learning Engineer with 5 years of Python and TensorFlow experience. Delivered 3 NLP projects.",
            "Recent CS Graduate with strong fundamentals in algorithms. Built a few computer vision side projects using PyTorch.",
            "Data Scientist with a background in statistics. Strong R and SQL skills, looking to move into deep learning."
        ]
        for i, res in enumerate(mock_resumes):
            state["applications"].append({
                "id": f"mock_app_{i}",
                "name": f"Mock Candidate {i+1}",
                "email": f"candidate{i+1}@example.com",
                "resume_text": res,
                "score": None,
                "decision": None,
                "interview_slot": None,
                "outcome": None
            })

    # The edges.py logic will decide whether this is enough or if we need to regenerate the JD
    state["status"] = "APPLICATIONS_COLLECTED"
    return state
