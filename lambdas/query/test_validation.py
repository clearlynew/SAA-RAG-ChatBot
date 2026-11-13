import base64
import json

from validation import cache_key, parse_question


def ev(body, b64=False):
    return {"body": body, "isBase64Encoded": b64}


def test_valid_question_is_trimmed():
    q, err = parse_question(ev(json.dumps({"question": "  How   does KMS work? "})))
    assert err is None and q == "How does KMS work?"


def test_base64_body():
    raw = base64.b64encode(json.dumps({"question": "hi there"}).encode()).decode()
    q, err = parse_question(ev(raw, b64=True))
    assert err is None and q == "hi there"


def test_missing_body():
    assert parse_question({})[1] is not None


def test_invalid_json():
    assert parse_question(ev("not json"))[1] is not None


def test_wrong_shape():
    assert parse_question(ev(json.dumps({"question": 5})))[1] is not None
    assert parse_question(ev(json.dumps(["x"])))[1] is not None


def test_empty_question():
    assert parse_question(ev(json.dumps({"question": "   "})))[1] is not None


def test_too_long():
    assert parse_question(ev(json.dumps({"question": "a" * 501})))[1] is not None


def test_cache_key_ignores_case():
    assert cache_key("How does KMS work?") == cache_key("how does kms work?")
