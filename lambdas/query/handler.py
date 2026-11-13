import json
import os
import time
import traceback

import boto3

from answer import answer_question
from validation import cache_key, parse_question

CACHE_TABLE = os.environ["CACHE_TABLE"]
DAILY_LIMIT = int(os.environ.get("DAILY_LIMIT", "500"))
CACHE_TTL_SECONDS = 24 * 3600

cache_table = boto3.resource("dynamodb").Table(CACHE_TABLE)


def respond(status, body):
    # CORS headers are added by API Gateway, not here
    return {"statusCode": status,
            "headers": {"content-type": "application/json"},
            "body": json.dumps(body)}


def cache_get(key):
    try:
        item = cache_table.get_item(Key={"query_hash": key}).get("Item")
        if item and int(item["ttl"]) > time.time():   # DynamoDB TTL deletes lazily
            return json.loads(item["response"])
    except Exception as e:
        print("cache read failed:", e)
    return None


def cache_put(key, body):
    try:
        cache_table.put_item(Item={
            "query_hash": key,
            "response": json.dumps(body),
            "ttl": int(time.time()) + CACHE_TTL_SECONDS,
        })
    except Exception as e:
        print("cache write failed:", e)


def under_daily_limit():
    """Atomic counter, one row per UTC day. Counts uncached questions only."""
    day = time.strftime("%Y-%m-%d", time.gmtime())
    r = cache_table.update_item(
        Key={"query_hash": f"daily#{day}"},
        UpdateExpression="ADD n :one SET #t = :ttl",
        ExpressionAttributeNames={"#t": "ttl"},
        ExpressionAttributeValues={":one": 1, ":ttl": int(time.time()) + 3 * 86400},
        ReturnValues="UPDATED_NEW",
    )
    return int(r["Attributes"]["n"]) <= DAILY_LIMIT


def public_view(r):
    """Only what the browser needs. Never return the raw chunk text."""
    return {
        "answer": r["answer"],
        "refused": r["refused"],
        "sources": [{"n": s["n"], "doc": s["doc"], "heading_path": s["heading_path"]}
                    for s in r["sources"]],
        "latency_ms": r["latency_ms"],
    }


def handler(event, context):
    question, err = parse_question(event)
    if err:
        return respond(400, {"error": err})

    key = cache_key(question)
    hit = cache_get(key)
    if hit:
        hit["cached"] = True
        print(json.dumps({"cached": True, "q_len": len(question)}))
        return respond(200, hit)

    try:
        if not under_daily_limit():
            return respond(429, {"error": "Daily question limit reached. Please try again tomorrow."})
        result = answer_question(question)
    except Exception:
        traceback.print_exc()          # full details go to CloudWatch only
        return respond(500, {"error": "Something went wrong. Please try again."})

    body = public_view(result)
    cache_put(key, body)
    body["cached"] = False
    # log shape and timing, not the question text (users may type personal details)
    print(json.dumps({"cached": False, "q_len": len(question), "refused": body["refused"],
                      "latency_ms": body["latency_ms"]}))
    return respond(200, body)
