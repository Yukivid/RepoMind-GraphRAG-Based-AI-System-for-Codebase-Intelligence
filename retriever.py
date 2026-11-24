import numpy as np
from sentence_transformers import SentenceTransformer
from query_understanding import extract_query_terms
from symbol_matching import symbol_match_score
from intent_detector import detect_intent

model = SentenceTransformer("all-MiniLM-L6-v2")

def graph_rag_retrieve(query, graph, chunks, top_k=5):
    intent = detect_intent(query)
    terms = extract_query_terms(query)
    q_emb = model.encode([query])[0]

    scored = []

    for c in chunks:
        node = f"{c['file']}::{c['name']}"
        lex = symbol_match_score(c["name"], c["file"], terms)
        sem = float(np.dot(q_emb, c["embedding"]))
        score = lex + sem

        if intent == "find_implementation":
            score += 2  # promote concrete definitions

        scored.append((score, node, c))

    scored.sort(reverse=True, key=lambda x: x[0])

    results = []
    seen = set()

    for _, node, c in scored:
        if node in seen or node not in graph:
            continue
        seen.add(node)

        results.append({
            "primary": c,
            "related_nodes": list(graph.successors(node))
        })

        if len(results) >= top_k:
            break

    return results
