# ingest.py
import os
import re
import ast
import shutil
from datetime import timezone
from dotenv import load_dotenv
from git import Repo
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

load_dotenv()

TARGET_REPO_DIR = "repos/myrepo"
VECTOR_DIR = "data/vector_store"
EXTENSIONS = ('.py', '.js', '.java', '.ts', '.md', '.txt', '.go', '.cpp', '.c', '.h', '.rs')
EMBED_MODEL = "thenlper/gte-base"

# (For brevity, reuse the earlier extract_chunks, python_ast_parse, tree-sitter logic if available)
# We'll include simplified chunking using python ast + regex fallback

def simple_function_split(code: str, language: str = "unknown") -> list:
    lines = code.splitlines()
    n = len(lines)
    boundaries = [0]
    for i, ln in enumerate(lines):
        s = ln.strip()
        if s.startswith("def ") or s.startswith("class "):
            boundaries.append(i)
    boundaries = sorted(set(boundaries))
    chunks = []
    for i, b in enumerate(boundaries):
        start = b
        end = boundaries[i + 1] if i + 1 < len(boundaries) else n
        text = "\n".join(lines[start:end]).strip()
        if text:
            name = None
            first = lines[start].strip() if start < n else ""
            m = re.match(r'(def|class|function)\s+([A-Za-z0-9_]+)', first)
            if m:
                name = m.group(2)
            chunks.append({
                "start_line": start + 1,
                "end_line": end,
                "text": text,
                "node_type": "chunk",
                "name": name,
                "language": language,
                "parser_used": "regex_fallback",
            })
    if not chunks:
        lines = code.splitlines()
        chunks = [{"start_line":1,"end_line":len(lines),"text":code,"node_type":"file","name":None,"language":language,"parser_used":"fallback"}]
    return chunks

def python_ast_parse(text: str):
    try:
        tree = ast.parse(text)
    except Exception:
        return []
    src_lines = text.splitlines()
    chunks = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            try:
                start_line = getattr(node, "lineno", 1)
                end_line = getattr(node, "end_lineno", start_line)
                try:
                    chunk_text = ast.get_source_segment(text, node) or "\n".join(src_lines[start_line - 1:end_line])
                except Exception:
                    chunk_text = "\n".join(src_lines[start_line - 1:end_line])
                name = getattr(node, "name", None)
                chunks.append({
                    "start_line": start_line,
                    "end_line": end_line,
                    "text": chunk_text,
                    "node_type": type(node).__name__,
                    "name": name,
                    "language": "python",
                    "parser_used": "python_ast",
                })
            except Exception:
                continue
    if not chunks:
        lines = src_lines
        chunks = [{"start_line":1,"end_line":len(lines),"text":text,"node_type":"file","name":None,"language":"python","parser_used":"python_fallback"}]
    return chunks

def extract_chunks(text: str, file_ext: str):
    ext = file_ext.lower()
    if ext == ".py":
        ast_chunks = python_ast_parse(text)
        if ast_chunks:
            return ast_chunks
    return simple_function_split(text, language=ext.lstrip('.'))

def clone_or_open_repo(repo_url: str, target_dir: str = TARGET_REPO_DIR) -> str:
    if repo_url.startswith("http"):
        if os.path.exists(target_dir):
            try:
                shutil.rmtree(target_dir)
            except Exception:
                pass
        Repo.clone_from(repo_url, target_dir)
    else:
        if not os.path.exists(repo_url):
            raise FileNotFoundError(f"Local repository path not found: {repo_url}")
        target_dir = repo_url
    return os.path.abspath(target_dir)

def list_repo_files(repo_path: str):
    for root, _, files in os.walk(repo_path):
        if any(ignored in root for ignored in [".git", "venv", "node_modules", "__pycache__"]):
            continue
        for f in files:
            if f.endswith(EXTENSIONS):
                yield os.path.join(root, f)

def ingest_repo(repo_url_or_path: str):
    repo_path = clone_or_open_repo(repo_url_or_path)
    documents = []
    for file_path in list_repo_files(repo_path):
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            if not content.strip():
                continue
            ext = os.path.splitext(file_path)[1].lower()
            chunks = extract_chunks(content, ext)
            rel_path = os.path.relpath(file_path, repo_path)
            for c in chunks:
                doc_metadata = {
                    "path": rel_path,
                    "abs_path": file_path,
                    "start_line": int(c.get("start_line", 1)),
                    "end_line": int(c.get("end_line", c.get("start_line", 1))),
                    "node_type": c.get("node_type"),
                    "symbol_name": c.get("name"),
                    "language": c.get("language") or ext.lstrip('.'),
                    "parser_used": c.get("parser_used", "unknown"),
                }
                doc = Document(page_content=c.get("text", "").strip(), metadata=doc_metadata)
                documents.append(doc)
        except Exception:
            continue
    if not documents:
        print("No docs to embed")
        return
    embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
    vectorstore = FAISS.from_documents(documents, embeddings)
    os.makedirs(VECTOR_DIR, exist_ok=True)
    vectorstore.save_local(VECTOR_DIR)
    # keyword index
    try:
        keyword_map = {}
        for doc in documents:
            path = doc.metadata["path"]
            keyword_map.setdefault(path, "")
            keyword_map[path] += " " + (doc.page_content or "").lower()
        os.makedirs("data/keyword_index", exist_ok=True)
        with open("data/keyword_index/map.txt", "w", encoding="utf-8") as f:
            for k, v in keyword_map.items():
                f.write(k + "|||" + v.replace("\n", " ") + "\n")
    except Exception:
        pass
