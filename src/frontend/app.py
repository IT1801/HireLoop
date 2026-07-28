from flask import Flask, render_template, request, jsonify, redirect, url_for
import requests
import os
import sys
from src.components.core.logger import logger
from src.components.core.exception import CustomException

app = Flask(__name__)

# URL to the FastAPI backend running in a separate process
BACKEND_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000")

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        role = request.form.get("role")
        experience = request.form.get("experience")
        salary = request.form.get("salary")
        location = request.form.get("location")
        
        # Start the pipeline on the backend
        try:
            resp = requests.post(f"{BACKEND_URL}/start", json={
                "role": role,
                "experience": experience,
                "salary": salary,
                "location": location
            })
            resp.raise_for_status()
            data = resp.json()
            thread_id = data.get("thread_id")
            return redirect(url_for("dashboard", thread_id=thread_id))
        except Exception as e:
            logger.error(f"Error communicating with backend: {CustomException(e, sys)}")
            return f"Error communicating with backend: {str(e)}", 500
            
    return render_template("index.html")

@app.route("/dashboard/<thread_id>")
def dashboard(thread_id):
    return render_template("dashboard.html", thread_id=thread_id)

@app.route("/api/status/<thread_id>")
def api_status(thread_id):
    """Proxy the status fetch to the backend to avoid CORS and keep the frontend decoupled."""
    try:
        resp = requests.get(f"{BACKEND_URL}/status/{thread_id}")
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        logger.error(f"Error fetching status for thread {thread_id}: {CustomException(e, sys)}")
        return jsonify({"error": str(e)}), 500

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
