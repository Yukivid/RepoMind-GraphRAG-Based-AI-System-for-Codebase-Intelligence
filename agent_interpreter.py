# agent_interpreter.py
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.2)

SYSTEM_PROMPT = """
You are the Interpreter Agent. Your job: read the user's instruction and return a concise, prioritized
list of intentions and clarifying facts the system should assume. Output JSON:
{
  "intent": "fix_bug"|"refactor"|"explain"|"add_feature"|"create_tests"|...,
  "targets": ["path1","path2",...],   # optional
  "constraints": "...",               # optional
  "notes": "short explanation"
}
"""

def _llm_call(prompt: str):
    r = llm.invoke(prompt)
    return getattr(r, "content", None) or getattr(r, "text", "") or ""

def run(input_text: str, context: dict) -> dict:
    prompt = SYSTEM_PROMPT + "\nUser instruction:\n" + input_text + "\n\nReturn JSON only."
    raw = _llm_call(prompt)
    import json, re
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass
    # try to extract a JSON block
    m = re.search(r"\{.*\}", raw, flags=re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass
    # fallback heuristic
    lower = input_text.lower()
    intent = "explain"
    if any(w in lower for w in ["fix", "bug", "error", "fail"]):
        intent = "fix_bug"
    elif any(w in lower for w in ["refactor", "cleanup", "improve"]):
        intent = "refactor"
    elif any(w in lower for w in ["test", "unit test", "pytest"]):
        intent = "create_tests"
    elif any(w in lower for w in ["add", "implement", "feature"]):
        intent = "add_feature"
    return {"intent": intent, "targets": [], "constraints": "", "notes": input_text}
