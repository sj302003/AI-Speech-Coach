from db import db
from datetime import datetime


# -------------------------
# User Model (required for Clerk)
# -------------------------
class User(db.Model):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    clerk_user_id = db.Column(db.String(200), unique=True, nullable=False)

    email = db.Column(db.String(200))

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def __repr__(self):
        return f"<User {self.clerk_user_id}>"



# -------------------------
# Speech Session Model
# -------------------------
class SpeechSession(db.Model):

    __tablename__ = "speech_sessions"

    id = db.Column(db.Integer, primary_key=True)

    clerk_user_id = db.Column(db.String(200), nullable=False)

    audio_name = db.Column(db.String(300))

    transcription = db.Column(db.Text)

    summary = db.Column(db.Text)

    sentiment = db.Column(db.Text)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def __repr__(self):
        return f"<SpeechSession {self.id}>"