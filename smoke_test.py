import json
import boto3

brt = boto3.client("bedrock-runtime", region_name="us-east-1")

# 1) Embedding call
resp = brt.invoke_model(
    modelId="amazon.titan-embed-text-v2:0",
    body=json.dumps({"inputText": "What is Amazon S3?", "dimensions": 1024, "normalize": True}),
)
vec = json.loads(resp["body"].read())["embedding"]
print("embedding dims:", len(vec))

# 2) Generation call
resp = brt.converse(
    modelId="us.amazon.nova-lite-v1:0",
    messages=[{"role": "user", "content": [{"text": "In one sentence, what is S3?"}]}],
    inferenceConfig={"maxTokens": 100, "temperature": 0.2},
)
print(resp["output"]["message"]["content"][0]["text"])
