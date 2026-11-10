import os
import boto3

REGION = "us-east-1"
VECTOR_BUCKET = os.environ["VECTOR_BUCKET"]
RAW_BUCKET = os.environ["RAW_BUCKET"]

ddb = boto3.resource("dynamodb", region_name=REGION)
s3v = boto3.client("s3vectors", region_name=REGION)
s3 = boto3.client("s3", region_name=REGION)

TABLES = {
    "saa-rag-chunks": ["chunk_id"],
    "saa-rag-terms": ["term", "chunk_id"],
    "saa-rag-docstats": ["chunk_id"],
}


def wipe_table(name, keys):
    table, n = ddb.Table(name), 0
    kwargs = {
        "ProjectionExpression": ", ".join(f"#{k}" for k in keys),
        "ExpressionAttributeNames": {f"#{k}": k for k in keys},
    }
    while True:
        resp = table.scan(**kwargs)
        with table.batch_writer() as bw:
            for item in resp["Items"]:
                bw.delete_item(Key={k: item[k] for k in keys})
                n += 1
        if "LastEvaluatedKey" not in resp:
            return n
        kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]


def wipe_vectors():
    n, token = 0, None
    while True:
        kw = dict(vectorBucketName=VECTOR_BUCKET, indexName="chunks", maxResults=500)
        if token:
            kw["nextToken"] = token
        resp = s3v.list_vectors(**kw)
        keys = [v["key"] for v in resp.get("vectors", [])]
        if keys:
            s3v.delete_vectors(vectorBucketName=VECTOR_BUCKET, indexName="chunks", keys=keys)
            n += len(keys)
        token = resp.get("nextToken")
        if not token:
            return n


def wipe_test_files():
    resp = s3.list_objects_v2(Bucket=RAW_BUCKET, Prefix="test/")
    for obj in resp.get("Contents", []):
        s3.delete_object(Bucket=RAW_BUCKET, Key=obj["Key"])


if input("This deletes ALL chunks, keywords and vectors. Type yes: ") != "yes":
    raise SystemExit("cancelled")
for name, keys in TABLES.items():
    print(name, "deleted", wipe_table(name, keys))
print("vectors deleted", wipe_vectors())
wipe_test_files()
print("done")
