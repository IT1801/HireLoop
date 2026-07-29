from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import requests
import os
import sys
from src.components.core.logger import logger
from src.components.core.exception import CustomException

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "super-secret-hireloop-key-123")

# URL to the FastAPI backend running in a separate process
BACKEND_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        try:
            resp = requests.post(f"{BACKEND_URL}/api/auth/login", json={
                "email": email,
                "password": password
            })
            if resp.status_code == 200:
                data = resp.json()
                session["user_id"] = data["user_id"]
                session["company_id"] = data["company_id"]
                session["role"] = data["role"]
                return redirect(url_for("index"))
            elif resp.status_code == 422:
                return render_template("login.html", error="Please enter a valid email address.")
            else:
                return render_template("login.html", error="Invalid credentials. Please try again.")
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return render_template("login.html", error="System offline. Please try again later.")
            
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/", methods=["GET", "POST"])
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))
        
    company_id = session["company_id"]
        
    if request.method == "POST":
        role = request.form.get("role")
        experience = request.form.get("experience")
        salary = request.form.get("salary")
        location = request.form.get("location")
        
        # Start the pipeline on the backend, injecting the logged-in company_id
        try:
            resp = requests.post(f"{BACKEND_URL}/start", json={
                "role": role,
                "experience": experience,
                "salary": salary,
                "location": location,
                "company_id": company_id
            })
            resp.raise_for_status()
            data = resp.json()
            thread_id = data.get("thread_id")
            return redirect(url_for("dashboard", thread_id=thread_id))
        except Exception as e:
            logger.error(f"Error communicating with backend: {CustomException(e, sys)}")
            return f"Error communicating with backend: {str(e)}", 500
            
    # Fetch jobs for this company
    jobs = []
    has_auth_verified = False
    try:
        resp = requests.get(f"{BACKEND_URL}/api/jobs/{company_id}")
        if resp.status_code == 200:
            jobs = resp.json().get("jobs", [])
            
        settings_resp = requests.get(f"{BACKEND_URL}/api/settings/{company_id}")
        if settings_resp.status_code == 200:
            s_data = settings_resp.json()
            has_auth_verified = s_data.get("has_linkedin", False) and s_data.get("has_google", False)
            
    except Exception as e:
        logger.error(f"Error fetching jobs or settings: {e}")
        
    return render_template("index.html", jobs=jobs, has_auth_verified=has_auth_verified)

@app.route("/dashboard/<thread_id>")
def dashboard(thread_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html", thread_id=thread_id)

@app.route("/settings", methods=["GET", "POST"])
def settings():
    if "user_id" not in session:
        return redirect(url_for("login"))
        
    company_id = session["company_id"]
    
    if request.method == "POST":
        linkedin_org_id = request.form.get("linkedin_org_id")
        linkedin_access_token = request.form.get("linkedin_access_token")
        google_credentials = request.form.get("google_credentials")
        
        payload = {}
        if linkedin_org_id: payload["linkedin_org_id"] = linkedin_org_id
        if linkedin_access_token: payload["linkedin_access_token"] = linkedin_access_token
        if google_credentials: payload["google_credentials"] = google_credentials
        
        try:
            resp = requests.post(f"{BACKEND_URL}/api/settings/{company_id}", json=payload)
            if resp.status_code == 200:
                return render_template("settings.html", success="Settings updated successfully!", has_linkedin=True, has_google=True)
        except Exception as e:
            logger.error(f"Error updating settings: {e}")
            return render_template("settings.html", error="Failed to update settings.", has_linkedin=False, has_google=False)
            
    # GET Request - Fetch status
    has_linkedin = False
    has_google = False
    try:
        resp = requests.get(f"{BACKEND_URL}/api/settings/{company_id}")
        if resp.status_code == 200:
            data = resp.json()
            has_linkedin = data.get("has_linkedin", False)
            has_google = data.get("has_google", False)
    except Exception as e:
        logger.error(f"Error fetching settings: {e}")
        
    return render_template("settings.html", has_linkedin=has_linkedin, has_google=has_google)

@app.route("/apply/<job_id>")
def apply(job_id):
    """Public page for candidates to apply for a job."""
    return render_template("apply.html", job_id=job_id)

@app.route("/api/status/<thread_id>")
def api_status(thread_id):
    """Proxy the status fetch to the backend to avoid CORS and keep the frontend decoupled."""
    try:
        resp = requests.get(f"{BACKEND_URL}/status/{thread_id}")
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        logger.error(f"Error fetching status for thread {thread_id}: {CustomException(e, sys)}")
        return jsonify({"error": str(e)}), 500

@app.route("/delete_job/<job_id>", methods=["POST"])
def delete_job(job_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
        
    try:
        resp = requests.delete(f"{BACKEND_URL}/api/jobs/{job_id}")
        if resp.status_code != 200:
            logger.error(f"Failed to delete job {job_id}")
    except Exception as e:
        logger.error(f"Error deleting job: {e}")
        
    return redirect(url_for("index"))

@app.route("/api/resume/<thread_id>", methods=["POST"])
def api_resume(thread_id):
    """Proxy the resume request to the backend."""
    try:
        resp = requests.post(f"{BACKEND_URL}/resume/{thread_id}", json=request.json)
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        logger.error(f"Error resuming thread {thread_id}: {CustomException(e, sys)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(port=5000, debug=True)
