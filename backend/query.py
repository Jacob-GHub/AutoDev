from utils.utils import get_embedding
from chroma import create_collection
import re

def handleQuestion(query_msg):
    #hard coded for now, definitely subject to change
    func_name = func_name_extractor(query_msg)
    # if "where is" in query_msg:
    #     #simple embedding logic
    # elif "what does" in query_msg:
    #     # maybe find function using embeddings and then send func/prompt to ai
    # elif "what calls" in query_msg:
    #     # simple graphqe function use
    # elif "repo do" in query_msg:
    #     # readme detection/ main functions/file detections

def func_name_extractor(question):
    match = re.search(r"(?:function\s+)?([a-zA-Z_][a-zA-Z0-9_]*)\s*\(\)?", question)
    return match.group(1) if match else None

def query(collection, query_msg):
    res = search_functions(collection, query_msg, n=3)

    documents = res.get("documents", [[]])[0]
    metadatas = res.get("metadatas", [[]])[0]
    distances = res.get("distances", [[]])[0]

    if not documents:
        return {"results": []}

    results = []
    for doc, meta, dist in zip(documents, metadatas, distances):
        results.append({
            "file": meta["filepath"],
            "score": round(1 - dist, 4),
            "code": doc.strip(),
        })

    return {"results": results}

def print_collection(collection):
    results = collection.get(include=["documents", "metadatas", "embeddings"])
    for uid, doc, meta in zip(results["ids"], results["documents"], results["metadatas"]):
        print(f"🆔 ID: {uid}")
        print(f"📄 Code:\n{doc}")
        print(f"📝 Metadata: {meta}")
        print("-" * 60)

def search_functions(collection, code_query, n=3):
    embedding = get_embedding(code_query, model='text-embedding-3-small')
    res = collection.query(
        query_embeddings=[embedding],
        n_results=n,
        include=["documents", "metadatas", "distances"]
    )
    return res
