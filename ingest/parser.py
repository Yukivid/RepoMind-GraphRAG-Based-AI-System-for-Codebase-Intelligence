# ingest/parser.py
import json
import os
import re
from typing import List, Dict, Generator

def simple_function_split(code: str, lang: str = "auto") -> List[Dict]:
    """
    Attempt to split by function/class boundaries using regex heuristics for Python/JS.
    Returns list of dicts: {start_line, end_line, text}
    """
    lines = code.splitlines()
    n = len(lines)
    boundaries = [0]
    # very small heuristic: lines that start with 'def ' or 'class ' or 'function ' or 'export function' or those with '{' for JS
    for i, ln in enumerate(lines):
        s = ln.strip()
        if s.startswith("def ") or s.startswith("class "):
            boundaries.append(i)
        # js / ts
        if re.match(r'^(export\s+)?function\s+\w+\s*\(', s) or re.match(r'^\w+\s*:\s*function\s*\(', s):
            boundaries.append(i)
        # arrow functions in JS
        if re.match(r'^\w+\s*=\s*\(.*\)\s*=>', s):
            boundaries.append(i)
    boundaries = sorted(set(boundaries))
    chunks = []
    for i, b in enumerate(boundaries):
        start = b
        end = boundaries[i+1] if i+1 < len(boundaries) else n
        text = "\n".join(lines[start:end]).strip()
        if text:
            chunks.append({"start_line": start+1, "end_line": end, "text": text})
    # fallback: if only one chunk and large, do sliding windows
    if len(chunks) == 1 and len(lines) > 400:
        chunk_size = 200
        overlap = 50
        chunks = []
        for s in range(0, n, chunk_size - overlap):
            e = min(n, s + chunk_size)
            chunks.append({"start_line": s+1, "end_line": e, "text": "\n".join(lines[s:e])})
    return chunks

def chunk_files(input_jsonl: str = "chunks.jsonl", out_chunks_jsonl: str = "file_chunks.jsonl"):
    import json
    cnt = 0
    with open(input_jsonl, "r", encoding="utf-8") as inf, open(out_chunks_jsonl, "w", encoding="utf-8") as outf:
        for line in inf:
            rec = json.loads(line)
            path = rec["path"]
            commit_sha = rec.get("commit_sha", "")
            text = rec["text"]
            # choose language from extension
            ext = os.path.splitext(path)[1].lower()
            # simple split
            chunks = simple_function_split(text)
            for c in chunks:
                out = {
                    "path": path,
                    "commit_sha": commit_sha,
                    "start_line": c["start_line"],
                    "end_line": c["end_line"],
                    "text": c["text"]
                }
                outf.write(json.dumps(out) + "\n")
                cnt += 1
    print(f"Wrote {cnt} chunks to {out_chunks_jsonl}")
