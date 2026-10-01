import json
from pathlib import Path

from openai import OpenAI

import store

client = OpenAI()

MODEL = "gpt-4o"
MAX_TOOL_CALLS = 10

_NAME_PARAM = {
    "type": "object",
    "properties": {
        "function_name": {
            "type": "string",
            "description": (
                "Function name. A bare name (build_graph), a method (Foo.bar), or a fully "
                "qualified name (backend/graph.py:Foo.bar) to pick one of several matches."
            ),
        }
    },
    "required": ["function_name"],
}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "find_function_location",
            "description": "Find where a function is defined. Returns every match with file path and line numbers.",
            "parameters": _NAME_PARAM,
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_callers",
            "description": "Get all functions that call a given function. Use this to trace where a function is used.",
            "parameters": _NAME_PARAM,
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_called_functions",
            "description": "Get all functions in this repo that a given function calls. Use this to trace what it depends on.",
            "parameters": _NAME_PARAM,
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_function_code",
            "description": "Get the source code of a function. Use this to understand what a function does.",
            "parameters": _NAME_PARAM,
        },
    },
    {
        "type": "function",
        "function": {
            "name": "semantic_search",
            "description": "Search for code related to a concept, topic, or behavior. Use this when you don't know the exact function name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The concept or topic to search for",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_repo_structure",
            "description": "Get the top-level file and folder structure of the repo plus README content.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]

AGENT_SYSTEM_PROMPT = """
You are an expert code analyst helping a developer understand a GitHub repository.

You have tools to explore the codebase. Use them to build a complete picture before answering.
- For simple questions (where is X), use 1-2 tool calls
- For complex questions (how does X work, trace this flow), use multiple tool calls to follow the chain
- Always read actual function code before summarizing what it does
- If a name matches several functions, say which one you mean by its qualified name (file:Class.method)
- IMPORTANT: If a tool call returns data, treat that as confirmed information. Never say something "wasn't found" if a tool call successfully returned it.
- Show your reasoning: explain what you found at each step
- When you have enough information, give a clear structured answer

Never guess. If you can't find something, say so honestly.
"""


def _not_found(name):
    return {
        "error": f"No function named '{name}' in this repo. Try semantic_search instead."
    }


def execute_tool(name, args, repo_id, repo_path):
    if name == "find_function_location":
        matches = store.find_functions(repo_id, args["function_name"])
        return {"matches": matches} if matches else _not_found(args["function_name"])

    if name == "get_callers":
        result = store.get_callers(repo_id, args["function_name"])
        return (
            {"results": result}
            if result is not None
            else _not_found(args["function_name"])
        )

    if name == "get_called_functions":
        result = store.get_callees(repo_id, args["function_name"])
        return (
            {"results": result}
            if result is not None
            else _not_found(args["function_name"])
        )

    if name == "get_function_code":
        matches = store.find_functions(repo_id, args["function_name"], with_code=True)
        return {"matches": matches} if matches else _not_found(args["function_name"])

    if name == "semantic_search":
        return {"results": store.semantic_search(repo_id, args["query"])}

    if name == "get_repo_structure":
        return repo_summary(repo_path)

    return {"error": f"Unknown tool: {name}"}


def run_agent(query, repo_id, repo_path, history=None):
    messages = [
        {"role": "system", "content": AGENT_SYSTEM_PROMPT},
        *(history or []),
        {"role": "user", "content": query},
    ]
    tool_calls_made = []
    tool_call_count = 0

    def result(answer):
        return {
            "type": "agent",
            "question": query,
            "answer": answer,
            "tool_calls": tool_calls_made,
        }

    while True:
        # Force a final answer once the budget is spent.
        if tool_call_count >= MAX_TOOL_CALLS:
            messages.append(
                {
                    "role": "user",
                    "content": "You have reached the tool call limit. Synthesize everything you've found into a final answer now.",
                }
            )
            response = client.chat.completions.create(model=MODEL, messages=messages)
            return result(response.choices[0].message.content)

        response = client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOLS
        )
        msg = response.choices[0].message
        messages.append(msg)

        if not msg.tool_calls:
            return result(msg.content)

        for tool_call in msg.tool_calls:
            tool_call_count += 1
            name = tool_call.function.name
            try:
                args = json.loads(tool_call.function.arguments or "{}")
                output = execute_tool(name, args, repo_id, repo_path)
            except Exception as e:
                # One bad tool call shouldn't kill the whole answer; let the model recover.
                args = {}
                output = {"error": f"{type(e).__name__}: {e}"}

            tool_calls_made.append({"tool": name, "args": args, "result": output})
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(output, default=str),
                }
            )


def repo_summary(repo_path):
    repo_root = Path(repo_path)

    readme_content = None
    for readme_name in ["README.md", "README.txt", "README.rst", "README"]:
        readme_path = repo_root / readme_name
        if readme_path.exists():
            readme_content = readme_path.read_text(encoding="utf-8", errors="replace")[
                :3000
            ]
            break

    structure = [
        {"name": item.name, "type": "directory" if item.is_dir() else "file"}
        for item in sorted(repo_root.iterdir())
        if not item.name.startswith(".")
    ]

    return {"readme": readme_content or "No README found.", "structure": structure}
