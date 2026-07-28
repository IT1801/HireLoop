from langchain_groq import ChatGroq
from src.components.graphs.state import HireLoopState
from src.components.prompts.jd_creator import JD_GENERATION_PROMPT
from src.components.core.logger import logger
from src.components.core.config import settings
from langgraph.types import interrupt

def generate_jd_node(state: HireLoopState) -> HireLoopState:
    role = state.get("role")
    experience = state.get("experience", "Not specified")
    salary = state.get("salary", "Not specified")
    location = state.get("location", "Not specified")
    
    if not role:
        raise ValueError("Role must be provided to generate JD.")
        
    logger.info(f"Generating JD for role: {role}")
    llm = ChatGroq(model="llama-3.1-8b-instant", api_key=settings.GROQ_API_KEY)
    
    try:
        chain = JD_GENERATION_PROMPT | llm
        response = chain.invoke({
            "role": role,
            "experience": experience,
            "salary": salary,
            "location": location
        })
        jd = response.content
    except Exception as e:
        logger.error(f"LLM Error, falling back to mock JD: {str(e)}")
        jd = f"**[Fallback JD due to API Quota]**\n\nRole: {role}\nExperience: {experience}\nLocation: {location}\n\nThis is a fallback job description because the Google Gemini API free-tier quota was exhausted."
    
    logger.info("JD generated successfully.")
    
    state["jd"] = jd
    state["jd_approved"] = False
    state["status"] = "PENDING_JD_APPROVAL"
    return state

def approve_jd_node(state: HireLoopState) -> HireLoopState:
    if not state.get("jd"):
        logger.warning("JD was not generated.")
        return state
        
    approval = interrupt({"action": "approve_jd", "jd": state["jd"]})
    
    if isinstance(approval, dict):
        state["jd"] = approval.get("jd", state["jd"])
        state["jd_approved"] = approval.get("jd_approved", True)
    
    state["status"] = "JD_APPROVED"
    return state
