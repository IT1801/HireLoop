from src.components.graphs.state import HireLoopState
from src.components.tools.email_tool import send_email
from src.components.tools.calender_tool import schedule_interview
from src.components.prompts.email_templates import get_invite_email
from src.components.core.logger import logger
from src.components.core.config import settings
from src.components.core.exception import CustomException
from langchain_groq import ChatGroq
import sys
from langgraph.types import interrupt

def draft_schedule_emails(state: HireLoopState) -> HireLoopState:
    """
    Generates personalized invite emails for shortlisted candidates using LLM.
    """
    if not state.get("shortlist_approved"):
        logger.warning("Shortlist was not approved. Halting email drafting.")
        return state
        
    apps = state.get("applications", [])
    role = state.get("role", "Open Position")
    
    llm = ChatGroq(model="llama-3.1-8b-instant", api_key=settings.GROQ_API_KEY)
    
    for candidate in apps:
        if candidate.get("decision") == "shortlist" and not candidate.get("invite_email_draft"):
            logger.info(f"Drafting invite email for {candidate['name']}...")
            
            prompt = f"""You are an HR coordinator at HireLoop. Write a professional, welcoming interview invitation email to a candidate.
            
            Candidate Name: {candidate['name']}
            Role: {role}
            Proposed Interview Slot: {candidate['interview_slot']}
            
            Keep the email concise (2-3 short paragraphs). Mention the role, the proposed time slot, and express excitement to speak with them. 
            Do not include placeholders for links, just mention that a calendar invite will follow.
            Output ONLY the email body text."""
            
            try:
                response = llm.invoke(prompt)
                draft_content = response.content
                if isinstance(draft_content, list):
                    draft_content = "".join([block.get("text", "") if isinstance(block, dict) else str(block) for block in draft_content])
            except Exception as e:
                logger.error(f"LLM Error drafting email for {candidate['name']}: {CustomException(e, sys)}")
                # Fallback to standard template
                draft_content = get_invite_email(candidate['name'], role, candidate['interview_slot'])
                
            candidate["invite_email_draft"] = draft_content.strip()
            
    state["schedule_emails_approved"] = False
    state["status"] = "PENDING_SCHEDULE_APPROVAL"
    
    return state


def approve_schedule_emails(state: HireLoopState) -> HireLoopState:
    """
    Interrupts to request human approval of the drafted schedule emails.
    """
    if state.get("schedule_emails_approved"):
        return state
        
    apps = state.get("applications", [])
    shortlisted = [app for app in apps if app.get("decision") == "shortlist"]
    
    drafts = [{"id": c["id"], "name": c["name"], "draft": c.get("invite_email_draft", "")} for c in shortlisted]
    
    approval = interrupt({"action": "approve_schedule_emails", "drafts": drafts})
    
    if isinstance(approval, dict):
        state["schedule_emails_approved"] = approval.get("schedule_emails_approved", True)
        approved_drafts = approval.get("drafts", [])
        
        # Update drafts with any edits made by HR
        for updated_draft in approved_drafts:
            for c in apps:
                if c["id"] == updated_draft["id"]:
                    c["invite_email_draft"] = updated_draft["draft"]
                    break
                    
    if not state.get("schedule_emails_approved"):
        logger.warning("Schedule emails were not approved.")
        return state
        
    state["status"] = "SCHEDULING_INTERVIEWS"
    return state


def scheduler_email(state: HireLoopState) -> HireLoopState:
    """
    Sends the approved interview invites and blocks calendar.
    Then interrupts to wait for the interviews to conclude.
    """
    if not state.get("schedule_emails_approved"):
        return state
        
    apps = state.get("applications", [])
    shortlisted = [app for app in apps if app.get("decision") == "shortlist"]
    role = state.get("role", "Open Position")
    company_id = state.get("company_id")
    
    for candidate in shortlisted:
        logger.info(f"Booking calendar for {candidate['name']} at {candidate['interview_slot']}")
        schedule_interview(candidate["email"], candidate["interview_slot"], company_id)
        
        logger.info(f"Sending personalized invite email to {candidate['email']}")
        body = candidate.get("invite_email_draft", get_invite_email(candidate["name"], role, candidate["interview_slot"]))
        send_email(candidate["email"], f"Interview Invitation - {role}", body, company_id)
        
    state["status"] = "WAITING_FOR_INTERVIEWS"
    state["interviews_concluded"] = False
    
    # Interrupt to wait for interviews to conclude
    interrupt({"action": "wait_interviews", "message": "Wait for interviews to finish before finalizing outcomes."})
    
    state["interviews_concluded"] = True
    state["status"] = "INTERVIEWS_CONCLUDED"
    
    return state
