# HireLoop ♾️

HireLoop is a fully autonomous, multi-tenant AI hiring SaaS platform built with **LangGraph**, **FastAPI**, and **Flask**. It simulates the entire lifecycle of a recruiter's job, from writing the initial Job Description all the way to sending out final offer letters. 

The system leverages a beautiful Human-in-the-Loop (HITL) dashboard that allows you to review and approve the AI's actions at critical stages, ensuring you always maintain final control.

## 🌟 Key Features

1. **Multi-Tenant Architecture & Secure Auth**
   - Supports multiple companies and recruiters on a centralized platform.
   - Secure authentication with `bcrypt` password hashing and a PostgreSQL backend.

2. **AI Job Description Generator**
   - Provide a role, salary, location, and experience level.
   - The AI uses Groq to generate a professional, tailored Job Description.
   - *Human-in-the-Loop:* Review and edit the JD on the dashboard before approving.

3. **Autonomous LinkedIn Posting**
   - Automatically drafts an engaging LinkedIn post based on the JD.
   - Authenticates via the LinkedIn API (OAuth) to post directly to your Personal Profile or Company Page.
   - *Human-in-the-Loop:* Review and edit the post before the AI pushes it live.

4. **Intelligent Resume Screening**
   - Simulates the collection of applicant resumes via candidate portals.
   - The AI reads each resume, compares it against the JD, and scores candidates out of 100 with detailed reasoning.
   - *Human-in-the-Loop:* Review the shortlisted candidates and their scores before proceeding.

5. **Automated Interview Scheduling (Google Calendar)**
   - Evaluates your availability via the **Google Calendar API**.
   - Drafts and sends personalized scheduling emails for shortlisted candidates using the **Gmail API** via Google Workspace OAuth.

6. **Observability & Reliability**
   - Deep integration with **LangSmith** for full LLM trace monitoring.
   - Centralized exception handling and file-based logging for robust debugging.

## 🛠️ Technology Stack

- **AI Framework:** LangChain & LangGraph (Stateful graph execution)
- **LLM Provider:** Groq (High-speed inference)
- **Backend APIs:** FastAPI (for graph execution), Flask (for the UI dashboard)
- **Database:** PostgreSQL via SQLAlchemy (Multi-tenant schema)
- **Integrations:** Google Workspace (Gmail, Calendar API via OAuth), LinkedIn Developer API (UGC Posts)
- **Observability:** LangSmith
- **Frontend:** HTML, CSS, JavaScript (Custom styling, dynamic polling, and timeline UI)

## 🚀 How to Run

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables:**
   Create a `.env` file in the root directory:
   ```env
   # API Keys
   GOOGLE_API_KEY=your_key
   GROQ_API_KEY=your_key
   LINKEDIN_ACCESS_TOKEN=your_token
   LINKEDIN_ORGANIZATION_ID=optional_company_id

   # OAuth Configurations
   GOOGLE_CLIENT_ID=your_google_client_id
   GOOGLE_CLIENT_SECRET=your_google_client_secret
   LINKEDIN_CLIENT_ID=your_linkedin_client_id
   LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret

   # LangSmith Observability
   LANGCHAIN_TRACING_V2=true
   LANGCHAIN_API_KEY=your_langchain_key
   LANGCHAIN_PROJECT=HireLoop

   # PostgreSQL DB
   POSTGRES_USER=hireloop
   POSTGRES_PASSWORD=hireloop_password
   POSTGRES_DB=hireloop_db
   POSTGRES_PORT=5434

   # App Settings
   APP_PORT=8000
   ```

3. **Run PostgreSQL Database:**
   Ensure your PostgreSQL instance is running on port 5434 and the credentials match your `.env` file.

4. **Run the Backend (FastAPI):**
   ```bash
   python -m uvicorn src.components.main:app --reload
   ```

5. **Run the Frontend Dashboard (Flask):**
   ```bash
   python src/frontend/app.py
   ```

6. **Initialize:**
   Navigate to `http://127.0.0.1:5000/`, log in/sign up, fill in the job details, and watch the AI go to work!

## 📸 Dashboard Overview
The frontend includes a dynamic timeline showing the current state of the pipeline. When the AI needs your permission, it pauses execution and presents a review block on the dashboard.
