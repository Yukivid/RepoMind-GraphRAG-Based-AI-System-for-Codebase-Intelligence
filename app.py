import streamlit as st
import os

from clone_repo import clone_repo
from parser import parse_repo
from graph_builder import build_knowledge_graph, save_knowledge_graph, load_knowledge_graph
from chunker import chunk_python_file
from retriever import graph_rag_retrieve
from graph_visualizer import visualize_graph
from sentence_transformers import SentenceTransformer

st.set_page_config("AI Code Analysis", layout="wide")
st.title("🧠 AI Code Analysis Tool")

repo_url = st.sidebar.text_input(
    "GitHub Repository",
    "https://github.com/pallets/flask"
)

if st.sidebar.button("Analyze Repository"):
    repo_path = clone_repo(repo_url)

    graph = load_knowledge_graph(repo_path)
    if graph is None:
        symbols = parse_repo(repo_path)
        graph = build_knowledge_graph(symbols)
        save_knowledge_graph(graph, repo_path)

    chunks = []
    for root, _, files in os.walk(repo_path):
        for f in files:
            if f.endswith(".py"):
                chunks.extend(chunk_python_file(os.path.join(root, f)))

    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode([c["code"] for c in chunks])
    for i, c in enumerate(chunks):
        c["embedding"] = embeddings[i]

    st.session_state.graph = graph
    st.session_state.chunks = chunks
    st.session_state.graph_html = visualize_graph(graph)

# ---- GRAPH FIRST ----
st.header("📊 Knowledge Graph")

if "graph_html" in st.session_state:
    st.components.v1.html(
        open(st.session_state.graph_html).read(),
        height=1200,
        scrolling=True
    )
else:
    st.info("Analyze a repository to view the graph.")

# ---- QUERY BELOW ----
st.header("🔎 Ask a Question")

query = st.text_input("Your question")

if st.button("Run Query") and "graph" in st.session_state:
    results = graph_rag_retrieve(
        query,
        st.session_state.graph,
        st.session_state.chunks
    )

    for r in results:
        st.code(r["primary"]["code"][:2000], language="python")
