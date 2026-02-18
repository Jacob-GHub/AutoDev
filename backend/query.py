from utils.utils import get_embedding
from chroma import create_collection
import re
from pathlib import Path
from graph import build_graph, save_graph
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


def generate_answer(query_msg: str, context: dict) -> dict:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": ANSWER_PROMPT},
            {
                "role": "user",
                "content": f"Question: {query_msg}\n\nContext:\n{json.dumps(context, indent=2)}",
            },
        ],
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


def handleQuestion(collection, query_msg, repo_path, repo_id):
    intent_data = classify_intent(query_msg)
    intent = intent_data.get("intent")
    func_name = intent_data.get("function_name")

    if intent == "semantic_lookup":
        context = semantic_lookup(collection, func_name or query_msg, query_msg)
    elif intent == "function_summary":
        context = function_summary(query_msg, func_name)
    elif intent == "call_graph":
        context = call_graph(query_msg, func_name, repo_path, repo_id)
    elif intent == "repo_summary":
        context = repo_summary(query_msg, func_name)
    else:
        # open_ended: semantic search on the full query, not just a function name
        context = semantic_lookup(collection, query_msg, query_msg)

    return generate_answer(query_msg, context)


def call_graph(query_msg, func_name, repo_path, repo_id):
    raw_graph = build_graph(repo_path)
    graph_engine = GraphQueryEngine(raw_graph)
    func_id = graph_engine.get_function_by_name(func_name)["id"]
    callers = graph_engine.get_calling_functions(func_id)
    save_graph(Path("repos") / repo_id, raw_graph)

    return {
        "type": "call_graph",
        "question": query_msg,
        "results": [{"target": func_name, "callers": callers}],
    }


def repo_summary(query_msg, func_name):
    return {
        "type": "repo_summary",
        "question": "what does the repo do?",
        "results": [
            {
                "summary": "This repo analyzes codebases, builds call graphs, and provides insights using NLP and embeddings.",
                "entry_points": ["main.py", "cli.py"],
                "key_modules": ["graph.py", "parser.py"],
            }
        ],
    }


def function_summary(query_msg, func_name):
    return {
        "type": "function_summary",
        "question": "what does build_graph do?",
        "results": [
            {
                "file": "src/graph.py",
                "function": "build_graph",
                "summary": "This function constructs a graph using nodes from parsed files.",
                "code": "def build_graph(...)",
                "line_range": [12, 41],
            }
        ],
    }


def find_function_location(repo_path, repo_id, func_name):
    raw_graph = build_graph(repo_path)
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


# def print_collection(collection):
#     results = collection.get(include=["documents", "metadatas", "embeddings"])
#     for uid, doc, meta in zip(results["ids"], results["documents"], results["metadatas"]):
#         print(f"🆔 ID: {uid}")
#         print(f"📄 Code:\n{doc}")
#         print(f"📝 Metadata: {meta}")
#         print("-" * 60)


def search_functions(collection, code_query, n=3):
    embedding = get_embedding(code_query, model="text-embedding-3-small")
    res = collection.query(
        query_embeddings=[embedding],
        n_results=n,
        include=["documents", "metadatas", "distances"],
    )
    return res
