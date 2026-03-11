"""
API routes for LLM Reasoning Agent.

Endpoints:
- POST /reasoning/explain/{customer_id}  — Full explainable risk assessment
- POST /reasoning/summarize-interaction   — Summarize a conversation
- GET  /reasoning/health                  — Check Ollama connection
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel, Field

from app.db.postgres import get_db
from app.models.customer_model import Customer
from app.models.loan_model import Loan
from app.models.payment_model import Payment

from app.services.analytics_service import (
    classify_dpd,
    analyze_payment_trends,
    calculate_financial_exposure,
    detect_emi_delay_pattern,
)
from app.services.risk_segmentation_service import generate_risk_profile
from app.services.recommendation_service import recommend_action

from app.rag.retriever import retrieve_full_context

from app.agents.reasoning_agent.llm_client import call_llm, check_ollama_health
from app.agents.reasoning_agent.prompts import (
    SYSTEM_PROMPT,
    RISK_EXPLANATION_PROMPT,
    CONVERSATION_SUMMARY_PROMPT,
)

router = APIRouter(prefix="/reasoning", tags=["LLM Reasoning"])


# --- Response Schemas ---

class ExplainableAssessmentResponse(BaseModel):
    """Full explainable risk assessment with LLM reasoning."""
    customer_id: str
    customer_name: str
    loan_id: str

    # Analytics results (numbers)
    dpd_classification: str
    days_past_due: int
    customer_segment: str
    self_cure_probability: float
    value_at_risk: float
    recommended_action: str
    risk_level: str
    expected_recovery: float
    estimated_npv: float

    # LLM explanation (natural language)
    llm_explanation: str

    # RAG context used
    rag_context_used: str


class SummarizeRequest(BaseModel):
    """Request to summarize an interaction."""
    interaction_type: str = Field(..., example="Voice")
    interaction_time: str = Field(..., example="2026-03-10 10:30")
    interaction_outcome: str = Field(..., example="Promise to Pay")
    conversation_text: str = Field(
        ...,
        example="Customer said his salary was delayed this month. He promised to pay the EMI by next Friday."
    )


class SummarizeResponse(BaseModel):
    """Summarized interaction."""
    original_text: str
    summary: str


# --- Endpoints ---

@router.post("/explain/{customer_id}", response_model=ExplainableAssessmentResponse)
def explain_risk_assessment(
    customer_id: str,
    loan_id: Optional[str] = Query(None, description="Specific loan ID"),
    db: Session = Depends(get_db),
):
    """
    Generate a full explainable risk assessment with LLM reasoning.

    This endpoint:
    1. Runs all deterministic analytics (same as /analytics/risk-assessment)
    2. Retrieves RAG context (past interactions + policies)
    3. Sends everything to Llama-3 for human-readable explanation
    4. Returns both numbers AND natural language explanation

    Requires: Ollama running with llama3 model.
    If Ollama is unavailable, returns a fallback rule-based explanation.
    """

    # === Step 1: Fetch Data ===
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")

    if loan_id:
        loan = db.query(Loan).filter(
            Loan.loan_id == loan_id, Loan.customer_id == customer_id
        ).first()
    else:
        loan = (
            db.query(Loan)
            .filter(Loan.customer_id == customer_id)
            .order_by(Loan.days_past_due.desc())
            .first()
        )

    if not loan:
        raise HTTPException(status_code=404, detail=f"No loans found for customer {customer_id}")

    payments_orm = (
        db.query(Payment).filter(Payment.loan_id == loan.loan_id)
        .order_by(Payment.payment_date).all()
    )
    payments_data = [
        {"payment_date": p.payment_date, "payment_amount": p.payment_amount, "payment_method": p.payment_method}
        for p in payments_orm
    ]

    # === Step 2: Run Analytics ===
    dpd_class = classify_dpd(loan.days_past_due)

    payment_trends = analyze_payment_trends(
        payments=payments_data, emi_amount=loan.emi_amount, emi_due_date=loan.emi_due_date
    )

    delay_pattern = detect_emi_delay_pattern(
        payments=payments_data, emi_due_date=loan.emi_due_date
    )

    financial_exposure = calculate_financial_exposure(
        outstanding_balance=loan.outstanding_balance,
        emi_amount=loan.emi_amount,
        days_past_due=loan.days_past_due,
    )

    income_to_emi_ratio = customer.monthly_income / loan.emi_amount if loan.emi_amount > 0 else 0

    risk_profile = generate_risk_profile(
        days_past_due=loan.days_past_due,
        credit_score=customer.credit_score,
        payment_consistency=payment_trends["payment_consistency"],
        income_to_emi_ratio=income_to_emi_ratio,
        employment_type=customer.employment_type,
        delay_trend=delay_pattern["delay_trend"],
        outstanding_balance=loan.outstanding_balance,
    )

    strategy = recommend_action(
        customer_segment=risk_profile["customer_segment"],
        days_past_due=loan.days_past_due,
        outstanding_balance=loan.outstanding_balance,
        self_cure_probability=risk_profile["self_cure_probability"],
        payment_consistency=payment_trends["payment_consistency"],
    )

    # === Step 3: RAG Context Retrieval ===
    rag_query = (
        f"{customer.customer_name} {risk_profile['customer_segment']} "
        f"{loan.loan_type} loan {loan.days_past_due} days past due "
        f"{strategy['recommended_action']}"
    )

    rag_result = retrieve_full_context(
        query=rag_query,
        customer_id=customer_id,
        top_k_interactions=3,
        top_k_policies=3,
    )
    rag_context_text = rag_result["combined_context_text"]

    # === Step 4: LLM Explanation ===
    prompt = RISK_EXPLANATION_PROMPT.format(
        customer_name=customer.customer_name,
        customer_id=customer.customer_id,
        loan_id=loan.loan_id,
        loan_type=loan.loan_type,
        monthly_income=customer.monthly_income,
        employment_type=customer.employment_type,
        credit_score=customer.credit_score,
        days_past_due=loan.days_past_due,
        dpd_classification=dpd_class,
        customer_segment=risk_profile["customer_segment"],
        self_cure_probability=risk_profile["self_cure_probability"],
        value_at_risk=risk_profile["value_at_risk"],
        total_payments=payment_trends["total_payments"],
        on_time_payments=payment_trends["on_time_payments"],
        late_payments=payment_trends["late_payments"],
        payment_consistency=payment_trends["payment_consistency"],
        delay_trend=delay_pattern["delay_trend"],
        outstanding_balance=loan.outstanding_balance,
        overdue_amount=financial_exposure["overdue_amount"],
        exposure_ratio=financial_exposure["exposure_ratio"],
        recommended_action=strategy["recommended_action"],
        risk_level=strategy["risk_level"],
        expected_recovery=strategy["expected_recovery"],
        estimated_npv=strategy["estimated_npv"],
        rag_context=rag_context_text,
    )

    llm_explanation = call_llm(prompt=prompt, system_prompt=SYSTEM_PROMPT)

    # === Step 5: Build Response ===
    return ExplainableAssessmentResponse(
        customer_id=customer.customer_id,
        customer_name=customer.customer_name,
        loan_id=loan.loan_id,
        dpd_classification=dpd_class,
        days_past_due=loan.days_past_due,
        customer_segment=risk_profile["customer_segment"],
        self_cure_probability=risk_profile["self_cure_probability"],
        value_at_risk=risk_profile["value_at_risk"],
        recommended_action=strategy["recommended_action"],
        risk_level=strategy["risk_level"],
        expected_recovery=strategy["expected_recovery"],
        estimated_npv=strategy["estimated_npv"],
        llm_explanation=llm_explanation,
        rag_context_used=rag_context_text,
    )


@router.post("/summarize-interaction", response_model=SummarizeResponse)
def summarize_interaction(request: SummarizeRequest):
    """
    Use LLM to summarize a customer interaction transcript.
    Useful for storing concise summaries in vector DB.
    """
    prompt = CONVERSATION_SUMMARY_PROMPT.format(
        interaction_type=request.interaction_type,
        interaction_time=request.interaction_time,
        interaction_outcome=request.interaction_outcome,
        conversation_text=request.conversation_text,
    )

    summary = call_llm(prompt=prompt, system_prompt=SYSTEM_PROMPT, max_tokens=256)

    return SummarizeResponse(
        original_text=request.conversation_text,
        summary=summary,
    )


@router.get("/health")
def check_llm_health():
    """
    Check Ollama server status and model availability.
    Call this to verify LLM is ready before using reasoning endpoints.
    """
    return check_ollama_health()