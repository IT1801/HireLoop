from typing import Literal
from src.components.graphs.state import HireLoopState
from src.components.core.logger import logger

def check_responses(state: HireLoopState) -> Literal["resume_screener", "jd_generator"]:
    """
    Check if we have enough applications. If not, route back to JD generator
    to tweak the JD and repost.
    """
    apps = state.get("applications", [])
    if len(apps) < 3: # Arbitrary threshold for enough responses
        logger.info(f"Only {len(apps)} applications received. Regenerating JD...")
        return "jd_generator"
    
    logger.info(f"{len(apps)} applications received. Proceeding to screening.")
    return "resume_screener"
