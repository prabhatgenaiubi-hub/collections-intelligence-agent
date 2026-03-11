"""
ChromaDB Vector Database connection and collection management.

Two collections:
- interaction_memory: stores customer interaction summaries with embeddings
- policy_knowledge: stores collection policies and regulatory guidelines

ChromaDB persists data locally to CHROMA_PERSIST_DIR (default: ./chroma_data)
"""
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.core.config import get_settings
from functools import lru_cache

settings = get_settings()


@lru_cache()
def get_chroma_client() -> chromadb.ClientAPI:
    """
    Get a persistent ChromaDB client (cached singleton).
    Data is stored in the local directory specified by CHROMA_PERSIST_DIR.
    """
    client = chromadb.PersistentClient(
        path=settings.CHROMA_PERSIST_DIR,
    )
    return client


def get_interaction_memory_collection():
    """
    Get or create the 'interaction_memory' collection.
    Stores: customer interaction summaries + embeddings.
    Metadata: customer_id, interaction_type, timestamp.
    """
    client = get_chroma_client()
    collection = client.get_or_create_collection(
        name="interaction_memory",
        metadata={"description": "Customer interaction summaries for context retrieval"},
    )
    return collection


def get_policy_knowledge_collection():
    """
    Get or create the 'policy_knowledge' collection.
    Stores: collection policies, regulatory guidelines, recovery procedures.
    Metadata: source, category, document_type.
    """
    client = get_chroma_client()
    collection = client.get_or_create_collection(
        name="policy_knowledge",
        metadata={"description": "Collection policies and regulatory guidelines for RAG"},
    )
    return collection


def reset_collection(collection_name: str):
    """Delete and recreate a collection (useful for re-seeding)."""
    client = get_chroma_client()
    try:
        client.delete_collection(name=collection_name)
    except Exception:
        pass  # Collection may not exist
    return client.get_or_create_collection(name=collection_name)