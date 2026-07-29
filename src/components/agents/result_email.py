from src.components.graphs.state import HireLoopState
from src.components.tools.email_tool import send_email
from src.components.prompts.email_templates import get_accept_email, get_reject_email
from src.components.core.logger import logger
from langgraph.types import interrupt

def result_preparer(state: HireLoopState) -> HireLoopState:
    """
    Prepare draft outcomes and interrupt for HR approval.
    """
    if not state.get("interviews_concluded"):
        return state
        
    apps = state.get("applications", [])
    
    # In a real app, HR or interviewers would have submitted feedback to the state
    # Here we simulate that the top scorer (or random) gets accepted, rest rejected
    # For simulation, anyone with score >= 90 gets accept, else reject
    # We will just mark it in the state draft
    draft_outcomes = {}
    for app in apps:
        if app.get("decision") == "shortlist":
            if app.get("score", 0) >= 90:
                draft_outcomes[app["id"]] = "accept"
            else:
                draft_outcomes[app["id"]] = "reject"
        else:
            draft_outcomes[app["id"]] = "reject"
            
    state["final_results_draft"] = draft_outcomes
    state["final_results_approved"] = False
    state["status"] = "PENDING_RESULTS_APPROVAL"
    
    # HR Approval Interrupt
    approval = interrupt({"action": "approve_results", "draft_outcomes": draft_outcomes})
    
    if isinstance(approval, dict):
        state["final_results_draft"] = approval.get("draft_outcomes", draft_outcomes)
        state["final_results_approved"] = approval.get("final_results_approved", True)
        
    state["status"] = "RESULTS_APPROVED"
    return state

def result_email(state: HireLoopState) -> HireLoopState:
    """
    Dispatch outcome emails based on approved results.
    """
    if not state.get("final_results_approved"):
        logger.warning("Final results were not approved.")
        return state
        
    apps = state.get("applications", [])
    role = state.get("role", "Open Position")
    draft_outcomes = state.get("final_results_draft", {})
    company_id = state.get("company_id")
    
    for app in apps:
        outcome = draft_outcomes.get(app["id"], "reject")
        app["outcome"] = outcome
        
        logger.info(f"Sending {outcome} email to {app['email']}")
        
        if outcome == "accept":
            body = get_accept_email(app["name"], role)
            subject = f"Offer to Join - {role} at HireLoop"
        else:
            body = get_reject_email(app["name"], role)
            subject = f"Update on your application for {role}"
            
        send_email(app["email"], subject, body, company_id)
        
    state["emails_sent"] = True
    state["status"] = "PIPELINE_COMPLETE"
    return state
