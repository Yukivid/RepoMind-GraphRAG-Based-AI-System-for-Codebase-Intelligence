# directory_summary.py
import os
from langchain_core.prompts import ChatPromptTemplate

def generate_directory_summary(llm, repo_path: str, dir_path: str, max_file_chars=2000):
    abs_dir = os.path.join(repo_path, dir_path)
    if not os.path.exists(abs_dir):
        return f"⚠️ Directory `{dir_path}` not found under repo."

    files = []
    for root, _, fs in os.walk(abs_dir):
        for f in fs:
            if f.endswith((".py", ".js", ".ts", ".java", ".cpp", ".go", ".md")):
                p = os.path.join(root, f)
                try:
                    with open(p, "r", encoding="utf-8", errors="ignore") as fp:
                        code = fp.read(max_file_chars)
                    files.append({"path": os.path.relpath(p, repo_path), "content_snippet": code})
                except Exception:
                    pass

    prompt = ChatPromptTemplate.from_template("""
You are an assistant that summarizes a directory of source code.

Directory: {dir}
Files (path + small code snippet): {files}

Produce:
- A short title for this directory (3-6 words)
- A 3–6 sentence summary of purpose and major modules
- List of key files/classes/functions to look at
- Notes for maintainers (TODOs / likely areas of interest)

Keep it concise and developer-focused.
""")

    content_str = str(files)[:6000]
    messages = prompt.format_messages(dir=dir_path, files=content_str)
    resp = llm.invoke(messages)
    return getattr(resp, "content", None) or getattr(resp, "text", "") or "No summary returned."
