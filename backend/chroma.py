from pathlib import Path
from utils.utils import get_embedding
from utils.code_parser import extract_functions_from_repo
import chromadb

def create_collection(path):
    root_dir = Path.home()
    code_root = root_dir / path

    chroma_client = chromadb.PersistentClient(path="chroma_db")
    collection = chroma_client.get_or_create_collection(
        name="code_functions",
        metadata={"hnsw:space": "cosine"}
    )

    # Extract all functions from the repository
    all_funcs = extract_functions_from_repo(code_root)

    # Get existing IDs from the DB
    existing = collection.get(include=["metadatas"])
    existing_ids = set(existing.get("ids", []))

    new_ids = []
    new_codes = []
    new_embeddings = []
    new_metadatas = []

    for idx, func in enumerate(all_funcs):
        filepath = Path(func['filepath']).relative_to(code_root)
        uid = f"{filepath}_{idx}"  # Create UID first

        if uid in existing_ids:
            continue  # Skip if already added

        code = func['code']
        print(func['function_name'])

        # Defer embedding until we know it's new
        embedding = get_embedding(code, model='text-embedding-3-small')

        new_ids.append(uid)
        new_codes.append(code)
        new_embeddings.append(embedding)
        new_metadatas.append({
            "filepath": str(filepath),
            "function_name": func['function_name'],
        })

    if new_ids:
        collection.add(
            ids=new_ids,
            documents=new_codes,
            embeddings=new_embeddings,
            metadatas=new_metadatas
        )

    return collection
