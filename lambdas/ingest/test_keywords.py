from keywords import tokenize


def test_lowercases_and_drops_stopwords():
    assert "the" not in tokenize("The bucket")


def test_plural_matches_singular():
    assert tokenize("buckets") == tokenize("bucket")


def test_keeps_service_names():
    assert "s3" in tokenize("Amazon S3 and EC2")
    assert "ec2" in tokenize("Amazon S3 and EC2")
