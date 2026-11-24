# ingest/repo_loader.py
import os
from git import Repo
from pathlib import Path
import subprocess
from typing import List, Dict, Generator

DEFAULT_EXTS = ('.py', '.js', '.java', '.ts', '.md', '.txt', '.go', '.cpp', '.c', '.h', '.rs')

def clone_or_open(repo: str, target_dir: str = "repos/myrepo") -> str:
    """
    If repo is a URL, clone into target_dir. If a local path, use it directly.
    Returns path to repository.
    """
    if repo.startswith("http://") or repo.startswith("https://") or repo.endswith(".git"):
        if os.path.exists(target_dir):
            print(f"Target {target_dir} exists. Removing and recloning.")
            subprocess.run(["rm", "-rf", target_dir])
        print(f"Cloning {repo} -> {target_dir}")
        Repo.clone_from(repo, target_dir)
        return target_dir
    else:
        # assume local path
        return os.path.abspath(repo)

def list_code_files(repo_path: str, exts=DEFAULT_EXTS) -> Generator[str, None, None]:
    for root, dirs, files in os.walk(repo_path):
        # skip .git and virtual envs
        if '.git' in root.split(os.sep):
            continue
        for f in files:
            if f.startswith('.'):
                continue
            if any(f.endswith(ext) for ext in exts):
                yield os.path.join(root, f)

def get_latest_commit_for_file(repo_path: str, file_path: str) -> str:
    """
    Returns the latest commit sha for the file.
    """
    repo = Repo(repo_path)
    rel = os.path.relpath(file_path, repo_path)
    commits = list(repo.iter_commits(paths=rel, max_count=1))
    if commits:
        return commits[0].hexsha
    return ""

def read_file(file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()

def dump_repo_files(repo_path: str, out_jsonl: str = "chunks.jsonl"):
    """
    Walk repo, read files, produce simple per-file records (content + metadata).
    We'll do chunking in parser.py
    """
    import json
    records = []
    for fp in list_code_files(repo_path):
        text = read_file(fp)
        sha = get_latest_commit_for_file(repo_path, fp)
        records.append({
            "path": os.path.relpath(fp, repo_path),
            "abs_path": fp,
            "commit_sha": sha,
            "text": text
        })
    with open(out_jsonl, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    print(f"Wrote {len(records)} files to {out_jsonl}")
