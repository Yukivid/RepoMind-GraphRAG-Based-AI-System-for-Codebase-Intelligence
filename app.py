# app.py
import os
import traceback
import streamlit as st
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langsmith import Client

from ingest import ingest_repo, VECTOR_DIR, TARGET_REPO_DIR
from retrieval_engine import (
    infer_metadata_filters,
    dedupe_docs,
    rewrite_query,
    multihop_query_generation,
)
from directory_summary import generate_directory_summary
from agent_orchestrator import run_pipeline

load_dotenv()
st.set_page_config(page_title="Chat with Your Codebase", layout="wide")
st.title("💬 Chat with Your Codebase – Hierarchical Agent Pipeline")

try:
    client = Client()
    print("LangSmith ready")
except Exception:
    pass

EMBED_MODEL = "thenlper/gte-base"
DEFAULT_REPO_PATH = TARGET_REPO_DIR

st.subheader("📦 Ingest a New Repository")
repo_url = st.text_input("🔗 Enter GitHub Repository URL or Local Path")
if st.button("🚀 Start Ingestion"):
    if not repo_url.strip():
        st.warning("Enter repo URL or local path")
    else:
        try:
            ingest_repo(repo_url.strip())
            st.success("Ingest complete")
        except Exception as e:
            st.error(f"Ingest failed: {e}")
            st.text(traceback.format_exc())

st.divider()
st.subheader("🤖 Orchestrator Agent (Interpreter→Retriever→Code→Inspector/Refactor/Dependency→Formatter)")
agent_query = st.text_area("Instruction for agent", height=140)
if st.button("Run Orchestrator"):
    if not agent_query.strip():
        st.warning("Enter instruction")
    else:
        with st.spinner("Running pipeline..."):
            try:
                out = run_pipeline(agent_query, repo_path=DEFAULT_REPO_PATH)
                st.markdown("### Final Answer")
                st.markdown(out["final"])
                st.write("### Pipeline internals")
                st.json(out["pipeline"])
            except Exception as e:
                st.error(f"Pipeline failed: {e}")
                st.text(traceback.format_exc())

st.divider()
st.subheader("📁 Directory Summary")
dir_to_sum = st.text_input("Directory to summarize (relative to repo)")
if st.button("Summarize Directory"):
    if not os.path.exists(DEFAULT_REPO_PATH):
        st.error("Please ingest repo first")
    elif not dir_to_sum.strip():
        st.warning("Enter directory")
    else:
        try:
            llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.2)
            summary = generate_directory_summary(llm, DEFAULT_REPO_PATH, dir_to_sum.strip())
            st.markdown(summary)
        except Exception as e:
            st.error(f"Failed: {e}")
            st.text(traceback.format_exc())

# RAG section (light)
if not os.path.exists(VECTOR_DIR):
    st.warning("Ingest repository to enable retrieval UI")
    st.stop()

embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
vectorstore = FAISS.load_local(VECTOR_DIR, embeddings, allow_dangerous_deserialization=True)
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.2)

prompt = ChatPromptTemplate.from_template("""
You are an assistant helping a developer understand code.
Context:
{context}
Sources:
{sources}
Question: {input}
Respond with: summary, explanation, where in code (path: start–end).
""")

st.subheader("💡 Ask Questions About Your Codebase")
query = st.text_input("Question (e.g., where is login implemented?)")
if query:
    with st.spinner("Running retrieval..."):
        try:
            rewritten = rewrite_query(llm, query)
            subqs = multihop_query_generation(llm, rewritten)
            docs_and_scores = vectorstore.similarity_search_with_score(rewritten, k=6)
            docs = [d for d, _ in docs_and_scores]
            docs = dedupe_docs(docs)[:4]
            # build context
            context_parts = []
            sources = []
            for i, d in enumerate(docs, start=1):
                m = d.metadata or {}
                context_parts.append(f"### Source {i}: {m.get('path')} ({m.get('start_line')}-{m.get('end_line')})\n{d.page_content[:1200]}")
                sources.append(f"{m.get('path')}: {m.get('start_line')}-{m.get('end_line')}")
            context_str = "\n\n-----\n\n".join(context_parts)
            sources_str = "\n".join(sources)
            messages = prompt.format_messages(context=context_str, sources=sources_str, input=query)
            resp = llm.invoke(messages)
            ans = getattr(resp, "content", None) or getattr(resp, "text", "")
            st.markdown(ans or "No answer")
        except Exception as e:
            st.error(f"Error: {e}")
            st.text(traceback.format_exc())
