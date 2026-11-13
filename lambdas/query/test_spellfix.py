import spellfix


def setup_module(_):
    spellfix.set_vocab({"encryption": 9, "rotation": 7, "bucket": 4})


def test_transposition_is_fixed():
    assert spellfix.correct_token("encrpytion") == "encryption"
    assert spellfix.correct_token("rotaiton") == "rotation"


def test_known_word_is_unchanged():
    assert spellfix.correct_token("bucket") == "bucket"


def test_short_words_and_numbers_are_unchanged():
    assert spellfix.correct_token("key") == "key"
    assert spellfix.correct_token("s3bucket") == "s3bucket"


def test_unrelated_word_is_unchanged():
    assert spellfix.correct_token("kubectl") == "kubectl"


def test_empty_vocab_changes_nothing():
    spellfix.set_vocab({})
    assert spellfix.correct_token("encrpytion") == "encrpytion"
