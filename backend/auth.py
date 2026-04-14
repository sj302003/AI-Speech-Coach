from functools import wraps
from flask import request, jsonify
from db import db
from models import User
from dotenv import load_dotenv
import os
import jwt
import requests

load_dotenv()

# 🔹 CHANGE THIS to your real Clerk issuer
CLERK_ISSUER = "https://talented-chow-95.clerk.accounts.dev"
JWKS_URL = f"{CLERK_ISSUER}/.well-known/jwks.json"


def get_jwks():
    return requests.get(JWKS_URL).json()["keys"]


def verify_clerk_token(token):
    jwks = get_jwks()
    unverified_header = jwt.get_unverified_header(token)
    key = next(k for k in jwks if k["kid"] == unverified_header["kid"])
    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)

    payload = jwt.decode(
        token,
        public_key,
        algorithms=["RS256"],
        audience=None,
        issuer=CLERK_ISSUER
    )

    return payload


def clerk_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return jsonify({"error": "Missing token"}), 401

        token = auth_header.replace("Bearer ", "")

        try:
            payload = verify_clerk_token(token)
            clerk_user_id = payload.get("sub")

            # 🔹 Save user if not exists
            user = User.query.filter_by(clerk_user_id=clerk_user_id).first()
            if not user:
                user = User(clerk_user_id=clerk_user_id)
                db.session.add(user)
                db.session.commit()

            request.user = clerk_user_id

        except Exception as e:
            print("AUTH ERROR:", e)
            return jsonify({"error": "Invalid token"}), 401

        return f(*args, **kwargs)

    return decorated
