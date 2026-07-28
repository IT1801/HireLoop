from typing import TypedDict, List, Dict, Any, Optional
from operator import add
from typing_extensions import Annotated

class Candidate(TypedDict):
    id: str
    name: str
    email: str
    resume_text: str
    score: Optional[int]
    decision: Optional[str] # "shortlist" or "reject"
    interview_slot: Optional[str]
    outcome: Optional[str] # "accept" or "reject"

class HireLoopState(TypedDict):
    status: str
    role: str
    experience: str
    salary: str
    location: str
    jd: Optional[str]
    jd_approved: bool
    
    linkedin_post: Optional[str]
    post_approved: bool
    
    days_waited: int
    applications: List[Candidate]
    
    shortlist_approved: bool
    
    interviews_concluded: bool
    final_results_approved: bool
    emails_sent: bool
    
    # Track the current status for debugging or UI
    status: str
