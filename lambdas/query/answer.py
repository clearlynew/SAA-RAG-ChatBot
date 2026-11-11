import time

from generate import generate
from retrieval import retrieve


def answer_question(question, k=5):
    t0 = time.time()
    chunks = retrieve(question, mode="hybrid_rerank", k=k)
    result = generate(question, chunks)
    result["latency_ms"] = int((time.time() - t0) * 1000)
    return result
