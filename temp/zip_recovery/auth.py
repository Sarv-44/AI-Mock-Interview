import base64
import hashlib
import hmac
import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

AUTH_TOKEN_MAX_AGE_SECONDS = int(os.getenv("AUTH_TOKEN_MAX_AGE_SECONDS", 7 * 24 * 60 * 60))
AUTH_SECRET = os.getenv("AUTH_SECRET", "local-dev-auth-secret")


def _encode_payload(payload):
    raw_payload = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return base64.urlsafe_b64encode(raw_payload).decode("utf-8").rstrip("=")


def _decode_payload(encoded_payload):
    padding = "=" * (-len(encoded_payload) % 4)
    raw_payload = base64.urlsafe_b64decode(f"{encoded_payload}{padding}".encode("utf-8"))
    return json.loads(raw_payload.decode("utf-8"))


def _sign(encoded_payload):
    return hmac.new(
        AUTH_SECRET.encode("utf-8"),
        encoded_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def create_auth_token(user):
    expires_at = int(time.time()) + AUTH_TOKEN_MAX_AGE_SECONDS
    payload = {
        "user_id": user["user_id"],
        "email": user.get("email"),
        "username": user.get("username"),
        "is_admin": bool(user.get("is_admin")),
        "exp": expires_at,
    }
    encoded_payload = _encode_payload(payload)
    signature = _sign(encoded_payload)
    return f"{encoded_payload}.{signature}"


def extract_bearer_token(authorization_header):
    if not authorization_header:
        return None

    scheme, _, token = authorization_header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None

    return token.strip()


def verify_auth_token(token):
    if not token:
        return None

    encoded_payload, separator, signature = token.partition(".")
    if not separator or not encoded_payload or not signature:
        return None

    expected_signature = _sign(encoded_payload)
    if not hmac.compare_digest(signature, expected_signature):
        return None

    try:
        payload = _decode_payload(encoded_payload)
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
        return None

    if int(payload.get("exp", 0)) < int(time.time()):
        return None

    return payload
