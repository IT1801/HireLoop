from langchain_groq import ChatGroq
from src.components.graphs.state import HireLoopState
from src.components.tools.linkedin_tool import post_job_to_linkedin
from src.components.core.logger import logger
from src.components.core.config import settings
from src.components.core.exception import CustomException
import sys
from langgraph.types import interrupt

def generate_post_node(state: HireLoopState) -> HireLoopState:
    if not state.get("jd_approved"):
        logger.warning("JD was not approved. Cannot post.")
        return state
        
    if not state.get("linkedin_post"):
        logger.info("Generating LinkedIn post from JD...")
        llm = ChatGroq(model="llama-3.1-8b-instant", api_key=settings.GROQ_API_KEY)
        
        prompt = f"""You are an expert social media manager. Create a highly engaging, professional LinkedIn post announcing a new job opening.
        
        Job Role: {state['role']}
        Location: {state.get('location', 'Not specified')}
        Salary: {state.get('salary', 'Not specified')}
        Experience: {state.get('experience', 'Not specified')}
        
        Job Description:
        {state['jd']}
        
        Keep it concise, use relevant hashtags, and encourage people to apply.
        Output ONLY the text of the post without markdown blocks."""
        
        try:
            response = llm.invoke(prompt)
            
            post_content = response.content
            if isinstance(post_content, list):
                post_content = "".join([block.get("text", "") if isinstance(block, dict) else str(block) for block in post_content])
        except Exception as e:
            logger.error(f"LLM Error, falling back to mock Post: {CustomException(e, sys)}")
            post_content = f"We are hiring a {state['role']}!\n\nApply now if you have experience and want to work with an amazing team. #Hiring #{state['role'].replace(' ', '')}"
            
        state["linkedin_post"] = post_content.strip()
        state["post_approved"] = False
        state["status"] = "PENDING_POST_APPROVAL"
        
    return state

def approve_post_node(state: HireLoopState) -> HireLoopState:
    if not state.get("linkedin_post"):
        return state
        
    approval = interrupt({"action": "approve_post", "post": state["linkedin_post"]})
    
    if isinstance(approval, dict):
        state["linkedin_post"] = approval.get("post", state["linkedin_post"])
        state["post_approved"] = approval.get("post_approved", True)
        
    if not state.get("post_approved"):
        logger.warning("Post was not approved by HR.")
        return state
        
    logger.info("Posting job to LinkedIn...")
    posting_id = post_job_to_linkedin(state["role"], state["linkedin_post"])
    logger.info(f"Job posted with ID: {posting_id}")
    
    state["status"] = "POSTED_WAITING"
    return state
    
def wait_for_apps_node(state: HireLoopState) -> HireLoopState:
    if not state.get("post_approved"):
        return state
        
    state["days_waited"] = 0
    interrupt({"action": "wait_7_days", "message": "Waiting for applications to roll in..."})
    
    state["days_waited"] += 7
    state["status"] = "COLLECTING_APPS"
    return state
