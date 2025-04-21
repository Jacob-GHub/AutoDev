from sentence_transformers import SentenceTransformer, util

def embed(code,query):
    # Use a valid model — CodeBERT is trained for code
    model = SentenceTransformer("microsoft/codebert-base")

    # Encode code and query
    code_emb = model.encode(code, convert_to_tensor=True)
    query_emb = model.encode(query, convert_to_tensor=True)

    # Compute similarity
    sim = util.cos_sim(code_emb, query_emb)
    print(sim)
    print(sim.item())
