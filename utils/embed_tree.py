from utils.code_parser import parse
from utils.embedding import embed_code
# from utils.plot import plot
import chromadb
from chromadb.config import Settings



chroma_client = chromadb.Client(Settings())

def embed_parse_tree(file_path):
    collection = chroma_client.get_or_create_collection(name="test")
    functions = parse(file_path)
    for function in functions:
        collection.upsert(
            documents=[function["code"]],
            embeddings=[embed_code(function["code"])],
            ids=[function["name"]]
        )

    # results = collection.get(include=["documents", "metadatas", "embeddings"])

    # for doc, metadata, embedding in zip(results["documents"], results["metadatas"], results["embeddings"]):
    #     print("Document:", doc)
    #     print("Metadata:", metadata)
    #     print("Embedding:", embedding[:10],"...")
    #     print("="*50)
    return collection
