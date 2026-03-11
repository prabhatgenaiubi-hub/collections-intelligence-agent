"""
RAG Retriever — Semantic search across vector collections.

Provides retrieval functions for:
1. Interaction memory: find past interactions for a customer
2. Policy knowledge: find relevant policies/regulations for a query
3. Combined retrieval: search both collections for full context

All retrieval uses cosine similarity via ChromaDB.
"""
from typing import List, Dict, Any, Optional
from app.db.vector_db import (
    get_interaction_memory_collection,
    get_policy_knowledge_collection,
)
from app.rag.embeddings import generate_embedding


def retrieve_interaction_memory(
    query: str,
    customer_id: Optional[str] = None,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """
    Retrieve relevant past interaction summaries.

    Args:
        query: search query (e.g. "customer promised payment")
        customer_id: optional filter to only search this customer's interactions
        top_k: number of results to return

    Returns:
        List of dicts with: id, document, metadata, distance
    """
    collection = get_interaction_memory_collection()

    # Check if collection has any documents
    if collection.count() == 0:
        return []

    # Build query embedding
    query_embedding = generate_embedding(query)

    # Build where filter for customer_id if provided
    where_filter = {"customer_id": customer_id} if customer_id else None

    # Query ChromaDB
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),
        where=where_filter,
    )

    # Format results
    formatted = []
    if results and results["ids"] and results["ids"][0]:
        for i in range(len(results["ids"][0])):
            formatted.append({
                "id": results["ids"][0][i],
                "document": results["documents"][0][i],
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                "distance": results["distances"][0][i] if results["distances"] else None,
            })

    return formatted


def retrieve_policy_knowledge(
    query: str,
    category: Optional[str] = None,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """
    Retrieve relevant policy documents and regulatory guidelines.

    Args:
        query: search query (e.g. "restructuring eligibility criteria")
        category: optional filter (e.g. "recovery_policy", "regulatory", "procedure")
        top_k: number of results to return

    Returns:
        List of dicts with: id, document, metadata, distance
    """
    collection = get_policy_knowledge_collection()

    if collection.count() == 0:
        return []

    query_embedding = generate_embedding(query)

    where_filter = {"category": category} if category else None

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),
        where=where_filter,
    )

    formatted = []
    if results and results["ids"] and results["ids"][0]:
        for i in range(len(results["ids"][0])):
            formatted.append({
                "id": results["ids"][0][i],
                "document": results["documents"][0][i],
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                "distance": results["distances"][0][i] if results["distances"] else None,
            })

    return formatted


def retrieve_full_context(
    query: str,
    customer_id: Optional[str] = None,
    top_k_interactions: int = 3,
    top_k_policies: int = 3,
) -> Dict[str, Any]:
    """
    Combined retrieval: search both interactions and policies.
    This is the main function used by the LangGraph workflow.

    Args:
        query: search query
        customer_id: optional customer filter for interactions
        top_k_interactions: number of interaction results
        top_k_policies: number of policy results

    Returns:
        Dict with:
        - interaction_context: list of relevant past interactions
        - policy_context: list of relevant policies
        - combined_context_text: formatted text ready for LLM prompt
    """
    interactions = retrieve_interaction_memory(
        query=query,
        customer_id=customer_id,
        top_k=top_k_interactions,
    )

    policies = retrieve_policy_knowledge(
        query=query,
        top_k=top_k_policies,
    )

    # Build formatted context string for LLM
    context_parts = []

    if interactions:
        context_parts.append("=== PAST INTERACTIONS ===")
        for item in interactions:
            context_parts.append(f"- {item['document']}")

    if policies:
        context_parts.append("\n=== RELEVANT POLICIES ===")
        for item in policies:
            context_parts.append(f"- {item['document']}")

    combined_text = "\n".join(context_parts) if context_parts else "No relevant context found."

    return {
        "interaction_context": interactions,
        "policy_context": policies,
        "combined_context_text": combined_text,
    }