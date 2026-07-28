from langchain_core.prompts import PromptTemplate

JD_GENERATION_PROMPT = PromptTemplate(
    input_variables=["role", "experience", "salary", "location"],
    template="""You are an expert HR recruiter. 
Please generate a professional, compelling, and detailed Job Description for the following role:
Role: {role}
Experience Required: {experience}
Salary Range: {salary}
Location: {location}

Include:
1. Job Title
2. About the Role
3. Key Responsibilities
4. Requirements (Skills and Experience)

Format the output cleanly in plain text (no markdown formatting)."""
)
