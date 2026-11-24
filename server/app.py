# server/app.py
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
from retrieval.search import Retriever
import html
import textwrap

st.set_page_config(page_title="Chat with Code (MVP)", layout="wide")
st.title("Chat with Your Codebase — (MVP)")

st.markdown("""
Enter a repo path or URL to ingest (run the ingest pipeline first), or just query the already built index.
This demo expects that you have run the ingest -> chunk -> embed -> build_index steps.
""")

query = st.text_input("Ask a question about the codebase", value="Where is user authentication handled?")
k = st.number_input("Number of results", min_value=1, max_value=10, value=3)

if st.button("Search"):
    with st.spinner("Loading retriever..."):
        r = Retriever()
    with st.spinner("Searching..."):
        results = r.query(query, top_k=k)
    st.subheader("Top results (code snippet + location)")
    for i, res in enumerate(results):
        st.markdown(f"**Result {i+1} — score: {res.get('score', 0):.3f}**")
        st.markdown(f"**File:** `{res['path']}` — lines {res['start_line']}–{res['end_line']} — commit `{res.get('commit_sha','')[:8]}`")
        # show snippet with code block
        snippet = res['text']
        st.code(snippet, language=None)
        st.markdown("---")
