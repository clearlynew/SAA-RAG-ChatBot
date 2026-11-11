import sys

from answer import answer_question

r = answer_question(" ".join(sys.argv[1:]))
print("\n" + r["answer"])
if r["refused"]:
    print(f"\n[refused: {r['reason']}, top judge score = {r['top_judge_score']}]")
else:
    if r["no_citations"]:
        print("\n[warning: the answer has no valid citations]")
    for s in r["sources"]:
        print(f"  [{s['n']}] {s['doc']} > {s['heading_path']}")
print(f"\n{r['latency_ms']} ms")
