import argparse

from retrieval import retrieve

ap = argparse.ArgumentParser()
ap.add_argument("question")
ap.add_argument("--mode", default="hybrid", choices=["vector_only", "keyword_only", "hybrid"])
ap.add_argument("--k", type=int, default=5)
args = ap.parse_args()

for i, h in enumerate(retrieve(args.question, args.mode, args.k), start=1):
    print(f"\n#{i}  {h['chunk_id']}   vector_rank={h['vector_rank']}  keyword_rank={h['keyword_rank']}")
    print(f"    {h['heading_path']}")
    body = h["text"].split("\n\n", 1)[-1].replace("\n", " ")
    print(f"    {body[:250]}...")
