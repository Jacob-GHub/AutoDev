from transformers import AutoTokenizer, AutoModel
import torch

tokenizer = AutoTokenizer.from_pretrained("microsoft/codebert-base")
model = AutoModel.from_pretrained("microsoft/codebert-base")

def embed_code(code_string):
    inputs = tokenizer(code_string, return_tensors='pt')
    outputs = model(**inputs)
    embeddings = outputs.last_hidden_state.mean(dim=1)
    return embeddings.squeeze().tolist()
# .last_hidden_state.mean(dim=1).detach().numpy()[0]  # [batch_size, hidden_size]
# print(embeddings)
# def embed_lang(nl):
#     inputs = tokenizer(nl, return_tensors='pt')
#     outputs = model(**inputs)
#     embeddings = outputs.last_hidden_state.mean(dim=1)
#     return embeddings.squeeze().tolist()