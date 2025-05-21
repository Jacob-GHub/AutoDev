import os
import numpy as np
from scipy import spatial
from openai import OpenAI
from dotenv import load_dotenv
from typing import List


load_dotenv()

client = OpenAI(
  api_key=os.getenv("OPENAI_API_KEY")
)

client = OpenAI(max_retries=5)


def get_embedding(text: str, model="text-embedding-3-small", **kwargs) -> List[float]:
    # replace newlines, which can negatively affect performance.
    text = text.replace("\n", " ")

    response = client.embeddings.create(input=[text], model=model, **kwargs)

    return response.data[0].embedding


async def aget_embedding(
    text: str, model="text-embedding-3-small", **kwargs
) -> List[float]:
    # replace newlines, which can negatively affect performance.
    text = text.replace("\n", " ")

    return (await client.embeddings.create(input=[text], model=model, **kwargs))[
        "data"
    ][0]["embedding"]


def get_embeddings(
    list_of_text: List[str], model="text-embedding-3-small", **kwargs
) -> List[List[float]]:
    assert len(list_of_text) <= 2048, "The batch size should not be larger than 2048."

    # replace newlines, which can negatively affect performance.
    list_of_text = [text.replace("\n", " ") for text in list_of_text]

    data = client.embeddings.create(input=list_of_text, model=model, **kwargs).data
    return [d.embedding for d in data]


async def aget_embeddings(
    list_of_text: List[str], model="text-embedding-3-small", **kwargs
) -> List[List[float]]:
    assert len(list_of_text) <= 2048, "The batch size should not be larger than 2048."

    # replace newlines, which can negatively affect performance.
    list_of_text = [text.replace("\n", " ") for text in list_of_text]

    data = (
        await client.embeddings.create(input=list_of_text, model=model, **kwargs)
    ).data
    return [d.embedding for d in data]


def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def distances_from_embeddings(
    query_embedding: List[float],
    embeddings: List[List[float]],
    distance_metric="cosine",
) -> List[List]:
    """Return the distances between a query embedding and a list of embeddings."""
    distance_metrics = {
        "cosine": spatial.distance.cosine,
        "L1": spatial.distance.cityblock,
        "L2": spatial.distance.euclidean,
        "Linf": spatial.distance.chebyshev,
    }
    distances = [
        distance_metrics[distance_metric](query_embedding, embedding)
        for embedding in embeddings
    ]
    return distances
