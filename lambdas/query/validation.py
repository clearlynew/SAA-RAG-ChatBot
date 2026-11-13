import base64
import hashlib
import json
import re

MAX_QUESTION_CHARS = 500
MAX_BODY_CHARS = 5000


def parse_question(event):
    """Return (question, error). Exactly one of the two is None."""
    body = event.get("body")
    if not body:
        return None, "Request body is required."
    if event.get("isBase64Encoded"):
        try:
            body = base64.b64decode(body).decode("utf-8")
        except Exception:
            return None, "Request body could not be decoded."
    if len(body) > MAX_BODY_CHARS:
        return None, "Request body is too large."
    try:
        data = json.loads(body)
    except ValueError:
        return None, "Request body must be valid JSON."
    if not isinstance(data, dict) or not isinstance(data.get("question"), str):
        return None, 'Request body must look like {"question": "..."}.'
    q = re.sub(r"\s+", " ", data["question"]).strip()
    if not q:
        return None, "Question is empty."
    if len(q) > MAX_QUESTION_CHARS:
        return None, f"Question is too long (max {MAX_QUESTION_CHARS} characters)."
    return q, None


def cache_key(question):
    return hashlib.sha256(question.lower().encode("utf-8")).hexdigest()
