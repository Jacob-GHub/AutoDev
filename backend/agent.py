from graph import get_or_build_graph
from graphqe import GraphQueryEngine
from utils.utils import get_embedding
from pathlib import Path
from openai import OpenAI
import json
client = OpenAI()



TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "find_function_location",
            "description": "Find where a specific function is defined in the codebase. Returns file path and line numbers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "function_name": {"type": "string", "description": "The name of the function to find"}
                },
                "required": ["function_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_callers",
            "description": "Get all functions that call a given function. Use this to trace where a function is used.",
            "parameters": {
                "type": "object",
                "properties": {
                    "function_name": {"type": "string", "description": "The name of the function to find callers for"}
                },
                "required": ["function_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_called_functions",
            "description": "Get all functions that a given function calls. Use this to trace what a function depends on.",
            "parameters": {
                "type": "object",
                "properties": {
                    "function_name": {"type": "string", "description": "The name of the function to inspect"}
                },
                "required": ["function_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_function_code",
            "description": "Get the actual source code of a function. Use this to understand what a function does.",
            "parameters": {
                "type": "object",
                "properties": {
                    "function_name": {"type": "string", "description": "The name of the function to get code for"}
                },
                "required": ["function_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "semantic_search",
            "description": "Search for code related to a concept, topic, or behavior. Use this when you don't know the exact function name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The concept or topic to search for"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_repo_structure",
            "description": "Get the top-level file and folder structure of the repo plus README content.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }
]

AGENT_SYSTEM_PROMPT = """
You are an expert code analyst helping a developer understand a GitHub repository.

You have tools to explore the codebase. Use them to build a complete picture before answering.
- For simple questions (where is X), use 1-2 tool calls
- For complex questions (how does X work, trace this flow), use multiple tool calls to follow the chain
- Always read actual function code before summarizing what it does
- IMPORTANT: If a tool call returns data, treat that as confirmed information. Never say something "wasn't found" if a tool call successfully returned it.
- Show your reasoning: explain what you found at each step
- When you have enough information, give a clear structured answer

Never guess. If you can't find something, say so honestly.
"""

def execute_tool(tool_call, repo_path, repo_id, collection):
    name = tool_call.function.name
    args = json.loads(tool_call.function.arguments)
    
    if name == "find_function_location":
        return find_function_location(repo_path, repo_id, args["function_name"])
    
    elif name == "get_callers":
        raw_graph = get_or_build_graph(repo_path, repo_id)
        engine = GraphQueryEngine(raw_graph)
        func = engine.get_function_by_name(args["function_name"])
        if not func:
            return {"error": f"Function '{args['function_name']}' not found"}
        callers = engine.get_calling_functions(func["id"])
        return {"function": args["function_name"], "callers": callers}
    
    elif name == "get_called_functions":
        raw_graph = get_or_build_graph(repo_path, repo_id)
        engine = GraphQueryEngine(raw_graph)
        func = engine.get_function_by_name(args["function_name"])
        if not func:
            return {"error": f"Function '{args['function_name']}' not found"}
        called = engine.get_called_functions(func["id"])
        return {"function": args["function_name"], "calls": called}
    
    elif name == "get_function_code":
        return function_summary(None, args["function_name"], repo_path, repo_id)
    
    elif name == "semantic_search":
        return semantic_lookup(collection, args["query"], args["query"])
    
    elif name == "get_repo_structure":
        return repo_summary(None, repo_path, repo_id)
    
    return {"error": f"Unknown tool: {name}"}


MAX_TOOL_CALLS = 10

def run_agent(query, repo_path, repo_id, collection, history=[]):
    messages = [
        {"role": "system", "content": AGENT_SYSTEM_PROMPT},
        *history,
        {"role": "user", "content": query}
    ]
    
    tool_calls_made = []
    tool_call_count = 0
    
    while True:
        # Force final answer if we hit the limit
        if tool_call_count >= MAX_TOOL_CALLS:
            messages.append({
                "role": "user", 
                "content": "You have reached the tool call limit. Synthesize everything you've found into a final answer now."
            })
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages
            )
            final_answer = response.choices[0].message.content
            return {
                "type": "agent",
                "question": query,
                "answer": final_answer,
                "tool_calls": tool_calls_made,
                "raw_context": {}
            }
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=TOOLS,
        )
        
        msg = response.choices[0].message
        messages.append(msg)
        
        # No tool calls means we have a final answer
        if not msg.tool_calls:
            return {
                "type": "agent",
                "question": query,
                "answer": msg.content,
                "tool_calls": tool_calls_made,
                "raw_context": {}
            }
        
        # Execute each tool call and feed results back
        for tool_call in msg.tool_calls:
            tool_call_count += 1
            result = execute_tool(tool_call, repo_path, repo_id, collection)
            
            # Track for frontend display
            tool_calls_made.append({
                "tool": tool_call.function.name,
                "args": json.loads(tool_call.function.arguments),
                "result": result
            })
            
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result)
            })

def repo_summary(query_msg, repo_path, repo_id):
    repo_root = Path(repo_path)

    # Try to read README
    readme_content = None
    for readme_name in ["README.md", "README.txt", "README.rst", "README"]:
        readme_path = repo_root / readme_name
        if readme_path.exists():
            with open(readme_path, "r", encoding="utf-8") as f:
                readme_content = f.read()[
                    :3000
                ]  # cap it so we don't blow the context window
            break

    # Get top level structure
    structure = []
    for item in sorted(repo_root.iterdir()):
        if item.name.startswith("."):
            continue
        structure.append(
            {"name": item.name, "type": "directory" if item.is_dir() else "file"}
        )

    return {
        "type": "repo_summary",
        "question": query_msg,
        "results": [
            {"readme": readme_content or "No README found.", "structure": structure}
        ],
    }


def function_summary(query_msg, func_name, repo_path, repo_id):
    raw_graph = get_or_build_graph(repo_path, repo_id)
    engine = GraphQueryEngine(raw_graph)
    func = engine.get_function_by_name(func_name)

    if not func:
        return {"type": "function_summary", "question": query_msg, "results": []}

    file_node = engine.get_file_of_function(func["id"])
    file_path = Path(repo_path) / func["location"]

    # Read the actual source lines
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    code = "".join(lines[func["startLine"] - 1 : func["endLine"]])

    return {
        "type": "function_summary",
        "question": query_msg,
        "results": [
            {
                "file": file_node["filePath"],
                "function": func["name"],
                "code": code,
                "line_range": [func["startLine"], func["endLine"]],
            }
        ],
    }


def find_function_location(repo_path, repo_id, func_name):
    raw_graph = get_or_build_graph(repo_path, repo_id)
    engine = GraphQueryEngine(raw_graph)
    func = engine.get_function_by_name(func_name)
    if not func:
        return {"type": "semantic_lookup", "question": func_name, "results": []}
    file = engine.get_file_of_function(func["id"])
    return {
        "type": "semantic_lookup",
        "question": func_name,
        "results": [
            {
                "file": file["filePath"],
                "function": func["name"],
                "startLine": func["startLine"],
                "endLine": func["endLine"],
            }
        ],
    }


def semantic_lookup(collection, func_name, question):
    res = search_functions(collection, func_name, n=3)
    documents = res.get("documents", [[]])[0]

    if not documents:
        return {"type": "semantic_lookup", "question": question, "results": []}
    
    metadatas = res.get("metadatas", [[]])[0]
    distances = res.get("distances", [[]])[0]

    if not documents:
        return []

    results = []
    for doc, meta, dist in zip(documents, metadatas, distances):
        results.append(
            {
                "file": meta["filepath"],
                "score": round(1 - dist, 4),
                "code": doc.strip(),
            }
        )

    return {"type": "semantic_lookup", "question": question, "results": results}


def search_functions(collection, code_query, n=3):
    embedding = get_embedding(code_query, model="text-embedding-3-small")
    res = collection.query(
        query_embeddings=[embedding],
        n_results=n,
        include=["documents", "metadatas", "distances"],
    )
    return res
