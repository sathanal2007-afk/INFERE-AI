from openai import OpenAI
import os
import uuid

# -----------------------------
# SESSION STORAGE (IN-MEMORY - FREE)
# -----------------------------
sessions = {}

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)
# -----------------------------
# AI RESPONSE FUNCTION
# -----------------------------

def get_ai_response(message):
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a helpful medical assistant. Provide safe home remedies. If serious, advise doctor visit."},
            {"role": "user", "content": message}
        ],
        max_tokens=500
    )
    return response.choices[0].message.content


# -----------------------------
# FASTAPI SETUP
# -----------------------------

from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import pandas as pd
from langdetect import detect

app = FastAPI()
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
sessions={}

# -----------------------------
# LOAD MODELS
# -----------------------------

import os
import joblib
import gdown

# File paths
GENERAL_MODEL_PATH = "general_model.pkl"
VECTORIZER_PATH = "vectorizer.pkl"
SEPSIS_MODEL_PATH = "sepsis_model.pkl"

# Load general disease model
general_model = joblib.load(GENERAL_MODEL_PATH)
vectorizer = joblib.load(VECTORIZER_PATH)

# Download sepsis model if not present
if not os.path.exists(SEPSIS_MODEL_PATH):
    url = "https://drive.google.com/uc?id=1kPcIP0AEkYnebsDGWGSKt9y9F3V00voh"
    gdown.download(url, SEPSIS_MODEL_PATH, quiet=False)

# Load sepsis model
sepsis_model = joblib.load(SEPSIS_MODEL_PATH)

# Get feature names
sepsis_features = sepsis_model.feature_names_in_

# -----------------------------
# MEMORY STORAGE
# -----------------------------

conversation_state = {
    "awaiting_more_symptoms": False,
    "previous_message": ""
}

# -----------------------------
# REQUEST MODELS
# -----------------------------

class ChatRequest(BaseModel):
    message: str
    session_id:str|None=None

class SepsisRequest(BaseModel):
    HR: float
    Temp: float
    SBP: float
    Resp: float
    O2Sat: float
    language: str = "en"

# -----------------------------
# LANGUAGE FUNCTIONS
# -----------------------------

def detect_language(text):
    try:
        return detect(text)
    except:
        return "en"

def translate_to_english(text):
    prompt = f"Translate the following text to English only:\n\n{text}"
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a translator."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=300
    )
    return response.choices[0].message.content.strip()

def translate_back(text, target_lang):
    if target_lang == "en":
        return text

    prompt = f"Translate the following medical response into {target_lang} language clearly:\n\n{text}"

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a professional medical translator."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500
    )
    return response.choices[0].message.content.strip()

# -----------------------------
# ANALYZE MESSAGE
# -----------------------------

def analyze_message(message):

    message = message.lower()
    input_vector = vectorizer.transform([message])
    probs = general_model.predict_proba(input_vector)[0]

    top_index = probs.argmax()
    confidence = probs[top_index]
    prediction = general_model.classes_[top_index]

    danger_keywords = [
        "high fever",
        "confusion",
        "low bp",
        "low blood pressure",
        "rapid heart rate",
        "shortness of breath"
    ]

    if sum(word in message for word in danger_keywords) >= 2:
        return "emergency", None, None

    if confidence >= 0.60:
        return "high", prediction, confidence
    else:
        return "low", None, confidence

# -----------------------------
# SEPSIS FUNCTION
# -----------------------------

def predict_sepsis(HR, Temp, SBP, Resp, O2Sat):

    input_data = pd.DataFrame(columns=sepsis_features)
    input_data.loc[0] = 0

    if "HR" in sepsis_features:
        input_data.at[0, "HR"] = HR
    if "Temp" in sepsis_features:
        input_data.at[0, "Temp"] = Temp
    if "SBP" in sepsis_features:
        input_data.at[0, "SBP"] = SBP
    if "Resp" in sepsis_features:
        input_data.at[0, "Resp"] = Resp
    if "O2Sat" in sepsis_features:
        input_data.at[0, "O2Sat"] = O2Sat

    risk = sepsis_model.predict_proba(input_data)[0][1]
    return risk

# -----------------------------
# CHAT ROUTE
# -----------------------------

