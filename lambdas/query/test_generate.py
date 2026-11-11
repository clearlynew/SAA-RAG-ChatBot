from generate import build_context, cited_numbers, generate


def test_single_and_multiple_citations():
    assert cited_numbers("A [1]. B [2][3]. C [1, 3].", 5) == [1, 2, 3]


def test_out_of_range_citations_are_ignored():
    assert cited_numbers("A [9]. B [2].", 3) == [2]


def test_no_citations():
    assert cited_numbers("plain text", 5) == []


def test_context_is_numbered_and_names_the_source():
    ctx = build_context([{"chunk_id": "doc#1#0", "heading_path": "A > B", "text": "hello"}])
    assert 'id="1"' in ctx and "doc > A > B" in ctx


def test_low_relevance_refuses_without_calling_the_model():
    chunks = [{"chunk_id": "d#0#0", "heading_path": "H", "text": "t", "judge_score": 0.0}]
    r = generate("anything", chunks)
    assert r["refused"] and r["reason"] == "low_relevance"
