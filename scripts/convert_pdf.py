import pathlib
import re
import sys

import pymupdf4llm

sys.path.insert(0, "lambdas/ingest")
from chunker import chunk_markdown   # preview with the real chunker


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def clean(md):
    keep = []
    for line in md.split("\n"):
        s = line.strip()
        if re.fullmatch(r"\d{1,4}", s):                 # lone page numbers
            continue
        if re.search(r"\.{4,}\s*\d+\s*$", s):           # table-of-contents lines
            continue
        if re.match(r"#{1,6}\s", s):
            line = line.replace("**", "").replace("__", "")
        keep.append(line.rstrip())
    return re.sub(r"\n{3,}", "\n\n", "\n".join(keep)).strip() + "\n"


pdf = pathlib.Path(sys.argv[1])
md = clean(pymupdf4llm.to_markdown(str(pdf), header=False, footer=False))

out = pathlib.Path("data/md")
out.mkdir(parents=True, exist_ok=True)
dest = out / f"{slug(pdf.stem)}.md"
dest.write_text(md, encoding="utf-8")

headings = sum(1 for l in md.split("\n") if re.match(r"#{1,3}\s", l))
chunks = chunk_markdown(md, dest.stem, dest.name)
tiny = sum(1 for c in chunks if c["token_count"] < 30)
avg = sum(c["token_count"] for c in chunks) // max(1, len(chunks))
print(f"wrote {dest}: {len(md):,} chars, {headings} headings")
print(f"{len(chunks)} chunks, avg {avg} tokens, {tiny} tiny (<30 tokens)")
for c in chunks[:: max(1, len(chunks) // 3)][:3]:
    print("-" * 50, "\n", c["heading_path"], "\n", c["text"][:250])
