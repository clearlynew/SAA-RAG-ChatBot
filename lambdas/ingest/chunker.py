import re

TARGET_TOKENS = 400   # aim for chunks about this big
MAX_TOKENS = 500      # never go above this (except code/tables)
OVERLAP_TOKENS = 50   # shared text between neighbouring chunks

HEADING = re.compile(r"^(#{1,3})\s+(.+?)\s*$")   # lines like "# Title", "## Sub"


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def parse_sections(text: str) -> list[tuple[str, str]]:
    """Split a markdown doc into (heading_path, body) pairs."""
    sections, stack, body, in_code = [], [], [], False

    def flush():
        content = "\n".join(body).strip()
        if content:
            sections.append((" > ".join(stack) or "Introduction", content))
        body.clear()

    for line in text.split("\n"):
        if line.strip().startswith("```"):
            in_code = not in_code            # a '#' inside code is not a heading
        m = None if in_code else HEADING.match(line)
        if m:
            flush()
            level = len(m.group(1))
            stack[:] = stack[: level - 1] + [m.group(2)]   # keep parents, replace this level
        else:
            body.append(line)
    flush()
    return sections


def split_blocks(body: str) -> list[str]:
    """Split a section into paragraphs/tables/code blocks (blank lines separate them,
    except inside code fences)."""
    blocks, cur, in_code = [], [], False
    for line in body.split("\n"):
        if line.strip().startswith("```"):
            in_code = not in_code
        if line.strip() == "" and not in_code:
            if cur:
                blocks.append("\n".join(cur))
                cur = []
        else:
            cur.append(line)
    if cur:
        blocks.append("\n".join(cur))
    return blocks


def split_long(block: str) -> list[str]:
    """Break an oversized paragraph on sentence boundaries. Code and tables stay whole."""
    if block.lstrip().startswith(("```", "|")) or estimate_tokens(block) <= TARGET_TOKENS:
        return [block]
    out, cur = [], ""
    for sentence in re.split(r"(?<=[.!?])\s+", block):
        if cur and estimate_tokens(cur + " " + sentence) > TARGET_TOKENS:
            out.append(cur)
            cur = sentence
        else:
            cur = f"{cur} {sentence}".strip()
    if cur:
        out.append(cur)
    return out


def overlap_tail(text: str) -> str:
    """Last ~OVERLAP_TOKENS of a chunk, starting at a word boundary. Skipped after code/tables."""
    stripped = text.rstrip()
    if stripped.endswith("```") or stripped.split("\n")[-1].startswith("|"):
        return ""
    tail = stripped[-OVERLAP_TOKENS * 4:]
    cut = tail.find(" ")
    return tail[cut + 1:] if cut != -1 else tail


def pack(blocks: list[str]) -> list[str]:
    """Group blocks into chunks of roughly TARGET_TOKENS."""
    pieces = [p for b in blocks for p in split_long(b)]
    chunks, cur = [], ""
    for piece in pieces:
        if cur and estimate_tokens(cur + "\n\n" + piece) > TARGET_TOKENS:
            chunks.append(cur)
            tail = overlap_tail(cur)
            cur = f"{tail}\n\n{piece}" if tail else piece
        else:
            cur = f"{cur}\n\n{piece}" if cur else piece
    if cur:
        chunks.append(cur)
    return chunks


def chunk_markdown(text: str, doc_id: str, source: str, topic_tags=None) -> list[dict]:
    text = text.lstrip("\ufeff")   # remove the invisible BOM some editors add
    chunks = []
    for s_idx, (path, body) in enumerate(parse_sections(text)):
        for c_idx, piece in enumerate(pack(split_blocks(body))):
            full = f"{path}\n\n{piece}"      # heading path goes in front of the text
            chunks.append({
                "chunk_id": f"{doc_id}#{s_idx}#{c_idx}",
                "doc_id": doc_id,
                "source": source,
                "heading_path": path,
                "text": full,
                "token_count": estimate_tokens(full),
                "topic_tags": topic_tags or [],
            })
    return chunks


if __name__ == "__main__":
    import pathlib
    import sys
    p = pathlib.Path(sys.argv[1])
    result = chunk_markdown(p.read_text(encoding="utf-8"), p.stem, p.name)
    print(len(result), "chunks")
    for c in result[:3]:
        print("-" * 40, c["chunk_id"], c["token_count"], "tokens")
        print(c["text"][:300])
