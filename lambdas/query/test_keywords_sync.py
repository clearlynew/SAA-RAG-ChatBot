import pathlib

HERE = pathlib.Path(__file__).parent


def test_tokenizer_copies_are_identical():
    a = (HERE / "keywords.py").read_text()
    b = (HERE.parent / "ingest" / "keywords.py").read_text()
    assert a == b, "keywords.py differs between ingest and query"
