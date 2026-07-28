from src.components.graphs.state import HireLoopState
from src.components.tools.calender_tool import find_available_slots
from src.components.core.logger import logger
from langgraph.types import interrupt

def calendar_checker(state: HireLoopState) -> HireLoopState:
    """
    Finds available slots for shortlisted candidates.
    Then interrupts for HR approval on the shortlist & proposed schedule.
    """
    apps = state.get("applications", [])
    shortlisted = [app for app in apps if app.get("decision") == "shortlist"]
    
    if not shortlisted:
        logger.warning("No candidates were shortlisted.")
        state["status"] = "NO_SHORTLIST"
        return state
        
    logger.info(f"Finding calendar slots for {len(shortlisted)} shortlisted candidates...")
    slots = find_available_slots()
    
    # Assign slots naively for demonstration
    for i, candidate in enumerate(shortlisted):
        assigned_slot = slots[i % len(slots)]
        candidate["interview_slot"] = assigned_slot
        logger.info(f"Proposed {assigned_slot} for {candidate['name']}")
        
    state["status"] = "PENDING_SHORTLIST_APPROVAL"
    state["shortlist_approved"] = False
    
    # Interrupt for human approval on the shortlist and schedule
    approval = interrupt({"action": "approve_shortlist", "shortlisted": shortlisted})
    
    if isinstance(approval, dict):
        state["shortlist_approved"] = approval.get("shortlist_approved", True)
        # Assuming approval dictionary might also pass updated interview slots
        # For simplicity, we just mark it approved here
        
    state["status"] = "SHORTLIST_APPROVED"
    return state
