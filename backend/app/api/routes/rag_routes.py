"""
API routes for RAG (Retrieval-Augmented Generation) system.

Endpoints:
- POST /rag/search              — Combined search across all collections
- POST /rag/search/interactions — Search interaction memory only
- POST /rag/search/policies     — Search policy knowledge only
- GET  /rag/stats               — Collection statistics
"""
from fastapi import APIRouter, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.rag.retriever import (
    retrieve_interaction_memory,
    retrieve_policy_knowledge,
    retrieve_full_context,
)
from app.db.vector_db import (
    get_interaction_memory_collection,
    get_policy_knowledge_collection,
)

router = APIRouter(prefix="/rag", tags=["RAG - Knowledge Retrieval"])


# --- Request/Response Schemas ---

class RAGSearchRequest(BaseModel):
    """Request body for RAG search."""
    query: str = Field(..., example="What should I do for a customer 60 days past due?")
    customer_id: Optional[str] = Field(None, example="CUST-1001")
    top_k: int = Field(5, ge=1, le=20, example=5)


class RAGDocumentResponse(BaseModel):
    """Single retrieved document."""
    id: str
    document: str
    metadata: Dict[str, Any]
    distance: Optional[float] = None


class RAGSearchResponse(BaseModel):
    """Response for interaction or policy search."""
    query: str
    results_count: int
    results: List[RAGDocumentResponse]


class RAGFullContextResponse(BaseModel):
    """Response for combined search."""
    query: str
    interaction_results: List[RAGDocumentResponse]
    policy_results: List[RAGDocumentResponse]
    combined_context_text: str


class RAGStatsResponse(BaseModel):
    """Collection statistics."""
    interaction_memory_count: int
    policy_knowledge_count: int


# --- Endpoints ---

@router.post("/search", response_model=RAGFullContextResponse)
def search_full_context(request: RAGSearchRequest):
    """
    Search across both interaction memory and policy knowledge.
    Returns combined context text ready for LLM consumption.

    This is the primary endpoint used by the LangGraph workflow.
    """
    result = retrieve_full_context(
        query=request.query,
        customer_id=request.customer_id,
        top_k_interactions=min(request.top_k, 5),
        top_k_policies=min(request.top_k, 5),
    )

    return RAGFullContextResponse(
        query=request.query,
        interaction_results=result["interaction_context"],
        policy_results=result["policy_context"],
        combined_context_text=result["combined_context_text"],
    )


@router.post("/search/interactions", response_model=RAGSearchResponse)
def search_interactions(request: RAGSearchRequest):
    """
    Search interaction memory only.
    Useful for finding past conversations with a specific customer.
    """
    results = retrieve_interaction_memory(
        query=request.query,
        customer_id=request.customer_id,
        top_k=request.top_k,
    )

    return RAGSearchResponse(
        query=request.query,
        results_count=len(results),
        results=results,
    )


@router.post("/search/policies", response_model=RAGSearchResponse)
def search_policies(request: RAGSearchRequest):
    """
    Search policy knowledge only.
    Useful for finding specific policies or regulations.
    """
    results = retrieve_policy_knowledge(
        query=request.query,
        top_k=request.top_k,
    )

    return RAGSearchResponse(
        query=request.query,
        results_count=len(results),
        results=results,
    )


@router.get("/stats", response_model=RAGStatsResponse)
def get_rag_stats():
    """Get document counts for each ChromaDB collection."""
    interaction_collection = get_interaction_memory_collection()
    policy_collection = get_policy_knowledge_collection()

    return RAGStatsResponse(
        interaction_memory_count=interaction_collection.count(),
        policy_knowledge_count=policy_collection.count(),
    )