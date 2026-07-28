from langchain_core.prompts import PromptTemplate

RESUME_SCORER_PROMPT = PromptTemplate(
    input_variables=["jd", "resume"],
    template="""You are an expert technical recruiter evaluating a candidate's resume against a job description.

Job Description:
{jd}

Candidate Resume:
{resume}

Evaluate the candidate based on how well their skills and experience match the requirements in the job description.
Score them from 0 to 100.
Also, make a decision to either "shortlist" or "reject" the candidate. A score above 70 should generally be shortlisted.

Return your response strictly in the following JSON format:
{{
    "score": <int>,
    "decision": "<shortlist or reject>"
}}
"""
)
