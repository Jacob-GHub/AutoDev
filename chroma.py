from pathlib import Path
from utils.utils import get_embedding, cosine_similarity
from utils.code_parser import extract_functions_from_repo
import chromadb

def create_collection():
    root_dir = Path.home()
    code_root = root_dir /'Desktop'/ 'codequery'/'test'
    chroma_client = chromadb.PersistentClient(path="chroma_db")
    collection = chroma_client.get_or_create_collection(name="code_functions",  metadata={"hnsw:space": "cosine"})

    # Extract all functions from the repository
    all_funcs = extract_functions_from_repo(code_root)
    existing = collection.get(include=["metadatas"])
    existing_ids = set(existing.get("ids", []))



    for idx, func in enumerate(all_funcs):
        code = func['code']
        filepath = Path(func['filepath']).relative_to(code_root)
        embedding = get_embedding(code, model='text-embedding-3-small')

        # Create a unique ID (filepath + index is a simple one)
        uid = f"{filepath}_{idx}"
        if uid in existing_ids:
            continue
        print(func['function_name'])

        collection.add(
            ids=[uid],
            documents=[code],
            embeddings=[embedding],
            metadatas=[{
                "filepath": str(filepath),
                "function_name": func['function_name'],
            }]
        )

    return collection
