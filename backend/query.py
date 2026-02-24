from utils.utils import get_embedding
from chroma import create_collection
import re
from pathlib import Path
from graph import save_graph, get_or_build_graph
from graphqe import GraphQueryEngine
from openai import OpenAI
import json

client = OpenAI()

INTENT_PROMPT = """
You are a router for a GitHub repo assistant. Given a user question, return JSON:
{
  "intent": one of ["semantic_lookup", "function_summary", "call_graph", "repo_summary", "open_ended"],
  "function_name": the function name mentioned, or null
}
Rules:
- "where is X" or "find X" → semantic_lookup
- "what does X do" → function_summary  
- "what calls X" or "who calls X" → call_graph
- "what does this repo do" or "overview" → repo_summary
- anything else → open_ended

Only return JSON. No explanation.
"""

ANSWER_PROMPT = """
You are a code assistant helping a developer understand a GitHub repo.
You will receive a question and structured context retrieved from the codebase.
Answer concisely. Reference specific files and function names when available.
If context is insufficient, say so honestly.
"""


def generate_answer(query_msg: str, context: dict, history: list = []) -> dict:
    messages = [{"role": "system", "content": ANSWER_PROMPT}]
    
    # Inject prior conversation
    messages.extend(history)
    
    # Add current question with context
    messages.append({
        "role": "user",
        "content": f"Question: {query_msg}\n\nContext:\n{json.dumps(context, indent=2)}"
    })

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )
    return {
        "type": context.get("type", "unknown"),
        "question": query_msg,
        "answer": response.choices[0].message.content,
        "raw_context": context,
    }


def classify_intent(query_msg: str) -> dict:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": INTENT_PROMPT},
            {"role": "user", "content": query_msg},
        ],
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)


def handleQuestion(collection, query_msg, repo_path, repo_id,history = []):
    if collection is None:
        return {
            "type": "error",
            "question": query_msg,
            "answer": "No indexable code found in this repository. Currently only Python repos are supported.",
            "raw_context": {}
        }
    
    intent_data = classify_intent(query_msg)
    intent = intent_data.get("intent")
    func_name = intent_data.get("function_name")

    if intent == "semantic_lookup":
        if func_name:
            context = find_function_location(repo_path, repo_id, func_name)
        else:
            # no specific function mentioned, fall back to embeddings
            context = semantic_lookup(collection, query_msg, query_msg)
    elif intent == "function_summary":
        context = function_summary(query_msg, func_name, repo_path, repo_id)
    elif intent == "call_graph":
        context = call_graph(query_msg, func_name, repo_path, repo_id)
    elif intent == "repo_summary":
        context = repo_summary(query_msg, repo_path, repo_id)
    else:
        # open_ended: semantic search on the full query, not just a function name
        context = semantic_lookup(collection, query_msg, query_msg)

    return generate_answer(query_msg, context, history)


def call_graph(query_msg, func_name, repo_path, repo_id):
    if not func_name:
        return {
            "type": "call_graph",
            "question": query_msg,
            "results": [{"target": "unknown", "callers": []}]
        }
    
    raw_graph = get_or_build_graph(repo_path, repo_id)
    graph_engine = GraphQueryEngine(raw_graph)
    func = graph_engine.get_function_by_name(func_name)
    
    if not func:
        return {
            "type": "call_graph",
            "question": query_msg,
            "results": [{"target": func_name, "callers": []}]
        }
    
    callers = graph_engine.get_calling_functions(func["id"])

    return {
        "type": "call_graph",
        "question": query_msg,
        "results": [{"target": func_name, "callers": callers}],
    }


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
