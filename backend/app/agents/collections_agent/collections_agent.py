"""
Collections Agent — Orchestrates all analytics for a customer.

Takes raw context data and runs:
- DPD classification
- Payment trend analysis
- EMI delay detection
- Financial exposure calculation
- Risk segmentation
- Strategy recommendation
"""
from typing import Dict, Any, List
from app.services.analytics_service import (
    classify_dpd,
    analyze_payment_trends,
    calculate_financial_exposure,
    detect_emi_delay_pattern,
)
from app.services.risk_segmentation_service import generate_risk_profile
from app.services.recommendation_service import recommend_action

def run_analytics(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the full analytics pipeline on gathered context.

    Args:
        context: output from context_agent.gather_context()

    Returns:
        Dict with all analytics results
    """
    customer = context["customer"]
    loan = context["loan"]
    payments = context["payments"]

    # --- DPD Classification ---
    dpd_class = classify_dpd(loan["days_past_due"])

    # --- Payment Trends ---
    payment_trends = analyze_payment_trends(
        payments=payments,
        emi_amount=loan["emi_amount"],
        emi_due_date=loan["emi_due_date"],
    )

    # --- EMI Delay Pattern ---
    delay_pattern = detect_emi_delay_pattern(
        payments=payments,
        emi_due_date=loan["emi_due_date"],
    )

    # --- Financial Exposure ---
    exposure = calculate_financial_exposure(
        outstanding_balance=loan["outstanding_balance"],
        emi_amount=loan["emi_amount"],
        days_past_due=loan["days_past_due"],
    )

    # --- Risk Profile ---
    income_to_emi = (
        customer["monthly_income"] / loan["emi_amount"]
        if loan["emi_amount"] > 0 else 0
    )

    risk_profile = generate_risk_profile(
        days_past_due=loan["days_past_due"],
        credit_score=customer["credit_score"],
        payment_consistency=payment_trends["payment_consistency"],
        income_to_emi_ratio=income_to_emi,
        employment_type=customer["employment_type"],
        delay_trend=delay_pattern["delay_trend"],
        outstanding_balance=loan["outstanding_balance"],
    )

    # --- Strategy Recommendation ---
    recommendation = recommend_action(
        customer_segment=risk_profile["customer_segment"],
        days_past_due=loan["days_past_due"],
        outstanding_balance=loan["outstanding_balance"],
        self_cure_probability=risk_profile["self_cure_probability"],
        payment_consistency=payment_trends["payment_consistency"],
    )

    return {
        "dpd_classification": dpd_class,
        "payment_trends": payment_trends,
        "delay_pattern": delay_pattern,
        "financial_exposure": exposure,
        "risk_profile": risk_profile,
        "recommendation": recommendation,
    }