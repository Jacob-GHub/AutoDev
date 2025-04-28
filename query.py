from utils.code_parser import parse
from utils.embed_tree import embed_parse_tree
from utils.embedding import embed_code,embed_text

collection = embed_parse_tree(("test/testing.py"))

# results = collection.get(include=["documents", "metadatas", "embeddings"])
# print(results)

results = collection.query(query_embeddings=[embed_code("finds the vowel")], n_results=3)

for doc, dist in zip(results['documents'][0], results['distances'][0]):
    print(f"{doc} → distance: {dist:.4f}")

