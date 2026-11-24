# index/build_faiss.py
import numpy as np
import faiss
import json

def build_index(emb_np: str = "embeddings.npy", out_index: str = "index.faiss", metric: str = "cosine"):
    X = np.load(emb_np)
    n, d = X.shape
    # we normalized earlier; use inner product on normalized vectors to get cosine
    index = faiss.IndexFlatIP(d)
    index.add(X)
    faiss.write_index(index, out_index)
    print(f"Built index {out_index} (n={n}, d={d})")

if __name__ == "__main__":
    build_index()