@app.post("/chat")
def chat(request: ChatRequest):

    global conversation_state

    # -----------------------------
    # SESSION HANDLING (MUST BE INSIDE FUNCTION)
    # -----------------------------
    if not request.session_id:
        session_id = str(uuid.uuid4())
        sessions[session_id] = {"history": []}
    else:
        session_id = request.session_id
        if session_id not in sessions:
            sessions[session_id] = {"history": []}

    try:
        original_message = request.message
        detected_lang = detect_language(original_message)

        # Translate input
        if detected_lang != "en":
            user_message = translate_to_english(original_message).lower()
        else:
            user_message = original_message.lower()

        status, prediction, confidence = analyze_message(user_message)

        # Severity logic
        if status == "emergency":
            severity_level = "Critical"
        elif status == "high":
            severity_level = "Moderate"
        else:
            severity_level = "Low"

        # ------------------ EMERGENCY ------------------

        if status == "emergency":

            final_text = (
                "⚠ Your symptoms may indicate a serious condition. "
                "Please seek immediate medical attention."
            )

            final_text = translate_back(final_text, detected_lang)

            # ✅ SAVE HISTORY
            sessions[session_id]["history"].append({
                "user": original_message,
                "bot": final_text
            })

            return {
                "session_id": session_id,
                "condition": "Unknown",
                "confidence": 0,
                "severity": severity_level,
                "emergency": True,
                "advice": final_text,
                "language": detected_lang
            }

        # ------------------ HIGH CONFIDENCE ------------------

        if status == "high":

            ai_response = get_ai_response(user_message)

            final_text = (
                f"Home Care Advice:\n{ai_response}\n\n"
                "This is not a medical diagnosis."
            )

            final_text = translate_back(final_text, detected_lang)

            # ✅ SAVE HISTORY
            sessions[session_id]["history"].append({
                "user": original_message,
                "bot": final_text
            })

            return {
                "session_id": session_id,
                "condition": prediction,
                "confidence": round(confidence * 100, 2),
                "severity": severity_level,
                "emergency": False,
                "advice": final_text,
                "language": detected_lang
            }

        # ------------------ LOW CONFIDENCE ------------------

        if status == "low":

            conversation_state["awaiting_more_symptoms"] = True
            conversation_state["previous_message"] = user_message

            final_text = (
                "I need a bit more information to provide a better assessment.\n"
                "Are you experiencing any other symptoms?"
            )

            final_text = translate_back(final_text, detected_lang)

            # ✅ SAVE HISTORY
            sessions[session_id]["history"].append({
                "user": original_message,
                "bot": final_text
            })

            return {
                "session_id": session_id,
                "condition": "Not clear yet",
                "confidence": round(confidence * 100, 2) if confidence else 0,
                "severity": severity_level,
                "emergency": False,
                "advice": final_text,
                "language": detected_lang
            }

    except Exception as e:
        return {"error": str(e)}
# -----------------------------
# CHAT HISTORY ROUTE (ADD HERE)
# -----------------------------
@app.get("/history/{session_id}")
def get_history(session_id: str):

    if session_id not in sessions:
        return {"error": "Session not found"}

    return {
        "session_id": session_id,
        "chat_history": sessions[session_id]["history"]
    }
# -----------------------------
# SEPSIS ROUTE
# -----------------------------

@app.post("/sepsis")
def sepsis_check(request: SepsisRequest):

    detected_lang = request.language

    risk = predict_sepsis(
        request.HR,
        request.Temp,
        request.SBP,
        request.Resp,
        request.O2Sat
    )

    if risk > 0.7:
        level = "HIGH RISK - Seek immediate medical care."
    elif risk > 0.4:
        level = "Moderate Risk - Monitor closely."
    else:
        level = "Low Risk."

    final_text = (
        f"Sepsis Risk: {round(risk * 100, 2)}%\n"
        f"Risk Level: {level}\n"
        "Educational AI prediction only."
    )

    final_text = translate_back(final_text, detected_lang)

    return {
        "risk_percentage": round(risk * 100, 2),
        "risk_level": level,
        "message": final_text,
        "language": detected_lang
    }

# -----------------------------
# HOME ROUTE
# -----------------------------

@app.get("/")
def home():

    return {"message": "AI Healthcare Chatbot is running"}
