import argparse
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lambdas" / "query"))
if not os.environ.get("VECTOR_BUCKET"):
    raise SystemExit("VECTOR_BUCKET is empty. Export it first.")

from answer import answer_question
from grounding import check_grounding

ap = argparse.ArgumentParser()
ap.add_argument("--n", type=int, default=15, help="how many in-scope questions to sample")
args = ap.parse_args()

inq = json.loads((ROOT / "eval" / "questions.json").read_text(encoding="utf-8"))
step = max(1, len(inq) // args.n)
inq = inq[::step][: args.n]
oos = json.loads((ROOT / "eval" / "oos_questions.json").read_text(encoding="utf-8"))


def run(q, check):
    try:
        r = answer_question(q["question"])
    except Exception as e:
        return {"id": q["id"], "question": q["question"], "error": str(e)}
    g = None
    if check and not r["refused"]:
        g = check_grounding(r["answer"], r["chunks"], [s["n"] for s in r["sources"]])
    return {"id": q["id"], "question": q["question"], "answer": r["answer"],
            "refused": r["refused"], "reason": r["reason"], "no_citations": r["no_citations"],
            "top_judge_score": r["top_judge_score"], "grounding": g,
            "sources": [f"[{s['n']}] {s['doc']} > {s['heading_path']}" for s in r["sources"]],
            "latency_ms": r["latency_ms"]}


print(f"{len(inq)} in-scope and {len(oos)} out-of-scope questions...")
ins = [run(q, True) for q in inq]
outs = [run(q, False) for q in oos]
ok_in = [r for r in ins if "error" not in r]
ok_out = [r for r in outs if "error" not in r]

answered = [r for r in ok_in if not r["refused"]]
graded = [r for r in answered if r["grounding"] and r["grounding"]["supported"] is not None]
summary = [
    ("In-scope questions refused (want low)", f"{sum(r['refused'] for r in ok_in)}/{len(ok_in)}"),
    ("Answers with valid citations (want all)", f"{sum(not r['no_citations'] for r in answered)}/{len(answered)}"),
    ("Answers fully supported by cited passages (judge)", f"{sum(r['grounding']['supported'] for r in graded)}/{len(graded)}"),
    ("Out-of-scope questions refused (want all)", f"{sum(r['refused'] for r in ok_out)}/{len(ok_out)}"),
    ("Errors", str(len(ins) + len(outs) - len(ok_in) - len(ok_out))),
]
lines = ["# Generation eval", "", "| check | result |", "|---|---|"]
lines += [f"| {a} | {b} |" for a, b in summary]

lines += ["", "## Top judge score (use it to tune MIN_JUDGE_SCORE)", ""]
lines += [f"- in-scope lowest: {min((r['top_judge_score'] for r in ok_in if r['top_judge_score'] is not None), default='n/a')}",
          f"- out-of-scope highest: {max((r['top_judge_score'] for r in ok_out if r['top_judge_score'] is not None), default='n/a')}"]


def block(r, title):
    out = ["", f"### {title} {r['id']}: {r['question']}"]
    if "error" in r:
        return out + [f"ERROR: {r['error']}"]
    out += [f"refused: {r['refused']} ({r['reason']}) | top judge score: {r['top_judge_score']} | {r['latency_ms']} ms",
            "", r["answer"], ""]
    out += [f"- {s}" for s in r["sources"]]
    if r["grounding"]:
        out.append(f"- judge: supported={r['grounding']['supported']} {r['grounding']['unsupported_claims']}")
    if not r["refused"] and title == "OUT OF SCOPE":
        out.append("- **FAILED: it answered an out-of-scope question**")
    out.append("- YOUR VERDICT (correct / partly / wrong): ")
    return out


lines += ["", "## In-scope answers (read these yourself)"]
for r in ins:
    lines += block(r, "IN SCOPE")
lines += ["", "## Out-of-scope answers"]
for r in outs:
    lines += block(r, "OUT OF SCOPE")

(ROOT / "eval" / "gen_results.md").write_text("\n".join(lines), encoding="utf-8")
(ROOT / "eval" / "gen_results.json").write_text(json.dumps({"in": ins, "out": outs}, indent=2), encoding="utf-8")
print("\n".join(f"{a}: {b}" for a, b in summary))
print("wrote eval/gen_results.md and eval/gen_results.json")
