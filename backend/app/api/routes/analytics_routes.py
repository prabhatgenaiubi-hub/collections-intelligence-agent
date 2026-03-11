"""
API routes for Analytics — Risk Assessment Engine.

Main endpoint:
    POST /analytics/risk-assessment/{customer_id}

This orchestrates all deterministic calculations and returns a
complete risk assessment with strategy recommendation.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

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

from app.schemas.risk_schema import FullRiskAssessmentResponse

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.post("/risk-assessment/{customer_id}", response_model=FullRiskAssessmentResponse)
def run_risk_assessment(
    customer_id: str,
    loan_id: Optional[str] = Query(None, description="Specific loan ID. If not provided, uses the first loan found."),
    db: Session = Depends(get_db),
):
    """
    Run a full risk assessment for a customer's loan.

    This endpoint orchestrates:
    1. DPD classification
    2. Payment trend analysis
    3. EMI delay pattern detection
    4. Financial exposure calculation
    5. Risk segmentation (self-cure probability, segment, VaR)
    6. Recovery strategy recommendation (action, NPV, expected recovery)

    All calculations are deterministic — no LLM involved.
    """

    # --- 1. Fetch Customer ---
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")

    # --- 2. Fetch Loan ---
    if loan_id:
        loan = db.query(Loan).filter(
            Loan.loan_id == loan_id,
            Loan.customer_id == customer_id,
        ).first()
        if not loan:
            raise HTTPException(
                status_code=404,
                detail=f"Loan {loan_id} not found for customer {customer_id}",
            )
    else:
        # Get the first (or most overdue) loan for this customer
        loan = (
            db.query(Loan)
            .filter(Loan.customer_id == customer_id)
            .order_by(Loan.days_past_due.desc())
            .first()
        )
        if not loan:
            raise HTTPException(
                status_code=404,
                detail=f"No loans found for customer {customer_id}",
            )

    # --- 3. Fetch Payments ---
    payments_orm = (
        db.query(Payment)
        .filter(Payment.loan_id == loan.loan_id)
        .order_by(Payment.payment_date)
        .all()
    )
    payments_data = [
        {
            "payment_date": p.payment_date,
            "payment_amount": p.payment_amount,
            "payment_method": p.payment_method,
        }
        for p in payments_orm
    ]

    # --- 4. DPD Classification ---
    dpd_class = classify_dpd(loan.days_past_due)

    # --- 5. Payment Trend Analysis ---
    payment_trends = analyze_payment_trends(
        payments=payments_data,
        emi_amount=loan.emi_amount,
        emi_due_date=loan.emi_due_date,
    )

    # --- 6. Delay Pattern Detection ---
    delay_pattern = detect_emi_delay_pattern(
        payments=payments_data,
        emi_due_date=loan.emi_due_date,
    )

    # --- 7. Financial Exposure ---
    financial_exposure = calculate_financial_exposure(
        outstanding_balance=loan.outstanding_balance,
        emi_amount=loan.emi_amount,
        days_past_due=loan.days_past_due,
    )

    # --- 8. Risk Segmentation ---
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

    # --- 9. Strategy Recommendation ---
    strategy = recommend_action(
        customer_segment=risk_profile["customer_segment"],
        days_past_due=loan.days_past_due,
        outstanding_balance=loan.outstanding_balance,
        self_cure_probability=risk_profile["self_cure_probability"],
        payment_consistency=payment_trends["payment_consistency"],
    )

    # --- 10. Build Response ---
    return FullRiskAssessmentResponse(
        customer_id=customer.customer_id,
        customer_name=customer.customer_name,
        loan_id=loan.loan_id,
        loan_type=loan.loan_type,
        dpd_classification=dpd_class,
        days_past_due=loan.days_past_due,
        payment_trends=payment_trends,
        delay_pattern=delay_pattern,
        financial_exposure=financial_exposure,
        risk_profile=risk_profile,
        strategy=strategy,
    )