import pytest

from rerank import parse_scores


def test_plain_json():
    assert parse_scores('[{"id":1,"score":7},{"id":2,"score":0}]', 2) == {1: 7.0, 2: 0.0}


def test_code_fence_and_chatter():
    text = 'Here you go:\n```json\n[{"id": 1, "score": 9}]\n```'
    assert parse_scores(text, 3) == {1: 9.0}


def test_scores_are_clamped():
    assert parse_scores('[{"id":1,"score":15},{"id":2,"score":-3}]', 2) == {1: 10.0, 2: 0.0}


def test_out_of_range_ids_are_ignored():
    assert parse_scores('[{"id":1,"score":5},{"id":99,"score":9}]', 2) == {1: 5.0}


def test_garbage_raises():
    with pytest.raises(ValueError):
        parse_scores("I cannot do that", 3)
