from pathlib import Path
from utils.utils import get_embedding
from utils.code_parser import extract_functions_from_repo
import chromadb
from tempfile import mkdtemp
import subprocess
from pathlib import Path
import shutil

def clone_repo(github_url: str):
    # Create a temp folder
    tmp_path = Path(mkdtemp())

    try:
        # Clone the repo
        subprocess.run(["git", "clone", github_url, str(tmp_path)], check=True)

        # Now pass it to your existing local folder logic
        return create_collection(tmp_path)

    except Exception as e:
        print("Error cloning repo:", e)
        return None
    finally:
        # Optionally clean up
        pass  # shutil.rmtree(tmp_path) if you want to remove it later


def create_collection(path):
    code_root = Path(path)

    chroma_client = chromadb.PersistentClient(path="chroma_db")
    collection = chroma_client.get_or_create_collection(
        name="code_functions",
        metadata={"hnsw:space": "cosine"}
    )

    # Extract all functions from the repository
    all_funcs = extract_functions_from_repo(code_root)

    if not all_funcs:
        print("No functions found. Skipping collection creation.")
        return collection  # or return None if that makes more sense

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
