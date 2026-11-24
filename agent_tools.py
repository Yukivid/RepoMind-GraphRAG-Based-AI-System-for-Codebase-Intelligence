# agent_tools.py
import os

def list_files(repo_path):
    files = []
    for root, _, fs in os.walk(repo_path):
        if ".git" in root: continue
        for f in fs:
            files.append(os.path.join(root, f))
    return files

def read_file(path):
    if not os.path.exists(path):
        return f"ERROR: File `{path}` does not exist."
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception as e:
        return f"ERROR reading file: {e}"

def apply_patch(path, new_code):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_code)
        return f"SUCCESS: Updated file `{path}`"
    except Exception as e:
        return f"ERROR writing file: {e}"

def search_file(path, keyword):
    if not os.path.exists(path):
        return f"File not found: {path}"
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.readlines()
        matches = []
        for i, line in enumerate(content, start=1):
            if keyword.lower() in line.lower():
                matches.append(f"{i}: {line.strip()}")
        return "\n".join(matches) if matches else "No matches found."
    except Exception as e:
        return f"Error searching file: {e}"
