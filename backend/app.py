import os
import uuid
import requests

import assemblyai as aai

from flask import Flask, request, jsonify, render_template

from auth import clerk_required
from db import db
from models import SpeechSession
from config import ASSEMBLYAI_API_KEY, DATABASE_URL, OPENROUTER_API_KEY

# -----------------------------
# AssemblyAI Setup
# -----------------------------
aai.settings.api_key = ASSEMBLYAI_API_KEY

# -----------------------------
# Flask Setup
# -----------------------------
app = Flask(
    __name__,
    template_folder='../frontend/templates',
    static_folder='../frontend/static'
)

# -----------------------------
# Neon DB Setup
# -----------------------------
if "sslmode" not in DATABASE_URL:
    if "?" in DATABASE_URL:
        DATABASE_URL += "&sslmode=require"
    else:
        DATABASE_URL += "?sslmode=require"

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
}

db.init_app(app)

# -----------------------------
# Upload Folder
# -----------------------------
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -----------------------------
# ROUTES
# -----------------------------
@app.route("/")
def index():
    return render_template("index.html")


# -----------------------------
# ANALYZE ROUTE
# -----------------------------
@app.route("/analyze", methods=["POST"])
@clerk_required
def analyze():

    if "audio" not in request.files:
        return jsonify({"error": "No audio uploaded"}), 400

    audio = request.files["audio"]

    filepath = os.path.join(
        UPLOAD_FOLDER,
        f"{uuid.uuid4()}_{audio.filename}"
    )

    audio.save(filepath)

    try:
        # -----------------------------
        # STEP 1: TRANSCRIPTION (AssemblyAI)
        # -----------------------------
        transcriber = aai.Transcriber()

        config = aai.TranscriptionConfig(
            speech_models=[aai.SpeechModel.universal]
        )

        transcript = transcriber.transcribe(
            filepath,
            config=config
        )

        if transcript.status == aai.TranscriptStatus.error:
            print("❌ AssemblyAI Error:", transcript.error)
            return jsonify({"error": transcript.error}), 500

        transcription = transcript.text or ""

        print("\n===== TRANSCRIPTION =====")
        print(transcription)

        # -----------------------------
        # STEP 2: ANALYSIS (OpenRouter)
        # -----------------------------
        model = request.form.get("model")

        if not model:
            return jsonify({"error": "No model selected"}), 400

        print("\n🔹 MODEL SELECTED FROM FRONTEND:", model)

        system_prompt = """You are analyzing a speech transcript. 
        Evaluate it strictly based on the following instructions. 
        The speech may be in any language, including Hindi. Always provide an evaluation using the same criteria regardless of the language. Do not refuse evaluation. 
        ---

        ### Instructions:  

        1. **Scoring System**  
        - Rate out of **100** points.  
        - Three metrics: **Clarity, Confidence, Fluency**. Each metric has equal weight (≈33.3 points).  
        - Begin your response with the **overall score** (after all deductions).  

        2. **Metrics**  
        - **Clarity:** Was the speech easy to understand, logically structured, and free from ambiguity?  
        - **Confidence:** Did the speaker sound assured, persuasive, and in control?  
        - **Fluency:** Was the speech smooth, well-paced, and natural-sounding?  

        If a metric is flawless → explicitly write **“Great job!”**.  

        3. **Topic Relevance**  
        - State if the speech adequately addresses the given topic.  

        4. **Strong Points Section**  
        - List specific strengths (e.g., engaging tone, strong vocabulary, good pacing).  

        5. **Improvements Section**  
        - For each weak metric, give **detailed second-person feedback** (e.g., “You spoke too fast during transitions, which hurt clarity. Slow down slightly to improve understanding.”).  

        6. **Filler Words Analysis**  
        - Identify filler words (e.g., “um,” “uh,” “like,” “you know”).  
        - Up to **2 fillers** → highlight but no penalty.  
        - Beyond 2 → deduct points using the **Fibonacci series rule**:  
            - 3rd word: −3  
            - 4th word: −5  
            - 5th word: −8  
            - 6th word: −13, etc.  

        7. **General Feedback Section**  
        - If no faults → brief encouraging comment.  
        - If improvements → summarize main advice in 1–2 sentences.  

        ---

        ### Output Format:  

        **Overall Score: X/100**  
        **Language: [Language here]**
        ---

        ### Score Breakdown  
        - Clarity: X/33  
        - Confidence: X/33  
        - Fluency: X/33  

        ---

        ### Topic Relevance  
        [...]  

        ---

        ### Strong Points  
        [...]  

        ---

        ### Improvements  
        [...]  

        ---

        ### Filler Words Analysis  
        [...]  

        ---

        ### General Feedback  
        [...]

        Format your output in plain text only.  
        Do not use Markdown (no ###, ---, or **).  
        Use line breaks between sections.  
        Use the bullet symbol "•" for lists.  
        Each bullet point and section should start in a new line.

        Output template:

        Overall Score: X/100

        Score Breakdown:
        Clarity: X/33
        Confidence: X/33
        Fluency: X/33

        Topic Relevance:
        [Text here]

        Strong Points:
        • [Point 1]
        • [Point 2]
        • [Point 3]

        Improvements:
        Clarity:
        • [Point 1]
        • [Point 2]
        Confidence:
        • [Point 1]
        Fluency:
        • [Point 1]

        Filler Words Analysis:
        Identified: [list them]
        Count: X
        Deduction: X points

        General Feedback:
        [1–2 sentence summary]
        """

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": transcription}
            ]
        }

        # DEBUG LOGS
        # print("\n===== OPENROUTER DEBUG =====")
        # print("MODEL:", model)
        # print("URL:", "https://openrouter.ai/api/v1/chat/completions")
        # print("HEADERS:", headers)
        # print("PAYLOAD:", payload)

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload
        )

        # print("\n===== OPENROUTER RESPONSE =====")
        # print("STATUS:", response.status_code)
        # print("BODY:", response.text)

        response.raise_for_status()

        result = response.json()

        analysis = result["choices"][0]["message"]["content"]

        # -----------------------------
        # SAVE TO DB
        # -----------------------------
        session = SpeechSession(
            clerk_user_id=request.user,
            audio_name=audio.filename,
            transcription=transcription,
            summary=analysis,
            sentiment=""  # optional
        )

        db.session.add(session)
        db.session.commit()

        return jsonify({
            "transcription": transcription,
            "summary": analysis,
            "sentiment": ""
        })

    except Exception as e:
        print("\n❌ FINAL ERROR:", str(e))
        return jsonify({"error": str(e)}), 500

    finally:
        if os.path.exists(filepath):
            os.remove(filepath)


# -----------------------------
# HISTORY ROUTE
# -----------------------------
@app.route("/api/history")
@clerk_required
def history():

    sessions = SpeechSession.query.filter_by(
        clerk_user_id=request.user
    ).order_by(
        SpeechSession.created_at.desc()
    ).all()

    return jsonify([
        {
            "audio_name": s.audio_name,
            "summary": s.summary,
            "created_at": s.created_at.strftime("%Y-%m-%d %H:%M")
        }
        for s in sessions
    ])


# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)