"""
Embedding model wrapper for generating vector embeddings.

Uses sentence-transformers (runs locally, no API needed).
Model: all-MiniLM-L6-v2 (fast, lightweight, good for semantic search).

Note: ChromaDB has its own default embedding function, but we define
this explicitly so we can reuse the same model across the app
(e.g., for embedding new interactions at runtime).
"""
from sentence_transformers import SentenceTransformer
from typing import List
from functools import lru_cache


# Model name — small and fast, good for POC
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"


@lru_cache()
def get_embedding_model() -> SentenceTransformer:
    """
    Load the embedding model (cached singleton).
    First call downloads the model (~80MB), subsequent calls reuse it.
    """
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return model


def generate_embedding(text: str) -> List[float]:
    """
    Generate an embedding vector for a single text string.

    Args:
        text: input text to embed

    Returns:
        List of floats (384-dimensional vector for MiniLM)
    """
    model = get_embedding_model()
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for multiple texts (batch operation, faster).

    Args:
        texts: list of input texts

    Returns:
        List of embedding vectors
    """
    model = get_embedding_model()
    embeddings = model.encode(texts, normalize_embeddings=True)
    return embeddings.tolist()