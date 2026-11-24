import ast
import os

def parse_python_file(file_path):
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        code = f.read()

    tree = ast.parse(code)
    symbols = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            symbols.append({"type": "function", "name": node.name, "file": file_path})
        elif isinstance(node, ast.ClassDef):
            symbols.append({"type": "class", "name": node.name, "file": file_path})
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            symbols.append({"type": "call", "name": node.func.id, "file": file_path})

    return symbols

def extract_dataflow(file_path):
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        tree = ast.parse(f.read())

    flows = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    flows.append(("defines", t.id))
        if isinstance(node, ast.Import):
            for n in node.names:
                flows.append(("imports", n.name))
        if isinstance(node, ast.ImportFrom) and node.module:
            flows.append(("imports", node.module))

    return flows

def parse_repo(repo_path):
    symbols = []
    for root, _, files in os.walk(repo_path):
        for f in files:
            if f.endswith(".py"):
                symbols.extend(parse_python_file(os.path.join(root, f)))
    return symbols
