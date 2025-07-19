from utils.utils import get_embedding
from chroma import create_collection
import re
from pathlib import Path
from graph import build_graph,save_graph
from graphqe import GraphQueryEngine

def handleQuestion(collection, query_msg, repo_path, repo_id):
    func_name = func_name_extractor(query_msg)

    if "where is" in query_msg:
        return semantic_lookup(collection, func_name, query_msg)
    elif "what does" in query_msg:
        print("Handling function summary")
        return function_summary(query_msg, func_name)
    elif "what calls" in query_msg:
        return call_graph(query_msg, func_name, repo_path, repo_id)
    elif "repo do" in query_msg:
        return repo_summary(query_msg, func_name)

    return {"type": "unknown", "question": query_msg, "results": []}

def func_name_extractor(question):
    match = re.search(r"(?:function\s+)?([a-zA-Z_][a-zA-Z0-9_]*)\s*\(\)?", question)
    return match.group(1) if match else None

def call_graph(query_msg,func_name,repo_path,repo_id):
    return {
  "type": "call_graph",
  "question": "what calls build_graph?",
  "results": [
    {
      "target": "build_graph",
      "callers": [
        {
          "file": "main.py",
          "function": "main",
          "line": 22
        },
        {
          "file": "pipeline.py",
          "function": "run_pipeline",
          "line": 10
        }
      ]
    }
  ]
}

def repo_summary(query_msg,func_name):
    return {
  "type": "repo_summary",
  "question": "what does the repo do?",
  "results": [
    {
      "summary": "This repo analyzes codebases, builds call graphs, and provides insights using NLP and embeddings.",
      "entry_points": ["main.py", "cli.py"],
      "key_modules": ["graph.py", "parser.py"]
    }
  ]
}

def function_summary(query_msg,func_name):
    return {
    "type": "function_summary",
    "question": "what does build_graph do?",
    "results": [
        {
        "file": "src/graph.py",
        "function": "build_graph",
        "summary": "This function constructs a graph using nodes from parsed files.",
        "code": "def build_graph(...)",
        "line_range": [12, 41]
        }
    ]
}
    
def semantic_lookup(collection, func_name,question):
    res = search_functions(collection, func_name, n=3)

    documents = res.get("documents", [[]])[0]
    metadatas = res.get("metadatas", [[]])[0]
    distances = res.get("distances", [[]])[0]

    if not documents:
        return []

    results = []
    for doc, meta, dist in zip(documents, metadatas, distances):
        results.append({
            "file": meta["filepath"],
            "score": round(1 - dist, 4),
            "code": doc.strip(),
        })

    return {"type":"semantic_lookup",
            "question":question,
            "results":results
            }

# def print_collection(collection):
#     results = collection.get(include=["documents", "metadatas", "embeddings"])
#     for uid, doc, meta in zip(results["ids"], results["documents"], results["metadatas"]):
#         print(f"🆔 ID: {uid}")
#         print(f"📄 Code:\n{doc}")
#         print(f"📝 Metadata: {meta}")
#         print("-" * 60)

def search_functions(collection, code_query, n=3):
    embedding = get_embedding(code_query, model='text-embedding-3-small')
    res = collection.query(
        query_embeddings=[embedding],
        n_results=n,
        include=["documents", "metadatas", "distances"]
    )
    return res
