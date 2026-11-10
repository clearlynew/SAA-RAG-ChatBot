import pathlib
import sys

sys.path.insert(0, "lambdas/ingest")
from chunker import chunk_markdown

phrase = sys.argv[1].lower()
for p in sorted(pathlib.Path("data/md").glob("*.md")):
    for c in chunk_markdown(p.read_text(encoding="utf-8"), p.stem, p.name):
        if phrase in c["text"].lower():
            print(c["chunk_id"], "|", c["heading_path"])
