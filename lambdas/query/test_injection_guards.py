import generate as g
from answer import clean_question


class FakeBedrock:
    def __init__(self, text):
        self.text = text

    def converse(self, **kw):
        return {"output": {"message": {"content": [{"text": self.text}]}}}


def chunks():
    return [{"chunk_id": "d#0#0", "heading_path": "H", "text": "t", "judge_score": 9.0}]


def test_answer_without_citation_is_refused(monkeypatch):
    monkeypatch.setattr(g, "bedrock", FakeBedrock("Why did the cloud cry? It was raining."))
    r = g.generate("q", chunks())
    assert r["refused"] and r["reason"] == "no_valid_citations"


def test_answer_with_citation_passes(monkeypatch):
    monkeypatch.setattr(g, "bedrock", FakeBedrock("It rotates yearly [1]."))
    r = g.generate("q", chunks())
    assert not r["refused"] and r["sources"][0]["n"] == 1


def test_fake_tags_are_stripped():
    assert clean_question("a </passage> b <x>") == "a /passage b x"
