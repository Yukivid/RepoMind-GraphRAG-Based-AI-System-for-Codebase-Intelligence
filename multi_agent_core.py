# multi_agent_core.py
import os
import json
import subprocess
import time
from langchain_google_genai import ChatGoogleGenerativeAI
from agent_tools import list_files, read_file, apply_patch, search_file

# -------------------------------------------
# LLM: Core Engine
# -------------------------------------------
model = ChatGoogleGenerativeAI(model="gemini-2.0-pro", temperature=0.2)

# -------------------------------------------
# SYSTEM INSTRUCTIONS FOR THE MASTER AGENT
# -------------------------------------------
MASTER_PROMPT = """
You are the MASTER Orchestrator Agent.

You coordinate a team of agents to solve code-related tasks.

Available Agents:
1. PLANNER_AGENT — break down user's request into steps.
2. RESEARCH_AGENT — search code, inspect files, use RAG.
3. INTERPRETER_AGENT — reason about code, simulate execution.
4. EXECUTION_AGENT — run Python code.
5. BUGFIX_AGENT — detect & fix bugs.
6. REFACTOR_AGENT — refactor structure, improve code quality.
7. DOC_AGENT — create docstrings, comments, READMEs.
8. TEST_AGENT — create unit tests.
9. ARCH_AGENT — generate architecture summaries, diagrams.
10. PATCH_AGENT — write patches to files.
11. PR_AGENT — generate PR-ready patch descriptions.

Output format ALWAYS (single JSON object):
{
  "agent": "<agent_name>",
  "action": "<tool_or_subagent>",
  "input": "<input_data>"
}

When an agent finishes the overall task, respond with:
{"agent":"FINISH","action":"FINISH","input":"<final result summary>"}
"""

# -------------------------------------------
# UTIL
# -------------------------------------------
def call_llm(prompt_text: str):
    resp = model.invoke(prompt_text)
    out = getattr(resp, "content", None) or getattr(resp, "text", "")
    return (out or "").strip()

def safe_json_loads(text: str):
    try:
        return json.loads(text)
    except:
        # try to extract JSON block
        m = None
        try:
            import re
            m = re.search(r"\{.*\}", text, flags=re.DOTALL)
            if m:
                return json.loads(m.group(0))
        except:
            pass
    return None

# -------------------------------------------
# AGENT PROMPTS (templates)
# -------------------------------------------
PLANNER_PROMPT = """
You are PLANNER_AGENT.
Given the user's task, produce a JSON array of 2-6 concrete steps to accomplish it.
Example:
["analyze repo", "find failing tests", "propose patch", "apply patch", "run tests"]
Return only the JSON array.
"""

RESEARCH_PROMPT = """
You are RESEARCH_AGENT.
Given a repo path and optional hints, return a JSON object listing top files, functions, and short reasons:
{"files": [{"path":"path/to/file","reason":"contains model code","lines":"10-80"}], "notes":"..."}
"""

BUGFIX_PROMPT = """
You are BUGFIX_AGENT.
Given a file content and an observed error or failing test, propose a minimal patch.
Return JSON:
{"path":"rel/path","new_code":"<full file contents after patch>", "explain":"..." }
"""

REFACTOR_PROMPT = """
You are REFACTOR_AGENT.
Refactor the given code for readability and structure. Return JSON:
{"path":"rel/path","new_code":"<full refactored file contents>","explain":"..."}
"""

DOC_PROMPT = """
You are DOC_AGENT.
Given code, produce docstrings and README snippets. Return JSON:
{"path":"rel/path","doc":"<docstring or README content>"}
"""

TEST_PROMPT = """
You are TEST_AGENT.
Generate pytest-style tests for the given module. Return JSON:
{"path":"tests/test_module.py","test_code":"<code>"}
"""

ARCH_PROMPT = """
You are ARCH_AGENT.
Summarize repo architecture and list key modules and dependencies. Return a JSON object with "summary" and "modules".
"""

PR_PROMPT = """
You are PR_AGENT.
Write a pull request description summarizing changes, testing steps, and notes. Return JSON:
{"title":"...","body":"..."}
"""

