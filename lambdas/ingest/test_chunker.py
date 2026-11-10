from chunker import chunk_markdown, MAX_TOKENS


def test_heading_paths():
    doc = "# A\n\nintro\n\n## B\n\nbody text"
    paths = [c["heading_path"] for c in chunk_markdown(doc, "d", "d.md")]
    assert paths == ["A", "A > B"]


def test_hash_inside_code_is_not_a_heading():
    doc = "# A\n\n```\n# not a heading\nx = 1\n```\n"
    chunks = chunk_markdown(doc, "d", "d.md")
    assert len(chunks) == 1 and "# not a heading" in chunks[0]["text"]


def test_long_section_is_split_and_under_max():
    doc = "# Big\n\n" + "This is a sentence about S3 storage. " * 400
    chunks = chunk_markdown(doc, "d", "d.md")
    assert len(chunks) > 1
    assert all(c["token_count"] <= MAX_TOKENS for c in chunks)


def test_ids_are_unique_and_formatted():
    doc = "# A\n\n" + "Sentence one is here. " * 300 + "\n\n# B\n\nshort"
    ids = [c["chunk_id"] for c in chunk_markdown(doc, "doc1", "doc1.md")]
    assert len(ids) == len(set(ids))
    assert all(i.startswith("doc1#") for i in ids)


def test_table_is_not_split():
    table = "| a | b |\n|---|---|\n| 1 | 2 |\n| 3 | 4 |"
    chunks = chunk_markdown(f"# T\n\n{table}", "d", "d.md")
    assert table in chunks[0]["text"]


def test_bom_is_removed():
    chunks = chunk_markdown("\ufeff# Title\n\nbody", "d", "d.md")
    assert chunks[0]["heading_path"] == "Title"
