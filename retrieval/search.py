# retrieval/search.py
import faiss
import numpy as np
import json
from sentence_transformers import SentenceTransformer

EMB_MODEL = "all-mpnet-base-v2"
INDEX_PATH = "index.faiss"
EMB_PATH = "embeddings.npy"
META_PATH = "emb_meta.jsonl"

class Retriever:
    def __init__(self, index_path=INDEX_PATH, meta_path=META_PATH, emb_model=EMB_MODEL):
        self.index = faiss.read_index(index_path)
        self.meta = [json.loads(l) for l in open(meta_path, "r", encoding="utf-8")]
        self.model = SentenceTransformer(emb_model)

    def query(self, text: str, top_k: int = 5):
        q_emb = self.model.encode([text], convert_to_numpy=True)
        faiss.normalize_L2(q_emb)
        D, I = self.index.search(q_emb, top_k)
        results = []
        for score, idx in zip(D[0], I[0]):
            if idx < 0:
                continue
            m = self.meta[idx].copy()
            m["score"] = float(score)
            m["chunk_id"] = int(idx)
            results.append(m)
        return results

if __name__ == "__main__":
    r = Retriever()
    q = input("Query> ")
    res = r.query(q, top_k=5)
    import pprint
    pprint.pprint(res)
