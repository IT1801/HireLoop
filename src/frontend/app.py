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
                session["email"] = email
                session["name"] = data.get("name")
                session["setup_complete"] = data.get("setup_complete", False)
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
    company_id = session.get("company_id")
    is_logged_in = company_id is not None
    
    if is_logged_in and not session.get("setup_complete"):
        return redirect(url_for("setup"))
        
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
    
    if is_logged_in:
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
            
    return render_template("index.html", jobs=jobs, has_auth_verified=has_auth_verified, is_logged_in=is_logged_in)

@app.route("/dashboard/<thread_id>")
def dashboard(thread_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    if not session.get("setup_complete"):
        return redirect(url_for("setup"))
    return render_template("pipeline_details.html", thread_id=thread_id)

@app.route("/setup", methods=["GET", "POST"])
def setup():
    if "user_id" not in session:
        return redirect(url_for("login"))
        
    if request.method == "POST":
        name = request.form.get("name")
        phone = request.form.get("phone")
        company_name = request.form.get("company_name")
        
        try:
            resp = requests.post(f"{BACKEND_URL}/api/user/setup", json={
                "user_id": session["user_id"],
                "name": name,
                "phone": phone,
                "company_name": company_name
            })
            if resp.status_code == 200:
                session["setup_complete"] = True
                session["name"] = name
                return redirect(url_for("index"))
            else:
                return render_template("setup.html", error="Setup failed, please try again.")
        except Exception as e:
            logger.error(f"Setup failed: {e}")
            return render_template("setup.html", error="System offline.")
            
    success = request.args.get("success")
    error = request.args.get("error")
    
    # Check connection status
    has_google = False
    has_linkedin = False
    company_id = session.get("company_id")
    if company_id:
        try:
            resp = requests.get(f"{BACKEND_URL}/api/settings/{company_id}")
            if resp.status_code == 200:
                data = resp.json()
                has_google = data.get("has_google", False)
                has_linkedin = data.get("has_linkedin", False)
        except Exception as e:
            logger.error(f"Failed to fetch connection status: {e}")
            
    return render_template("setup.html", success=success, error=error, has_google=has_google, has_linkedin=has_linkedin)

@app.route("/settings", methods=["GET", "POST"])
def settings():
    if "user_id" not in session:
        return redirect(url_for("login"))
        
    if not session.get("setup_complete"):
        return redirect(url_for("setup", **request.args))
        
    company_id = session["company_id"]
    
    if request.method == "POST":
        linkedin_org_id = request.form.get("linkedin_org_id")
        linkedin_access_token = request.form.get("linkedin_access_token")
        google_credentials = request.form.get("google_credentials")
        name = request.form.get("name")
        phone = request.form.get("phone")
        
        payload = {"user_id": session["user_id"]}
        if linkedin_org_id: payload["linkedin_org_id"] = linkedin_org_id
        if linkedin_access_token: payload["linkedin_access_token"] = linkedin_access_token
        if google_credentials: payload["google_credentials"] = google_credentials
        if name: payload["name"] = name
        if phone: payload["phone"] = phone
        
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
    user_name = session.get("name", "")
    user_phone = ""
    try:
        resp = requests.get(f"{BACKEND_URL}/api/settings/{company_id}?user_id={session['user_id']}")
        if resp.status_code == 200:
            data = resp.json()
            has_linkedin = data.get("has_linkedin", False)
            has_google = data.get("has_google", False)
            user_name = data.get("name", user_name)
            user_phone = data.get("phone", "")
    except Exception as e:
        logger.error(f"Error fetching settings: {e}")
        
    return render_template("settings.html", has_linkedin=has_linkedin, has_google=has_google, user_name=user_name, user_phone=user_phone)

@app.route("/apply/<job_id>", methods=["GET", "POST"])
def apply(job_id):
    """Public page for candidates to apply for a job."""
    if request.method == "POST":
        name = request.form.get("fullName")
        email = request.form.get("email")
        contact = request.form.get("phone")
        linkedin = request.form.get("linkedin", "")
        # In a real app we'd parse the file. For now we use the LinkedIn URL or placeholder.
        resume_text = f"LinkedIn/Portfolio: {linkedin}" if linkedin else "File attached (parsing simulated)."
        
        try:
            resp = requests.post(f"{BACKEND_URL}/api/apply/{job_id}", json={
                "name": name,
                "email": email,
                "contact_number": contact,
                "resume_text": resume_text
            })
            if resp.status_code == 200:
                return render_template("apply.html", job_id=job_id, success="Application submitted successfully!")
            else:
                return render_template("apply.html", job_id=job_id, error="Failed to submit application.")
        except Exception as e:
            logger.error(f"Error submitting application: {e}")
            return render_template("apply.html", job_id=job_id, error="System error. Please try again later.")
            
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
    app.run(port=5001, debug=True)