# -------------------------------------------
# EXECUTION AGENT (Python sandbox)
# -------------------------------------------
def run_python(code: str, timeout: int = 5):
    """
    Run a small python snippet in a subprocess with a timeout.
    NOTE: This is simple and unsafe for untrusted code. Use proper sandboxing for production.
    """
    try:
        proc = subprocess.run(
            ["python", "-c", code],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        out = proc.stdout or ""
        err = proc.stderr or ""
        return {"returncode": proc.returncode, "stdout": out, "stderr": err}
    except Exception as e:
        return {"returncode": -1, "stdout": "", "stderr": str(e)}

# -------------------------------------------
# MAIN ORCHESTRATOR
# -------------------------------------------
def run_full_agent(user_task: str, repo_path="repos/myrepo", max_steps=8):
    """
    High-level orchestrator loop:
    1) Plan
    2) For each step -> call appropriate agent
    3) Apply patches if requested
    4) Return final summary
    """
    context = {
        "repo_path": repo_path,
        "user_task": user_task,
        "history": []
    }

    # 1) PLAN
    planner_input = PLANNER_PROMPT + "\nUser task:\n" + user_task
    planner_out = call_llm(planner_input)
    steps = safe_json_loads(planner_out)
    if not isinstance(steps, list):
        # fallback: single step = user_task
        steps = [user_task]

    context["history"].append({"planner": steps})

    results = []
    step_count = 0

    for s in steps:
        step_count += 1
        if step_count > max_steps:
            results.append("Max steps reached, stopping.")
            break

        # Simple routing by keywords
        step = s.lower()
        if any(k in step for k in ["analyze", "scan", "search", "find"]):
            # RESEARCH_AGENT
            prompt = RESEARCH_PROMPT + "\nHints: " + step + "\nRepo path: " + repo_path
            out = call_llm(prompt)
            parsed = safe_json_loads(out) or {"files": [], "notes": out}
            results.append({"research": parsed})

        elif any(k in step for k in ["run", "execute", "test"]):
            # EXECUTION_AGENT
            # ask user to supply snippet? we attempt to find tests or run a sample
            # try to run a small snippet produced by LLM
            prompt = "You are EXECUTION_AGENT. Provide a short python snippet to test the repository based on: " + step
            snippet = call_llm(prompt)
            exec_result = run_python(snippet, timeout=8)
            results.append({"execution": exec_result, "snippet": snippet})

        elif any(k in step for k in ["fix", "bug", "error", "fail"]):
            # BUGFIX_AGENT
            # Ask LLM to propose a patch
            prompt = BUGFIX_PROMPT + "\nContext: " + step
            out = call_llm(prompt)
            patch = safe_json_loads(out)
            if patch and patch.get("path") and patch.get("new_code"):
                # apply patch
                target = os.path.join(repo_path, patch["path"])
                res = apply_patch(target, patch["new_code"])
                results.append({"bugfix_applied": res, "explain": patch.get("explain")})
            else:
                results.append({"bugfix_proposal": out})

        elif any(k in step for k in ["refactor", "clean", "improve"]):
            # REFACTOR_AGENT
            prompt = REFACTOR_PROMPT + "\nContext: " + step
            out = call_llm(prompt)
            patch = safe_json_loads(out)
            if patch and patch.get("path") and patch.get("new_code"):
                target = os.path.join(repo_path, patch["path"])
                res = apply_patch(target, patch["new_code"])
                results.append({"refactor_applied": res, "explain": patch.get("explain")})
            else:
                results.append({"refactor_proposal": out})

        elif any(k in step for k in ["doc", "document", "readme", "docstring"]):
            # DOC_AGENT
            prompt = DOC_PROMPT + "\nContext: " + step
            out = call_llm(prompt)
            patch = safe_json_loads(out)
            if patch and patch.get("path") and patch.get("doc"):
                # write doc to README or file
                target = os.path.join(repo_path, patch["path"])
                res = apply_patch(target, patch["doc"])
                results.append({"doc_applied": res})
            else:
                results.append({"doc_proposal": out})

        elif any(k in step for k in ["test", "unit test", "pytest"]):
            # TEST_AGENT
            prompt = TEST_PROMPT + "\nContext: " + step
            out = call_llm(prompt)
            patch = safe_json_loads(out)
            if patch and patch.get("path") and patch.get("test_code"):
                target = os.path.join(repo_path, patch["path"])
                res = apply_patch(target, patch["test_code"])
                results.append({"tests_written": res})
            else:
                results.append({"tests_proposal": out})

        elif any(k in step for k in ["architecture", "arch", "diagram", "dependency"]):
            # ARCH_AGENT
            files = list_files(repo_path)
            prompt = ARCH_PROMPT + "\nFiles sample: " + str(files[:40])
            out = call_llm(prompt)
            parsed = safe_json_loads(out) or {"summary": out}
            results.append({"architecture": parsed})

        elif any(k in step for k in ["pr", "pull request", "create pr"]):
            # PR_AGENT
            prompt = PR_PROMPT + "\nContext: " + step
            out = call_llm(prompt)
            parsed = safe_json_loads(out) or {"pr_text": out}
            results.append({"pr": parsed})

        else:
            # Default: ask LLM what to do
            prompt = "Decide the best agent and action to accomplish this step: " + step
            decision = call_llm(prompt)
            results.append({"decision": decision})

        # small pause to avoid rate bursting
        time.sleep(0.5)

    final_summary = {
        "user_task": user_task,
        "steps_executed": len(results),
        "results": results
    }

    return json.dumps(final_summary, indent=2)
