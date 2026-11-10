import json
import os
import urllib.parse
from collections import Counter

import boto3
from botocore.config import Config

from chunker import chunk_markdown
from keywords import tokenize

REGION = os.environ.get("AWS_REGION", "us-east-1")
EMBED_MODEL_ID = os.environ.get("EMBED_MODEL_ID", "amazon.titan-embed-text-v2:0")
VECTOR_BUCKET = os.environ["VECTOR_BUCKET"]
VECTOR_INDEX = os.environ["VECTOR_INDEX"]

# Retries with backoff: Bedrock throttles if we send too fast.
cfg = Config(retries={"max_attempts": 8, "mode": "adaptive"})
s3 = boto3.client("s3", region_name=REGION, config=cfg)
bedrock = boto3.client("bedrock-runtime", region_name=REGION, config=cfg)
s3vectors = boto3.client("s3vectors", region_name=REGION, config=cfg)
ddb = boto3.resource("dynamodb", region_name=REGION)

chunks_table = ddb.Table(os.environ["CHUNKS_TABLE"])
terms_table = ddb.Table(os.environ["TERMS_TABLE"])
docstats_table = ddb.Table(os.environ["DOCSTATS_TABLE"])

VECTOR_BATCH = 100


def embed(text: str) -> list[float]:
    resp = bedrock.invoke_model(
        modelId=EMBED_MODEL_ID,
        body=json.dumps({"inputText": text, "dimensions": 1024, "normalize": True}),
    )
    return json.loads(resp["body"].read())["embedding"]


def process_document(bucket: str, key: str) -> int:
    body = s3.get_object(Bucket=bucket, Key=key)["Body"].read().decode("utf-8")
    doc_id = os.path.splitext(os.path.basename(key))[0]
    chunks = chunk_markdown(body, doc_id, key)

    vectors = []
    with chunks_table.batch_writer() as cw, \
         terms_table.batch_writer() as tw, \
         docstats_table.batch_writer() as sw:
        for c in chunks:
            # 1) chunk text
            cw.put_item(Item=c)

            # 2) keyword index: one row per (term, chunk) with the count
            tokens = tokenize(c["text"])
            for term, tf in Counter(tokens).items():
                tw.put_item(Item={"term": term, "chunk_id": c["chunk_id"], "tf": tf})

            # 3) chunk length, for scoring later
            sw.put_item(Item={"chunk_id": c["chunk_id"], "length": len(tokens)})

            # 4) the vector
            vectors.append({
                "key": c["chunk_id"],
                "data": {"float32": embed(c["text"])},
                "metadata": {"doc_id": doc_id},
            })

    for i in range(0, len(vectors), VECTOR_BATCH):
        s3vectors.put_vectors(
            vectorBucketName=VECTOR_BUCKET,
            indexName=VECTOR_INDEX,
            vectors=vectors[i:i + VECTOR_BATCH],
        )
    return len(chunks)


def targets(event):
    """Yield (bucket, key). Accepts a manual test event or an SQS-wrapped S3 event."""
    if "bucket" in event and "key" in event:
        yield event["bucket"], event["key"]
        return
    for record in event.get("Records", []):
        body = json.loads(record["body"])
        for r in body.get("Records", []):   # S3's own "test event" has none; skipped
            yield r["s3"]["bucket"]["name"], urllib.parse.unquote_plus(r["s3"]["object"]["key"])


def handler(event, context):
    total = 0
    for bucket, key in targets(event):
        if not key.endswith(".md"):
            print(f"skipping {key} (not .md)")
            continue
        n = process_document(bucket, key)
        print(f"ingested {key}: {n} chunks")
        total += n
    return {"chunks_ingested": total}
