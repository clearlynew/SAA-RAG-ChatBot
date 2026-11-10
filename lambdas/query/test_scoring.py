from scoring import bm25_idf, bm25_term_score, rrf_merge


def test_chunk_in_both_lists_beats_chunk_in_one():
    merged = rrf_merge([["a", "b", "c"], ["b", "d"]])
    assert merged[0][0] == "b"


def test_single_list_keeps_its_order():
    assert [i for i, _ in rrf_merge([["x", "y", "z"]])] == ["x", "y", "z"]


def test_empty_input():
    assert rrf_merge([]) == []
    assert rrf_merge([[], []]) == []


def test_rare_term_weighs_more():
    assert bm25_idf(100, 2) > bm25_idf(100, 50)


def test_more_occurrences_score_higher():
    idf = bm25_idf(100, 5)
    assert bm25_term_score(3, 100, 100, idf) > bm25_term_score(1, 100, 100, idf)


def test_longer_chunk_scores_lower_for_same_count():
    idf = bm25_idf(100, 5)
    assert bm25_term_score(2, 50, 100, idf) > bm25_term_score(2, 400, 100, idf)
