# agent_inspector.py
import os
from agent_tools import read_file

def run(code_agent_output: dict, context: dict) -> dict:
    """
    Inspector analyzes files referenced by Code Agent or Retrieval results,
    runs quick static checks (patterns), and returns findings.
    """
    findings = []
    payload = code_agent_output.get("payload", {})
    paths = []
    if isinstance(payload, dict):
        p = payload.get("path") or payload.get("files") or payload.get("targets")
        if isinstance(p, list):
            paths.extend(p)
        elif isinstance(p, str):
            paths.append(p)
    retr = context.get("retrieval")
    if retr:
        for d in retr.get("top_docs", []):
            if d.get("path") and d.get("path") not in paths:
                paths.append(d.get("path"))

    for path in paths[:12]:
        abs_path = os.path.join(context.get("repo_path","repos/myrepo"), path)
        try:
            content = read_file(abs_path)
        except Exception:
            content = "ERROR_READING"
        if isinstance(content, str):
            if "TODO" in content or "FIXME" in content:
                findings.append({"path": path, "issue": "TODO/FIXME markers present"})
            if "print(" in content and "logging" not in content:
                findings.append({"path": path, "issue": "raw print statements (consider logging)"})
            if "assert " in content and "pytest" not in content:
                findings.append({"path": path, "issue": "assert usage observed"})
    return {"findings": findings}
