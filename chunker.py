import ast

def chunk_python_file(file_path):
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        code = f.read()

    tree = ast.parse(code)
    chunks = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            chunks.append({
                "name": node.name,
                "file": file_path,
                "code": ast.get_source_segment(code, node)
            })

    return chunks
