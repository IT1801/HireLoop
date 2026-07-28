# HireLoop ♾️

HireLoop is a fully autonomous, end-to-end AI hiring agent pipeline built with **LangGraph**, **FastAPI**, and **Flask**. It simulates the entire lifecycle of a recruiter's job, from writing the initial Job Description all the way to sending out final offer letters. 

The system leverages a beautiful Human-in-the-Loop (HITL) dashboard that allows you to review and approve the AI's actions at critical stages, ensuring you always maintain final control.

## 🌟 Key Features

1. **AI Job Description Generator**
   - Provide a role, salary, location, and experience level.
   - The AI uses Groq to generate a professional, tailored Job Description.
   - *Human-in-the-Loop:* Review and edit the JD on the dashboard before approving.

2. **Autonomous LinkedIn Posting**
   - Automatically drafts an engaging LinkedIn post based on the JD.
   - Authenticates via the LinkedIn API to post directly to your Personal Profile or Company Page.
   - *Human-in-the-Loop:* Review and edit the post before the AI pushes it live.

3. **Intelligent Resume Screening**
   - Simulates the collection of applicant resumes.
   - The AI reads each resume, compares it against the JD, and scores candidates out of 100 with detailed reasoning.
   - *Human-in-the-Loop:* Review the shortlisted candidates and their scores before proceeding.

4. **Automated Interview Scheduling**
   - Evaluates your calendar availability.
   - Drafts scheduling emails for shortlisted candidates using **SendGrid**.

5. **Final Decision & Offer Letters**
   - Simulates the interview process.
   - Drafts final Offer or Rejection emails based on simulated interview performance.
   - *Human-in-the-Loop:* Final approval required before the offer emails are dispatched.

## 🛠️ Technology Stack

- **AI Framework:** LangChain & LangGraph (Stateful graph execution with SQLite checkpointing)
- **LLM Provider:** Groq (High-speed inference)
- **Backend APIs:** FastAPI (for graph execution), Flask (for the UI dashboard)
- **Integrations:** LinkedIn Developer API (UGC Posts), SendGrid API (Email)
- **Frontend:** HTML, CSS, JavaScript (Custom styling, dynamic polling, and timeline UI)

## 🚀 How to Run

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables:**
   Create a `.env` file in the root directory:
   ```env
   GOOGLE_API_KEY=your_key
   GROQ_API_KEY=your_key
   SENDGRID_API_KEY=your_key
   LINKEDIN_ACCESS_TOKEN=your_token
   LINKEDIN_ORGANIZATION_ID=optional_company_id
   APP_PORT=8000
   DB_PATH=hireloop.sqlite
   ```

3. **Run the Backend (FastAPI):**
   ```bash
   python -m uvicorn src.components.main:app --reload
   ```

4. **Run the Frontend Dashboard (Flask):**
   ```bash
   python src/frontend/app.py
   ```

5. **Initialize:**
   Navigate to `http://127.0.0.1:5000/`, fill in the job details, and watch the AI go to work!

## 📸 Dashboard Overview
The frontend includes a dynamic timeline showing the current state of the pipeline (Initialize -> JD Generation -> LinkedIn Post -> App Collection). When the AI needs your permission, it pauses execution and presents a review block on the dashboard.
