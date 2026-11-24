# embeddings/embedder.py
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

MODEL_NAME = "all-mpnet-base-v2"  # good general-purpose embedder

def embed_chunks(chunks_jsonl: str = "file_chunks.jsonl", out_emb_np: str = "embeddings.npy", out_meta: str = "emb_meta.jsonl", batch_size: int = 32):
    model = SentenceTransformer(MODEL_NAME)
    texts = []
    metas = []
    with open(chunks_jsonl, "r", encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            # we can include path and lines as prefix for better context if desired
            texts.append(rec["text"])
            metas.append(rec)
    all_emb = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        emb = model.encode(batch, show_progress_bar=False, convert_to_numpy=True)
        all_emb.append(emb)
    X = np.vstack(all_emb).astype("float32")
    # normalize for cosine similarity
    import faiss
    faiss.normalize_L2(X)
    np.save(out_emb_np, X)
    # save metadata in same order
    with open(out_meta, "w", encoding="utf-8") as f:
        for m in metas:
            f.write(json.dumps(m) + "\n")
    print(f"Saved embeddings to {out_emb_np} and metadata to {out_meta} (n={X.shape[0]}, dim={X.shape[1]})")
