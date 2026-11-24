# agent_dependency.py
import os
from agent_tools import list_files, read_file
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.2)

PROMPT = """
You are Dependency Agent. Given a sample of files, produce:
- list of top-level modules
- likely external libs used (requirements)
Return JSON: {"modules":[...],"libraries":[...],"notes":"..."}
"""

def _call_llm(text: str):
    r = llm.invoke(text)
    return getattr(r, "content", None) or getattr(r, "text", "") or ""

def run(code_agent_output: dict, context: dict) -> dict:
    repo = context.get("repo_path","repos/myrepo")
    files = list_files(repo)
    sample = []
    for p in files[:40]:
        try:
            sample.append({"path": os.path.relpath(p, repo), "head": read_file(p)[:800]})
        except Exception:
            pass
    prompt = PROMPT + "\nFILES_SAMPLE:\n" + str(sample)
    raw = _call_llm(prompt)
    import json, re
    try:
        return json.loads(raw)
    except:
        m = re.search(r"\{.*\}", raw, flags=re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except:
                pass
    return {"modules": [], "libraries": [], "notes": raw}
