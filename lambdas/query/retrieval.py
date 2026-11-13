import json
import os
from collections import defaultdict
from rerank import rerank
from concurrent.futures import ThreadPoolExecutor
from spellfix import correct_token

import boto3
from boto3.dynamodb.conditions import Key
from botocore.config import Config

from keywords import tokenize
from scoring import bm25_idf, bm25_term_score, rrf_merge

REGION = os.environ.get("AWS_REGION", "us-east-1")
EMBED_MODEL_ID = os.environ.get("EMBED_MODEL_ID", "amazon.titan-embed-text-v2:0")
VECTOR_BUCKET = os.environ.get("VECTOR_BUCKET", "")
VECTOR_INDEX = os.environ.get("VECTOR_INDEX", "chunks")
CHUNKS_TABLE = os.environ.get("CHUNKS_TABLE", "saa-rag-chunks")
TERMS_TABLE = os.environ.get("TERMS_TABLE", "saa-rag-terms")
DOCSTATS_TABLE = os.environ.get("DOCSTATS_TABLE", "saa-rag-docstats")

K_VECTOR = int(os.environ.get("K_VECTOR", 20))
K_KEYWORD = int(os.environ.get("K_KEYWORD", 20))
RRF_K = int(os.environ.get("RRF_K", 60))
SPELLFIX = os.environ.get("SPELLFIX", "1") == "1"
RERANK_POOL = int(os.environ.get("RERANK_POOL", 15))
MAX_DF_RATIO = 0.5   # skip words that appear in more than half of all chunks

cfg = Config(retries={"max_attempts": 8, "mode": "adaptive"})
bedrock = boto3.client("bedrock-runtime", region_name=REGION, config=cfg)
s3vectors = boto3.client("s3vectors", region_name=REGION, config=cfg)
ddb = boto3.resource("dynamodb", region_name=REGION)
chunks_table = ddb.Table(CHUNKS_TABLE)
terms_table = ddb.Table(TERMS_TABLE)
docstats_table = ddb.Table(DOCSTATS_TABLE)

_lengths = None   # chunk_id -> length, loaded once and reused


def load_lengths():
    global _lengths
    if _lengths is None:
        _lengths, kw = {}, {}
        while True:
            r = docstats_table.scan(**kw)
            for it in r["Items"]:
                _lengths[it["chunk_id"]] = int(it["length"])
            if "LastEvaluatedKey" not in r:
                break
            kw["ExclusiveStartKey"] = r["LastEvaluatedKey"]
    return _lengths


def embed(text):
    resp = bedrock.invoke_model(
        modelId=EMBED_MODEL_ID,
        body=json.dumps({"inputText": text, "dimensions": 1024, "normalize": True}),
    )
    return json.loads(resp["body"].read())["embedding"]


def vector_search(question, k=K_VECTOR):
    r = s3vectors.query_vectors(
        vectorBucketName=VECTOR_BUCKET,
        indexName=VECTOR_INDEX,
        queryVector={"float32": embed(question)},
        topK=k,
        returnDistance=True,
    )
    return [v["key"] for v in r["vectors"]]          # best first


def query_term(term):
    items, kw = [], {"KeyConditionExpression": Key("term").eq(term)}
    while True:
        r = terms_table.query(**kw)
        items += [(i["chunk_id"], float(i["tf"])) for i in r["Items"]]
        if "LastEvaluatedKey" not in r:
            return items
        kw["ExclusiveStartKey"] = r["LastEvaluatedKey"]


def keyword_search(question, k=K_KEYWORD):
    lengths = load_lengths()
    n = len(lengths)
    avg = sum(lengths.values()) / n
    scores = defaultdict(float)

    tokens = tokenize(question)                          # NEW
    if SPELLFIX:                                         # NEW
        tokens = [correct_token(t) for t in tokens]      # NEW

    for term in set(tokens):                             # CHANGED (was set(tokenize(question)))
        postings = query_term(term)
        df = len(postings)
        if df == 0 or df > MAX_DF_RATIO * n:
            continue
        idf = bm25_idf(n, df)
        for chunk_id, tf in postings:
            scores[chunk_id] += bm25_term_score(tf, lengths.get(chunk_id, avg), avg, idf)
    ranked = sorted(scores.items(), key=lambda x: -x[1])
    return [cid for cid, _ in ranked[:k]]


def fetch_chunks(ids):
    if not ids:
        return {}
    keys = [{"chunk_id": i} for i in ids]
    found = {}
    while keys:
        r = ddb.batch_get_item(RequestItems={CHUNKS_TABLE: {"Keys": keys}})
        for it in r["Responses"][CHUNKS_TABLE]:
            found[it["chunk_id"]] = it
        keys = r.get("UnprocessedKeys", {}).get(CHUNKS_TABLE, {}).get("Keys", [])
    return found


def retrieve(question, mode="hybrid", k=10):
    """mode: vector_only | keyword_only | hybrid | hybrid_rerank. Returns the top-k chunks."""
    use_vector = mode in ("vector_only", "hybrid", "hybrid_rerank")
    use_keyword = mode in ("keyword_only", "hybrid", "hybrid_rerank")
    pool = max(k, RERANK_POOL) if mode == "hybrid_rerank" else k

    with ThreadPoolExecutor(max_workers=2) as ex:
        fv = ex.submit(vector_search, question) if use_vector else None
        fk = ex.submit(keyword_search, question) if use_keyword else None
        v = fv.result() if fv else []
        kw = fk.result() if fk else []
    merged = rrf_merge([lst for lst in (v, kw) if lst], k=RRF_K)[:pool]
    texts = fetch_chunks([cid for cid, _ in merged])
    hits = [
        {
            "chunk_id": cid,
            "score": score,
            "vector_rank": v.index(cid) + 1 if cid in v else None,
            "keyword_rank": kw.index(cid) + 1 if cid in kw else None,
            "heading_path": texts[cid]["heading_path"],
            "text": texts[cid]["text"],
        }
        for cid, score in merged if cid in texts
    ]
    if mode == "hybrid_rerank":
        hits = rerank(question, hits, top_n=k)     # 15 candidates in, best k out
    return hits
