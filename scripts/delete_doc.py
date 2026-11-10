import os
import sys

import boto3
from boto3.dynamodb.conditions import Attr

REGION = "us-east-1"
doc_id = sys.argv[1]                      # e.g. kms-cryptographic-details
prefix = doc_id + "#"
VECTOR_BUCKET = os.environ["VECTOR_BUCKET"]
RAW_BUCKET = os.environ["RAW_BUCKET"]

ddb = boto3.resource("dynamodb", region_name=REGION)
s3v = boto3.client("s3vectors", region_name=REGION)
s3 = boto3.client("s3", region_name=REGION)


def delete_rows(table_name, keys):
    table, n = ddb.Table(table_name), 0
    kw = {
        "FilterExpression": Attr("chunk_id").begins_with(prefix),
        "ProjectionExpression": ", ".join(f"#{k}" for k in keys),
        "ExpressionAttributeNames": {f"#{k}": k for k in keys},
    }
    while True:
        r = table.scan(**kw)
        with table.batch_writer() as bw:
            for it in r["Items"]:
                bw.delete_item(Key={k: it[k] for k in keys})
                n += 1
        if "LastEvaluatedKey" not in r:
            return n
        kw["ExclusiveStartKey"] = r["LastEvaluatedKey"]


def delete_vectors():
    ids, token = [], None
    while True:
        kw = dict(vectorBucketName=VECTOR_BUCKET, indexName="chunks", maxResults=500)
        if token:
            kw["nextToken"] = token
        r = s3v.list_vectors(**kw)
        ids += [v["key"] for v in r.get("vectors", []) if v["key"].startswith(prefix)]
        token = r.get("nextToken")
        if not token:
            break
    for i in range(0, len(ids), 100):
        s3v.delete_vectors(vectorBucketName=VECTOR_BUCKET, indexName="chunks", keys=ids[i:i + 100])
    return len(ids)


if input(f"Delete everything for '{doc_id}'? Type yes: ") != "yes":
    raise SystemExit("cancelled")
print("chunks:  ", delete_rows("saa-rag-chunks", ["chunk_id"]))
print("docstats:", delete_rows("saa-rag-docstats", ["chunk_id"]))
print("terms:   ", delete_rows("saa-rag-terms", ["term", "chunk_id"]))
print("vectors: ", delete_vectors())
s3.delete_object(Bucket=RAW_BUCKET, Key=f"whitepapers/{doc_id}.md")
print("done")
