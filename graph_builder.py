import networkx as nx
import json
import os
from parser import extract_dataflow

def build_knowledge_graph(symbols):
    G = nx.DiGraph()

    for s in symbols:
        nid = f"{s['file']}::{s['name']}"
        G.add_node(nid, **s)

    # call edges
    for s in symbols:
        if s["type"] == "call":
            for t in symbols:
                if t["type"] == "function" and t["name"] == s["name"]:
                    G.add_edge(
                        f"{s['file']}::{s['name']}",
                        f"{t['file']}::{t['name']}",
                        relation="calls"
                    )

    # dataflow & imports
    for s in symbols:
        if s["type"] in ("function", "class"):
            for rel, tgt in extract_dataflow(s["file"]):
                G.add_edge(
                    f"{s['file']}::{s['name']}",
                    tgt,
                    relation=rel
                )

    return G

def save_knowledge_graph(graph, repo_path):
    path = os.path.join(repo_path, "knowledge_graph.json")
    data = {
        "nodes": [{"id": n, **graph.nodes[n]} for n in graph.nodes],
        "edges": [{"source": u, "target": v, **graph.edges[u, v]} for u, v in graph.edges]
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return path

def load_knowledge_graph(repo_path):
    path = os.path.join(repo_path, "knowledge_graph.json")
    if not os.path.exists(path):
        return None

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    G = nx.DiGraph()
    for n in data["nodes"]:
        nid = n.pop("id")
        G.add_node(nid, **n)
    for e in data["edges"]:
        src = e.pop("source")
        tgt = e.pop("target")
        G.add_edge(src, tgt, **e)

    return G
