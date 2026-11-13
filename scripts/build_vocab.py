import json
import pathlib
from collections import Counter

import boto3

table = boto3.resource("dynamodb", region_name="us-east-1").Table("saa-rag-terms")
df, kw = Counter(), {"ProjectionExpression": "#t", "ExpressionAttributeNames": {"#t": "term"}}
while True:
    r = table.scan(**kw)
    for it in r["Items"]:
        df[it["term"]] += 1
    if "LastEvaluatedKey" not in r:
        break
    kw["ExclusiveStartKey"] = r["LastEvaluatedKey"]

vocab = {t: c for t, c in df.items() if t.isalpha() and len(t) >= 4}
out = pathlib.Path("lambdas/query/vocab.json")
out.write_text(json.dumps(vocab, separators=(",", ":")))
print(len(vocab), "words,", out.stat().st_size // 1024, "KB")
