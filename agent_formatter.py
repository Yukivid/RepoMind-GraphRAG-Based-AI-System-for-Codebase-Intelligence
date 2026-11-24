# agent_formatter.py
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.2)

PROMPT = """
You are Answer Formatter Agent. Given the pipeline outputs, produce a readable final answer for the user.
Input is JSON with keys: interpreter, retriever, code_agent, inspector, refactor, dependency.
Return a Markdown string summarizing:
- What was done / recommended
- Key files and patches (if any)
- Next steps and risks
Return only the markdown.
"""

def _call_llm(text: str):
    r = llm.invoke(text)
    return getattr(r, "content", None) or getattr(r, "text", "") or ""

def run(pipeline_outputs: dict, context: dict) -> str:
    prompt = PROMPT + "\nPIPELINE_OUTPUTS:\n" + str(pipeline_outputs)
    out = _call_llm(prompt)
    return out
