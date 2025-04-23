from utils.embedding import embed_code
import chromadb
from chromadb.config import Settings

test_code = "int x = 10"
test_code2 = "while x < 10:"

chroma_client = chromadb.Client(Settings())
collection = chroma_client.get_or_create_collection(name="test")
test_snippet ="def hello(): print('hello')"
embedding1 = embed_code(test_snippet)
embedding2 = embed_code(test_code2)

collection.add(
    ids=["snippet_001"],
    embeddings=[embedding1.tolist()],  # Convert from numpy to plain list
    documents=[test_snippet],
    metadatas=[{"function": "hello", "language": "python"}]
)

collection.add(
    ids=["snippet_002"],
    embeddings=[embedding2.tolist()],  # Convert from numpy to plain list
    documents=[test_code2],
    metadatas=[{"function": "hello", "language": "python"}]
)


query_code = "def hello(): print('hello')"
query_embedding = embed_code(query_code)

results = collection.query(
    query_embeddings=[query_embedding.tolist()],
    n_results=2
)

print(results)
