import math


def rrf_merge(ranked_lists, k=60):
    """Merge several ranked lists of ids. Returns [(id, score)] best first."""
    scores = {}
    for lst in ranked_lists:
        for rank, item in enumerate(lst, start=1):
            scores[item] = scores.get(item, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda x: -x[1])


def bm25_idf(n_docs, df):
    """Rarer term (small df) -> bigger weight."""
    return math.log(1 + (n_docs - df + 0.5) / (df + 0.5))


def bm25_term_score(tf, doc_len, avg_len, idf, k1=1.5, b=0.75):
    return idf * tf * (k1 + 1) / (tf + k1 * (1 - b + b * doc_len / avg_len))
