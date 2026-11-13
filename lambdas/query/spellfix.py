import difflib
import json
import pathlib

_VOCAB = None
_BY_LEN = {}


def set_vocab(vocab):
    global _VOCAB, _BY_LEN
    _VOCAB = dict(vocab)
    _BY_LEN = {}
    for t, df in _VOCAB.items():
        if df >= 2:                      # words seen once could be typos in the source itself
            _BY_LEN.setdefault(len(t), []).append(t)


def _load():
    if _VOCAB is None:
        p = pathlib.Path(__file__).with_name("vocab.json")
        set_vocab(json.loads(p.read_text()) if p.exists() else {})
    return _VOCAB


def correct_token(tok, min_len=5, cutoff=0.82):
    vocab = _load()
    if not vocab or tok in vocab or len(tok) < min_len or not tok.isalpha():
        return tok                       # known word, too short, or not a plain word: leave it
    pool = [t for n in range(len(tok) - 2, len(tok) + 3) for t in _BY_LEN.get(n, [])]
    close = difflib.get_close_matches(tok, pool, n=5, cutoff=cutoff)
    if not close:
        return tok
    return max(close, key=lambda t: (round(difflib.SequenceMatcher(None, tok, t).ratio(), 2), vocab[t]))
