"""
Workflow Routes — Main endpoint for the LangGraph collections pipeline.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from app.langgraph_workflow.collections_workflow import collections_graph

router = APIRouter(prefix="/workflow", tags=["Workflow"])


class WorkflowRequest(BaseModel):
    customer_id: str = Field(..., example="CUST-1001")
    message: str = Field(
        default="",
        example="Analyze this customer's risk and recommend a strategy",
    )


class WorkflowResponse(BaseModel):
    customer_id: str
    detected_language: str
    response: str
    error: Optional[str] = None


@router.post("/process", response_model=WorkflowResponse)
def process_workflow(request: WorkflowRequest):
    """
    Run the full collections intelligence pipeline.

    This is the MAIN endpoint that orchestrates:
    1. Language detection + translation
    2. SQL + Vector DB context gathering
    3. Analytics (DPD, risk, recommendation)
    4. RAG context enrichment
    5. LLM explanation generation
    6. Response translation (if non-English)
    """
    initial_state = {
        "customer_id": request.customer_id,
        "user_message": request.message or f"Analyze collections risk for {request.customer_id}",
    }

    # Run the LangGraph pipeline
    result = collections_graph.invoke(initial_state)

    return WorkflowResponse(
        customer_id=request.customer_id,
        detected_language=result.get("language", "English"),
        response=result.get("final_response", "No response generated."),
        error=result.get("error"),
    )