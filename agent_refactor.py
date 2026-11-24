# agent_refactor.py
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from agent_tools import read_file, apply_patch

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.2)

PROMPT = """
You are Refactor Agent. Given a file path and its content, produce a refactored version.
Return JSON: {"path":"rel/path","new_code":"...","explain":"..."}
"""

def _call_llm(text: str):
    r = llm.invoke(text)
    return getattr(r, "content", None) or getattr(r, "text", "") or ""

def run(code_agent_output: dict, context: dict) -> dict:
    payload = code_agent_output.get("payload", {})
    path = payload.get("path") or (payload.get("files")[0] if payload.get("files") else None)
    if not path:
        return {"refactor_applied": False, "reason": "no path provided"}
    repo = context.get("repo_path", "repos/myrepo")
    abs_path = os.path.join(repo, path)
    src = read_file(abs_path)
    prompt = PROMPT + "\nFILE_CONTENT:\n" + (src or "") + "\nReturn JSON only."
    out = _call_llm(prompt)
    import json, re
    parsed = None
    try:
        parsed = json.loads(out)
    except:
        m = re.search(r"\{.*\}", out, flags=re.DOTALL)
        if m:
            try:
                parsed = json.loads(m.group(0))
            except:
                parsed = None
    if parsed and parsed.get("new_code"):
        res = apply_patch(abs_path, parsed["new_code"])
        return {"refactor_applied": True, "result": res, "explain": parsed.get("explain","")}
    return {"refactor_applied": False, "proposal": out}
