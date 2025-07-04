from utils.utils import get_embedding
from chroma import create_collection

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
