import re
import time

from generate import generate
from retrieval import retrieve


def clean_question(q):
    q = re.sub(r"[<>]", " ", q)          # no fake tags
    return re.sub(r"\s+", " ", q).strip()


def answer_question(question, k=5):
    question = clean_question(question)
    t0 = time.time()
    chunks = retrieve(question, mode="hybrid_rerank", k=k)
    result = generate(question, chunks)
    result["latency_ms"] = int((time.time() - t0) * 1000)
    return result
