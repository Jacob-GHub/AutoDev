from pathlib import Path
from utils.utils import get_embedding
from utils.code_parser import extract_functions_from_repo
import chromadb
from tempfile import mkdtemp
import subprocess
from pathlib import Path
import shutil
import os
import subprocess
from pathlib import Path
from hashlib import sha1
from urllib.parse import urlparse
import shutil


def get_repo_id(github_url: str) -> str:
    """
    Generates a unique ID from the repo URL
    """
    parsed = urlparse(github_url)
    path_parts = parsed.path.strip("/").split("/")
    if len(path_parts) >= 2:
        owner, repo = path_parts[0], path_parts[1].replace(".git", "")
        repo_hash = sha1(github_url.encode()).hexdigest()[:7]
        return f"{owner}_{repo}_{repo_hash}"
    raise ValueError("Invalid GitHub URL")

def clone_repo(github_url: str, base_dir: Path = Path("repos")) -> Path:
    """
    Clones a GitHub repo into a persistent folder based on repo ID.
    Returns the path to the cloned repo.
    """
    repo_id = get_repo_id(github_url)
    target_path = base_dir / repo_id / "raw"

    if target_path.exists():
        print(f"Repo already cloned at {target_path}")
        return target_path

    print(f"Cloning {github_url} to {target_path}...")
    target_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        subprocess.run(["git", "clone", "--depth", "1", github_url, str(target_path)], check=True)
        return target_path

    except subprocess.CalledProcessError as e:
        print("Error cloning repo:", e)
        if target_path.exists():
            shutil.rmtree(target_path)
        return None


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
