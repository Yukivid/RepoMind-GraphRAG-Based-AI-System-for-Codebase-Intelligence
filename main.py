from clone_repo import clone_repo
from parser import parse_repo
from graph_builder import build_knowledge_graph
from chunker import chunk_python_file
from retriever import embed_chunks, graph_rag_retrieve
import os

REPO_URL = "https://github.com/pallets/flask"  # example

def main():
    repo_path = clone_repo(REPO_URL)

    print("Parsing repository...")
    symbols = parse_repo(repo_path)

    print("Building knowledge graph...")
    graph = build_knowledge_graph(symbols)

    print("Chunking code...")
    chunks = []
    for root, _, files in os.walk(repo_path):
        for f in files:
            if f.endswith(".py"):
                chunks.extend(
                    chunk_python_file(os.path.join(root, f))
                )

    print("Embedding chunks...")
    chunks = embed_chunks(chunks)

    print("\nAsk a question:")
    query = input(">> ")

    results = graph_rag_retrieve(query, graph, chunks)

    print("\n--- Answer Context ---")
    for r in results:
        print(f"\nFILE: {r['primary']['file']}")
        print(r['primary']['code'][:500])
        print("RELATED:", r["related_nodes"])

if __name__ == "__main__":
    main()
