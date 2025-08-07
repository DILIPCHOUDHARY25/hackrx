from flask import Blueprint, request, jsonify
import os
from dotenv import load_dotenv
from app.rag_engine import answer_questions_from_pdf

# Load environment variables from .env
load_dotenv()

# Get secret key from environment
API_SECRET_KEY = os.getenv("API_SECRET_KEY", "test123")  # default fallback for local

# Register Blueprint with versioned prefix
api = Blueprint("api", __name__, url_prefix="/api/v1")

@api.route("/hackrx/run", methods=["POST"])
def hackrx_run():
    # 🔐 Check for Bearer Token
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "Missing Bearer token"}), 401

    token = auth_header.split(" ")[1]
    if token != API_SECRET_KEY:
        return jsonify({"error": "Invalid API key"}), 403

    # 📦 Validate JSON
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid or missing JSON body"}), 400

    pdf_url = data.get("documents")
    questions = data.get("questions")

    if not pdf_url or not isinstance(questions, list) or not all(isinstance(q, str) for q in questions):
        return jsonify({"error": "Missing or invalid 'documents' or 'questions' field"}), 400

    try:
        # 🧠 Run RAG pipeline
        answers = answer_questions_from_pdf(pdf_url, questions)
        return jsonify({"answers": answers})
    except Exception as e:
        # 🛠️ Catch unexpected errors
        return jsonify({"error": str(e)}), 500
