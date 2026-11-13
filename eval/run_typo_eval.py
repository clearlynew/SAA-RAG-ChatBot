import argparse
import json
import os
import pathlib
import random
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lambdas" / "query"))
if not os.environ.get("VECTOR_BUCKET"):
    raise SystemExit("VECTOR_BUCKET is empty. Export it first.")

import boto3
import retrieval

ap = argparse.ArgumentParser()
ap.add_argument("--mode", default="hybrid_rerank")
ap.add_argument("--k", type=int, default=5)
ap.add_argument("--seed", type=int, default=7)
args = ap.parse_args()


def norm(t):
    return " ".join(t.lower().split())


def load_corpus():
    table = boto3.resource("dynamodb", region_name="us-east-1").Table(retrieval.CHUNKS_TABLE)
    corpus, kw = {}, {"ProjectionExpression": "chunk_id, #t", "ExpressionAttributeNames": {"#t": "text"}}
    while True:
        r = table.scan(**kw)
        for it in r["Items"]:
            corpus[it["chunk_id"]] = norm(it["text"])
        if "LastEvaluatedKey" not in r:
            return corpus
        kw["ExclusiveStartKey"] = r["LastEvaluatedKey"]


def add_typos(question, rng):
    words = sorted(set(re.findall(r"[A-Za-z]{6,}", question)))
    out = question
    for w in rng.sample(words, min(2, len(words))):
        i = rng.randrange(1, len(w) - 1)
        op = rng.choice(["swap", "drop", "dup", "sub"])
        if op == "swap":
            bad = w[:i] + w[i + 1] + w[i] + w[i + 2:]
        elif op == "drop":
            bad = w[:i] + w[i + 1:]
        elif op == "dup":
            bad = w[:i + 1] + w[i] + w[i + 1:]
        else:
            bad = w[:i] + rng.choice("abcdefghijklmnopqrstuvwxyz") + w[i + 1:]
        if bad != w:
            out = re.sub(r"\b" + w + r"\b", bad, out, count=1)
    return out


qs = json.loads((ROOT / "eval" / "questions.json").read_text(encoding="utf-8"))
corpus = load_corpus()
rel, keep = {}, []
for q in qs:
    phrases = q.get("answer_phrases") or ([q["answer"]] if q.get("answer") else [])
    ids = {cid for cid, t in corpus.items() if any(norm(p) in t for p in phrases)}
    if ids:
        rel[str(q["id"])] = ids
        q["id"] = str(q["id"])
        keep.append(q)

rng = random.Random(args.seed)
typo = {q["id"]: add_typos(q["question"], rng) for q in keep}
(ROOT / "eval" / "typo_questions.json").write_text(json.dumps(typo, indent=2), encoding="utf-8")


def run(texts, spellfix):
    retrieval.SPELLFIX = spellfix
    ranks = []
    for q in keep:
        hits = retrieval.retrieve(texts[q["id"]], mode=args.mode, k=args.k)
        ids = [h["chunk_id"] for h in hits]
        ranks.append(next((i for i, c in enumerate(ids, 1) if c in rel[q["id"]]), None))
    return ranks


def summarize(ranks):
    n = len(ranks)
    return sum(r is not None for r in ranks) / n, sum(1 / r for r in ranks if r) / n


clean = run({q["id"]: q["question"] for q in keep}, True)
off = run(typo, False)
on = run(typo, True)

rows = [("clean questions", clean), ("typos, spell-fix OFF", off), ("typos, spell-fix ON", on)]
lines = [f"| variant ({args.mode}, k={args.k}, {len(keep)} questions) | hit@{args.k} | MRR |", "|---|---|---|"]
for name, ranks in rows:
    h, m = summarize(ranks)
    lines.append(f"| {name} | {h:.2f} | {m:.2f} |")
print("\n".join(lines))

print("\nExamples:")
for q in keep[:5]:
    print(" ", typo[q["id"]])
print("\nQuestions where spell-fix changed the rank (off -> on):")
for q, a, b in zip(keep, off, on):
    if a != b:
        print(f"  {q['id']}: {a or 'MISS'} -> {b or 'MISS'}")

(ROOT / "eval" / "typo_results.md").write_text("\n".join(lines), encoding="utf-8")
print("\nwrote eval/typo_results.md and eval/typo_questions.json")
