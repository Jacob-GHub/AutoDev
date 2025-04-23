from utils.embedding import embed_code
from utils.plot import plot
import chromadb
from chromadb.config import Settings

chroma_client = chromadb.Client(Settings())
collection = chroma_client.get_or_create_collection(name="test",metadata={"hnsw:space": "cosine"})

examples = [
    ("def add(a, b): return a + b", "code_add"),
    ("def subtract(a, b): return a - b", "code_subtract"),
    ("def multiply(a, b): return a * b", "code_multiply"),
    ("print('Hello world')", "code_hello"),
    ("def greet(name): print(f'Hello {name}')", "code_greet"),
]

plot(examples)


# for snippet, id in examples:
#     collection.add(
#         documents=[snippet],
#         embeddings=[embed_code(snippet)],
#         ids=[id]
#     )

# results = collection.query(query_embeddings=[embed_code("function that adds two numbers")], n_results=3)

# for doc, dist in zip(results['documents'][0], results['distances'][0]):
#     print(f"{doc} → distance: {dist:.4f}")
