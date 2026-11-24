# agent_orchestrator.py
"""
Orchestrator: wires the pipeline:
Interpreter -> Retriever -> Code -> (Inspector, Refactor, Dependency) -> Formatter
"""

from agent_interpreter import run as run_interpreter
from agent_retriever import run as run_retriever
from agent_code import run as run_code_agent
from agent_inspector import run as run_inspector
from agent_refactor import run as run_refactor
from agent_dependency import run as run_dependency
from agent_formatter import run as run_formatter

def run_pipeline(user_instruction: str, repo_path: str = "repos/myrepo"):
    context = {"repo_path": repo_path, "retrieval": None}
    # 1. Interpreter
    interp = run_interpreter(user_instruction, context)
    # 2. Retriever
    retr = run_retriever(interp, context)
    context["retrieval"] = retr
    # 3. Code Agent
    code = run_code_agent(interp, retr, context)
    # 4. Inspector, Refactor, Dependency (sequential)
    inspector = run_inspector(code, {**context, "retrieval": retr})
    refactor = run_refactor(code, {**context, "retrieval": retr})
    dependency = run_dependency(code, {**context, "retrieval": retr})
    pipeline = {
        "interpreter": interp,
        "retriever": retr,
        "code_agent": code,
        "inspector": inspector,
        "refactor": refactor,
        "dependency": dependency
    }
    # 5. Formatter
    final_markdown = run_formatter(pipeline, context)
    return {"pipeline": pipeline, "final": final_markdown}
