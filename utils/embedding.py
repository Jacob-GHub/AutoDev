# from transformers import AutoTokenizer, AutoModel
# import torch
# from sentence_transformers import SentenceTransformer
from sentence_transformers import util



# tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/code-search-net")
# model = SentenceTransformer("microsoft/codebert-base")
# # model = AutoModel.from_pretrained("microsoft/codebert-base")

# # def embed(text):
# #     return model.encode(text, normalize_embeddings=True).tolist()


# def embed_code(code_string):
#     inputs = tokenizer(code_string, return_tensors='pt')
#     outputs = model(**inputs)
#     embeddings = outputs.last_hidden_state.mean(dim=1)
#     return embeddings.squeeze().tolist()
#     # return model.encode(code_string, normalize_embeddings=True).tolist()

# def embed_text(text):
#     inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
#     with torch.no_grad():
#         outputs = model(**inputs)
#     return outputs.last_hidden_state.mean(dim=1).squeeze().tolist()
#     # return model.encode(text, normalize_embeddings=True).tolist()


from sentence_transformers import SentenceTransformer

model = SentenceTransformer("microsoft/codebert-base")

def embed_code(code_string):
    return model.encode(code_string, normalize_embeddings=True).tolist()

def embed_text(text):
    return model.encode(text, normalize_embeddings=True).tolist()

# def similarity(code_str, text_str):
#     code_emb = embed_code(code_str)
#     text_emb = embed_text(text_str)
#     return util.cos_sim(code_emb, text_emb).item()

# code_sample = "print(hello world)"
# text_sample = "This function adds two numbers"

# print("Similarity:", similarity(code_sample, text_sample))
