# agent_code.py
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.2)

PROMPT_TEMPLATE = """
You are the Code Agent. You have:
- interpreter_result: {interp}
- retrieval_result: {retr}

Tasks:
Depending on intent, either:
- explain the relevant code (short)
- propose a minimal patch (JSON with fields: path, patch_type, diff_or_new_code, explanation)
- or outline steps to implement feature.

Return JSON with keys:
{{"action":"explain"|"propose_patch"|"plan","payload":{{...}}}}
"""

def _llm_call(text: str):
    r = llm.invoke(text)
    return getattr(r, "content", None) or getattr(r, "text", "") or ""

def run(interp_result: dict, retr_result: dict, context: dict) -> dict:
    prompt = PROMPT_TEMPLATE.format(interp=interp_result, retr=retr_result)
    raw = _llm_call(prompt)
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
    # fallback: return explanation
    return {"action":"explain","payload":{"explanation": raw}}
