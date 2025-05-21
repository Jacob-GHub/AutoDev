from utils.utils import get_embedding
from chroma import create_collection

def query(collection, query_msg):
    res = search_functions(collection, query_msg, n=3)

    if not res['documents'][0]:
        return("No results found.")
    else:
        for doc, meta, dist in zip(res['documents'][0], res['metadatas'][0], res['distances'][0]):
            return(f"\n📄 File: {meta['filepath']}\n🔎 Distance: {dist:.4f}\n🧠 Code:\n{doc}")


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
