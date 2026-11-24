import os
import hashlib
from git import Repo
from urllib.parse import urlparse

BASE_DIR = "repos"

def repo_id_from_url(repo_url: str):
    parsed = urlparse(repo_url)
    path = parsed.path.strip("/").replace("/", "__")
    hash_part = hashlib.md5(repo_url.encode()).hexdigest()[:6]
    return f"{path}__{hash_part}"

def clone_repo(repo_url: str):
    os.makedirs(BASE_DIR, exist_ok=True)
    repo_id = repo_id_from_url(repo_url)
    repo_path = os.path.join(BASE_DIR, repo_id)

    if not os.path.exists(repo_path):
        Repo.clone_from(repo_url, repo_path)

    return repo_path
