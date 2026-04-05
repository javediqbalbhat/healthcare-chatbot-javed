import os
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from azure.core.credentials import AzureKeyCredential
from azure.ai.language.questionanswering import QuestionAnsweringClient

load_dotenv()

ENDPOINT = os.getenv("AZURE_QA_ENDPOINT")
KEY = os.getenv("AZURE_QA_KEY")
PROJECT_NAME = os.getenv("AZURE_QA_PROJECT", "HealthcareAssistantBot")
DEPLOYMENT_NAME = os.getenv("AZURE_QA_DEPLOYMENT", "production")

if not ENDPOINT or not KEY:
    print("WARNING: Azure credentials not set")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")

app = Flask(__name__, template_folder=TEMPLATE_DIR)

def get_bot_answer(question: str) -> dict:
    client = QuestionAnsweringClient(
        endpoint=ENDPOINT,
        credential=AzureKeyCredential(KEY)
    )

    response = client.get_answers(
        question=question,
        project_name=PROJECT_NAME,
        deployment_name=DEPLOYMENT_NAME,
        top=1,
        confidence_threshold=0.2,
    )

    if response.answers:
        best = response.answers[0]
        return {
            "answer": best.answer,
            "confidence": round(best.confidence, 3),
        }

    return {
        "answer": (
            "I’m sorry, I couldn’t find an exact answer to your question. "
            "You can ask about appointments, clinic hours, services, insurance, "
            "doctor availability, or contact details."
        ),
        "confidence": None,
    }
@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json(silent=True) or {}
    question = str(data.get("question", "")).strip()

    if not question:
        return jsonify({
            "answer": "Please enter a question before sending.",
            "confidence": None
        }), 400

    try:
        result = get_bot_answer(question)
        return jsonify(result)
    except Exception as exc:
        print("ERROR in /ask:", repr(exc))
        return jsonify({
            "answer": "Sorry, the chatbot is temporarily unavailable. Please try again shortly.",
            "confidence": None,
            "error": str(exc)
        }), 500

if __name__ == "__main__":
    app.run()
