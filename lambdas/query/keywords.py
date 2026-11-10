import re

TOKEN = re.compile(r"[a-z0-9]+")

STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "of", "to", "in", "on", "at", "by",
    "for", "with", "as", "is", "are", "was", "were", "be", "been", "it", "its",
    "this", "that", "these", "those", "from", "can", "will", "may", "you", "your",
    "we", "our", "not", "no", "so", "than", "then", "also", "such", "into", "which",
}


def stem(word: str) -> str:
    """Very rough stemmer: 'buckets' -> 'bucket'. Not perfect, but consistent on both sides."""
    for suffix in ("ing", "ed", "es", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            return word[: -len(suffix)]
    return word


def tokenize(text: str) -> list[str]:
    return [
        stem(t) for t in TOKEN.findall(text.lower())
        if t not in STOPWORDS and len(t) > 1
    ]
