import re

STOPWORDS = {
    "where", "is", "the", "implemented", "does", "how",
    "what", "when", "in", "of", "a", "an"
}

def extract_query_terms(query: str):
    tokens = re.findall(r"[a-zA-Z_]+", query.lower())
    return [t for t in tokens if t not in STOPWORDS]
