"""Pure-Python text similarity (TF-IDF and cosine), shared by rfc.py and record.py.

No dependencies. `tokenize` lower-cases, drops stop words and words shorter than three characters;
`build_tfidf` weights each document's terms against the corpus it is given; `cosine_sim` compares
two weighted vectors (0.0 to 1.0).
"""
import math
import re
from collections import Counter

STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "for", "on", "is", "are",
    "this", "that", "with", "as", "by", "be", "at", "it", "its", "from", "not",
    "into", "over", "than", "then", "when", "which", "would", "could", "should",
    "has", "have", "had", "was", "were", "will", "can", "may", "if", "but",
    "rfc", "rfcs", "one", "two", "also", "these", "those", "any", "all",
}


def tokenize(text):
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9_]*", text.lower())
    return [w for w in words if w not in STOPWORDS and len(w) > 2]


def build_tfidf(docs):
    """docs: dict[doc_id] -> list of tokens. Returns dict[doc_id] -> {term: weight}."""
    df = Counter()
    for tokens in docs.values():
        for term in set(tokens):
            df[term] += 1
    n = len(docs)
    idf = {term: math.log((n + 1) / (freq + 1)) + 1 for term, freq in df.items()}
    vectors = {}
    for doc_id, tokens in docs.items():
        tf = Counter(tokens)
        length = len(tokens) or 1
        vectors[doc_id] = {term: (count / length) * idf.get(term, 0) for term, count in tf.items()}
    return vectors


def cosine_sim(v1, v2):
    common = set(v1) & set(v2)
    dot = sum(v1[t] * v2[t] for t in common)
    n1 = math.sqrt(sum(x * x for x in v1.values()))
    n2 = math.sqrt(sum(x * x for x in v2.values()))
    if n1 == 0 or n2 == 0:
        return 0.0
    return dot / (n1 * n2)
