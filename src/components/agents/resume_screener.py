import json
from langchain_groq import ChatGroq
from src.components.graphs.state import HireLoopState
from src.components.prompts.resume_scorer import RESUME_SCORER_PROMPT
from src.components.core.logger import logger
from src.components.core.config import settings
from src.components.core.exception import CustomException
import sys

def resume_screener(state: HireLoopState) -> HireLoopState:
    """
    Score candidates against the JD using an LLM.
    """
    jd = state.get("jd")
    apps = state.get("applications", [])
    
    if not jd or not apps:
        logger.warning("Missing JD or applications to screen.")
        return state
        
    logger.info(f"Screening {len(apps)} applications...")
    
    # Initialize LLM (Ensure to request JSON response)
    llm = ChatGroq(model="llama-3.1-8b-instant", api_key=settings.GROQ_API_KEY, model_kwargs={"response_format": {"type": "json_object"}})
    chain = RESUME_SCORER_PROMPT | llm
    
    for app in apps:
        logger.info(f"Scoring {app['name']}...")
        try:
            response = chain.invoke({"jd": jd, "resume": app["resume_text"]})
            
            # Clean up the response content in case it contains markdown formatting
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:-3]
            elif content.startswith("```"):
                content = content[3:-3]
            
            result = json.loads(content)
            
            app["score"] = result.get("score", 0)
            app["decision"] = result.get("decision", "reject").lower()
            logger.info(f"{app['name']} scored {app['score']} - {app['decision']}")
            
        except Exception as e:
            logger.error(f"Error scoring {app['name']}: {CustomException(e, sys)}")
            app["score"] = 0
            app["decision"] = "reject"
            
    state["applications"] = apps
    state["status"] = "SCREENING_COMPLETE"
    return state
