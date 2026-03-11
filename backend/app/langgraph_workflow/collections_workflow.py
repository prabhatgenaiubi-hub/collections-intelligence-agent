"""
LangGraph Workflow — Orchestrates the full collections intelligence pipeline.

Graph Nodes:
1. input_processor   — Validate and structure input
2. multilingual_node — Detect language, translate to English
3. context_node      — Gather SQL + RAG context
4. analytics_node    — Run all analytics
5. rag_node          — Enrich with RAG context text
6. reasoning_node    — LLM generates explanation
7. response_node     — Format + translate back to user language

Flow: input → multilingual → context → analytics → rag → reasoning → response
"""
from typing import TypedDict, Any, Dict, Optional
from langgraph.graph import StateGraph, END

# Agent imports (Option B — from separate named files)
from app.agents.multilingual_agent.multilingual_agent import (
    detect_language,
    translate_to_english,
    translate_from_english,
)
from app.agents.context_agent.context_agent import gather_context
from app.agents.collections_agent.collections_agent import run_analytics

# LLM + prompts
from app.agents.reasoning_agent.llm_client import call_llm
from app.agents.reasoning_agent.prompts import SYSTEM_PROMPT, RISK_EXPLANATION_PROMPT

# DB session
from app.db.postgres import SessionLocal


# ── State Schema ──────────────────────────────────────────────
class WorkflowState(TypedDict, total=False):
    """State passed between all nodes in the graph."""
    # Input
    customer_id: str
    user_message: str
    language: str            # detected language

    # Processed
    english_message: str     # translated to English
    context: Dict[str, Any]  # SQL + RAG data
    analytics: Dict[str, Any]  # analytics results
    rag_context_text: str    # formatted RAG text for LLM

    # Output
    llm_explanation: str     # English explanation from LLM
    final_response: str      # response in user's language
    error: Optional[str]     # error message if any


# ── Node Functions ────────────────────────────────────────────

def input_processor(state: WorkflowState) -> dict:
    """Validate and structure the input."""
    customer_id = state.get("customer_id", "").strip()
    user_message = state.get("user_message", "").strip()

    if not customer_id:
        return {"error": "customer_id is required"}
    if not user_message:
        user_message = f"Analyze collections risk for customer {customer_id}"

    return {
        "customer_id": customer_id,
        "user_message": user_message,
        "error": None,
    }


def multilingual_node(state: WorkflowState) -> dict:
    """Detect language and translate input to English."""
    if state.get("error"):
        return {}

    user_message = state["user_message"]
    language = detect_language(user_message)
    english_message = translate_to_english(user_message, language)

    return {
        "language": language,
        "english_message": english_message,
    }


def context_node(state: WorkflowState) -> dict:
    """Gather all context from SQL + Vector DB."""
    if state.get("error"):
        return {}

    db = SessionLocal()
    try:
        context = gather_context(
            db=db,
            customer_id=state["customer_id"],
            query=state.get("english_message", ""),
        )
        if "error" in context:
            return {"error": context["error"]}
        return {"context": context}
    finally:
        db.close()


def analytics_node(state: WorkflowState) -> dict:
    """Run the full analytics pipeline."""
    if state.get("error"):
        return {}

    context = state.get("context", {})
    analytics = run_analytics(context)
    return {"analytics": analytics}


def rag_node(state: WorkflowState) -> dict:
    """Extract RAG context text for the LLM prompt."""
    if state.get("error"):
        return {}

    context = state.get("context", {})
    rag_data = context.get("rag_context", {})
    rag_text = rag_data.get("combined_context_text", "No relevant context found.")
    return {"rag_context_text": rag_text}


def reasoning_node(state: WorkflowState) -> dict:
    """Call LLM to generate an explanation of the analytics."""
    if state.get("error"):
        return {}

    customer = state["context"]["customer"]
    loan = state["context"]["loan"]
    analytics = state["analytics"]
    risk = analytics["risk_profile"]
    trends = analytics["payment_trends"]
    exposure = analytics["financial_exposure"]
    rec = analytics["recommendation"]

    # Fill the prompt template
    prompt = RISK_EXPLANATION_PROMPT.format(
        customer_name=customer["customer_name"],
        customer_id=customer["customer_id"],
        loan_id=loan["loan_id"],
        loan_type=loan["loan_type"],
        monthly_income=customer["monthly_income"],
        employment_type=customer["employment_type"],
        credit_score=customer["credit_score"],
        days_past_due=loan["days_past_due"],
        dpd_classification=analytics["dpd_classification"],
        customer_segment=risk["customer_segment"],
        self_cure_probability=risk["self_cure_probability"],
        value_at_risk=risk["value_at_risk"],
        total_payments=trends["total_payments"],
        on_time_payments=trends["on_time_payments"],
        late_payments=trends["late_payments"],
        payment_consistency=trends["payment_consistency"],
        delay_trend=analytics["delay_pattern"]["delay_trend"],
        outstanding_balance=exposure["outstanding_balance"],
        overdue_amount=exposure["overdue_amount"],
        exposure_ratio=exposure["exposure_ratio"],
        recommended_action=rec["recommended_action"],
        risk_level=rec["risk_level"],
        expected_recovery=rec["expected_recovery"],
        estimated_npv=rec["estimated_npv"],
        rag_context=state.get("rag_context_text", ""),
    )

    explanation = call_llm(prompt=prompt, system_prompt=SYSTEM_PROMPT, temperature=0.3)
    return {"llm_explanation": explanation}


def response_node(state: WorkflowState) -> dict:
    """Format final response and translate if needed."""
    if state.get("error"):
        return {
            "final_response": f"Error: {state['error']}",
        }

    language = state.get("language", "English")
    explanation = state.get("llm_explanation", "No explanation generated.")

    # Translate back to user's language if not English
    final = translate_from_english(explanation, language)

    return {"final_response": final}


# ── Build Graph ───────────────────────────────────────────────

def build_workflow() -> StateGraph:
    """
    Construct the LangGraph StateGraph for the collections pipeline.

    Returns a compiled graph ready to .invoke()
    """
    workflow = StateGraph(WorkflowState)

    # Add nodes
    workflow.add_node("input_processor", input_processor)
    workflow.add_node("multilingual", multilingual_node)
    workflow.add_node("context", context_node)
    workflow.add_node("analytics", analytics_node)
    workflow.add_node("rag", rag_node)
    workflow.add_node("reasoning", reasoning_node)
    workflow.add_node("response", response_node)

    # Define edges (linear flow)
    workflow.set_entry_point("input_processor")
    workflow.add_edge("input_processor", "multilingual")
    workflow.add_edge("multilingual", "context")
    workflow.add_edge("context", "analytics")
    workflow.add_edge("analytics", "rag")
    workflow.add_edge("rag", "reasoning")
    workflow.add_edge("reasoning", "response")
    workflow.add_edge("response", END)

    return workflow.compile()


# Pre-built instance for import
collections_graph = build_workflow()