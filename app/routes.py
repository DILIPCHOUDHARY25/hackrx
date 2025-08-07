from flask import Blueprint, render_template, request, jsonify
import requests
import os

ui = Blueprint("ui", __name__)

@ui.route("/", methods=["GET", "POST"])
def index():
    answers = None
    error = None

    if request.method == "POST":
        pdf_url = request.form.get("pdf_url")
        questions_text = request.form.get("questions")
        questions = [q.strip() for q in questions_text.split("\n") if q.strip()]

        try:
            response = requests.post(
                "http://localhost:5000/api/v1/hackrx/run",
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Authorization": f"Bearer {os.getenv('API_SECRET_KEY')}"
                },
                json={
                    "documents": pdf_url,
                    "questions": questions
                },
                timeout=90
            )
            response.raise_for_status()
            answers = response.json().get("answers")
        except Exception as e:
            error = str(e)

    return render_template("index.html", answers=answers, error=error)
