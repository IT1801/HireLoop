from src.components.graphs.state import HireLoopState
from src.components.tools.email_tool import send_email
from src.components.tools.calender_tool import schedule_interview
from src.components.prompts.email_templates import get_invite_email
from src.components.core.logger import logger
from langgraph.types import interrupt

def scheduler_email(state: HireLoopState) -> HireLoopState:
    """
    Sends interview invites to the approved shortlisted candidates and blocks calendar.
    Then interrupts to wait for the interviews to conclude.
    """
    if not state.get("shortlist_approved"):
        logger.warning("Shortlist was not approved. Halting scheduling.")
        return state
        
    apps = state.get("applications", [])
    shortlisted = [app for app in apps if app.get("decision") == "shortlist"]
    role = state.get("role", "Open Position")
    
    for candidate in shortlisted:
        logger.info(f"Booking calendar for {candidate['name']} at {candidate['interview_slot']}")
        schedule_interview(candidate["email"], candidate["interview_slot"])
        
        logger.info(f"Sending invite email to {candidate['email']}")
        body = get_invite_email(candidate["name"], role, candidate["interview_slot"])
        send_email(candidate["email"], f"Interview Invitation - {role}", body)
        
    state["status"] = "WAITING_FOR_INTERVIEWS"
    state["interviews_concluded"] = False
    
    # Interrupt to wait for interviews to conclude
    interrupt({"action": "wait_interviews", "message": "Wait for interviews to finish before finalizing outcomes."})
    
    state["interviews_concluded"] = True
    state["status"] = "INTERVIEWS_CONCLUDED"
    
    return state
