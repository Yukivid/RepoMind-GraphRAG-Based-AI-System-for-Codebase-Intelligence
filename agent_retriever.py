# agent_retriever.py
from retrieval_engine import multihop_query_generation, rewrite_query
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
import os

VECTOR_DIR = "data/vector_store"
EMBED_MODEL = "thenlper/gte-base"

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.2)

def _load_faiss():
    if not os.path.exists(VECTOR_DIR):
        return None
    embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
    return FAISS.load_local(VECTOR_DIR, embeddings, allow_dangerous_deserialization=True)

def run(interp_result: dict, context: dict) -> dict:
    """
    Uses the interpreter output to generate focused retrieval queries and returns top docs list.
    Returns: {"queries":[...],"top_docs":[{"path":..., "snippet":..., "score":...}, ...]}
    """
    query = interp_result.get("notes") or interp_result.get("intent") or ""
    rewritten = rewrite_query(llm, query) if llm else query
    subqs = multihop_query_generation(llm, rewritten) if llm else [rewritten]
    vs = _load_faiss()
    top_docs = []
    if vs:
        for sq in subqs:
            docs_and_scores = vs.similarity_search_with_score(sq, k=6)
            for d, s in docs_and_scores:
                m = d.metadata or {}
                top_docs.append({
                    "path": m.get("path"),
                    "start_line": m.get("start_line"),
                    "end_line": m.get("end_line"),
                    "snippet": (d.page_content[:800] if d.page_content else ""),
                    "score": float(s)
                })
    # dedupe by path+start_line
    seen = set(); uniq=[]
    for t in top_docs:
        key=(t.get("path"), t.get("start_line"))
        if key in seen: continue
        seen.add(key); uniq.append(t)
    return {"queries": subqs, "top_docs": uniq[:12]}
