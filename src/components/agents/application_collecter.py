import uuid
from src.components.graphs.state import HireLoopState
from src.components.core.logger import logger

def application_collector(state: HireLoopState) -> HireLoopState:
    """
    Simulates polling an inbox or ATS for incoming applications.
    """
    logger.info("Polling for incoming applications...")
    
    # In a real app, this would read from Gmail/IMAP or an ATS API
    # We will simulate receiving 4 applications for the role
    mock_apps = [
        {
            "id": str(uuid.uuid4()),
            "name": "Alice Smith",
            "email": "alice@example.com",
            "resume_text": f"Experienced software engineer with 5 years of Python and React. Built scalable backends.",
            "score": None,
            "decision": None,
            "interview_slot": None,
            "outcome": None
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Bob Jones",
            "email": "bob@example.com",
            "resume_text": f"Recent grad, know some HTML and CSS. Looking for entry level.",
            "score": None,
            "decision": None,
            "interview_slot": None,
            "outcome": None
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Charlie Brown",
            "email": "charlie@example.com",
            "resume_text": f"Senior Data Scientist, expert in Machine Learning, LangChain, and generative AI.",
            "score": None,
            "decision": None,
            "interview_slot": None,
            "outcome": None
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Diana Prince",
            "email": "diana@example.com",
            "resume_text": f"Project manager with 10 years experience leading agile teams.",
            "score": None,
            "decision": None,
            "interview_slot": None,
            "outcome": None
        }
    ]
    
    state["applications"] = mock_apps
    logger.info(f"Collected {len(mock_apps)} applications.")
    
    # The edges.py logic will decide whether this is enough or if we need to regenerate the JD
    state["status"] = "APPLICATIONS_COLLECTED"
    return state
