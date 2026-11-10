import argparse
import json
import os
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lambdas" / "query"))

if not os.environ.get("VECTOR_BUCKET"):
    raise SystemExit("VECTOR_BUCKET is empty. export VECTOR_BUCKET=$(terraform -chdir=terraform output -raw vector_bucket_name)")

import boto3
from retrieval import CHUNKS_TABLE, retrieve

MODES = ["vector_only", "keyword_only", "hybrid"]


def norm(text):
    return " ".join(text.lower().split())      # lowercase, collapse whitespace/newlines


def load_corpus():
    """chunk_id -> normalized text, for every chunk in the index."""
    table = boto3.resource("dynamodb", region_name="us-east-1").Table(CHUNKS_TABLE)
    corpus = {}
    kw = {"ProjectionExpression": "chunk_id, #t", "ExpressionAttributeNames": {"#t": "text"}}
    while True:
        r = table.scan(**kw)
        for it in r["Items"]:
            corpus[it["chunk_id"]] = norm(it["text"])
        if "LastEvaluatedKey" not in r:
            return corpus
        kw["ExclusiveStartKey"] = r["LastEvaluatedKey"]


def is_relevant(text_norm, phrases):
    return any(norm(p) in text_norm for p in phrases)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--questions", default=str(ROOT / "eval" / "questions.json"))
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--modes", nargs="+", default=MODES, choices=MODES)
    args = ap.parse_args()
    k = args.k

    questions = json.loads(pathlib.Path(args.questions).read_text(encoding="utf-8"))
    corpus = load_corpus()
    print(f"{len(corpus)} chunks in index, {len(questions)} questions\n")

    # Label check: every question must match at least one chunk, or its score is meaningless.
    relevant = {}
    for q in questions:
        ids = {cid for cid, t in corpus.items() if is_relevant(t, q["answer_phrases"])}
        if not ids:
            raise SystemExit(f"{q['id']}: answer_phrases match NO chunk. Fix the phrase in questions.json.")
        relevant[q["id"]] = ids

    scores = {m: [] for m in args.modes}
    details = []
    for q in questions:
        rel = relevant[q["id"]]
        print(f"{q['id']}  {q['question']}   ({len(rel)} relevant chunk(s))")
        row = {"id": q["id"], "question": q["question"], "relevant": sorted(rel), "modes": {}}
        for m in args.modes:
            t0 = time.time()
            hits = retrieve(q["question"], mode=m, k=k)
            ms = (time.time() - t0) * 1000
            ids = [h["chunk_id"] for h in hits]
            flags = [cid in rel for cid in ids]
            first = flags.index(True) + 1 if True in flags else None
            found = sum(flags)
            scores[m].append({
                "hit": 1.0 if first else 0.0,
                "mrr": 1.0 / first if first else 0.0,
                "prec": found / k,
                "rec": found / len(rel),
                "ms": ms,
            })
            row["modes"][m] = {"first_relevant_rank": first, "retrieved": ids}
            print(f"    {m:<13} first relevant rank: {first if first else 'MISS'}")
        details.append(row)

    n = len(questions)
    lines = [
        f"| mode | hit@{k} | MRR | precision@{k} | recall@{k} | avg ms |",
        "|---|---|---|---|---|---|",
    ]
    for m in args.modes:
        def avg(key):
            return sum(s[key] for s in scores[m]) / n
        lines.append(f"| {m} | {avg('hit'):.2f} | {avg('mrr'):.2f} | {avg('prec'):.2f} | {avg('rec'):.2f} | {avg('ms'):.0f} |")
    table = "\n".join(lines)
    print("\n" + table)

    out = ROOT / "eval"
    (out / "results.md").write_text(
        f"# Eval results\n\n{n} questions, k={k}, {len(corpus)} chunks in index.\n\n{table}\n",
        encoding="utf-8",
    )
    (out / "results.json").write_text(json.dumps(details, indent=2), encoding="utf-8")
    print("\nwrote eval/results.md and eval/results.json")


if __name__ == "__main__":
    main()
