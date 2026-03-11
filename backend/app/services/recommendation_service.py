"""
Recommendation Service — Recovery strategy recommendation engine.

Based on the risk profile, recommends the optimal recovery action:
- Send Reminder (Self-Cure segment)
- Offer EMI Restructure (Medium Risk)
- Propose Settlement (High Risk, moderate exposure)
- Escalate to Recovery (High Risk, high exposure)

All logic is deterministic Python — no LLM.
"""
from typing import Dict, Any
from app.core.constants import (
    SEGMENT_SELF_CURE, SEGMENT_MEDIUM_RISK, SEGMENT_HIGH_RISK,
    ACTION_REMINDER, ACTION_RESTRUCTURE, ACTION_SETTLEMENT, ACTION_ESCALATE,
)
from app.services.analytics_service import calculate_expected_recovery, calculate_npv


def recommend_action(
    customer_segment: str,
    days_past_due: int,
    outstanding_balance: float,
    self_cure_probability: float,
    payment_consistency: float,
) -> Dict[str, Any]:
    """
    Recommend a recovery strategy based on segment and risk factors.

    Decision logic:
    ┌──────────────┬──────────┬───────────────────────────────┐
    │ Segment      │ DPD      │ Action                        │
    ├──────────────┼──────────┼───────────────────────────────┤
    │ Self-Cure    │ any      │ Send Reminder                 │
    │ Medium Risk  │ < 30     │ Send Reminder + Monitor       │
    │ Medium Risk  │ ≥ 30     │ Offer EMI Restructure         │
    │ High Risk    │ < 60     │ Propose Settlement            │
    │ High Risk    │ ≥ 60     │ Escalate to Recovery          │
    └──────────────┴──────────┴───────────────────────────────┘

    Returns:
    - recommended_action: primary action string
    - risk_level: Low / Medium / High / Critical
    - expected_recovery: estimated recovery amount
    - estimated_npv: NPV of expected recovery
    - reasoning_factors: list of reasons for the recommendation
    """
    reasoning_factors = []

    # --- Determine Action ---
    if customer_segment == SEGMENT_SELF_CURE:
        action = ACTION_REMINDER
        risk_level = "Low"
        reasoning_factors.append("Borrower has high self-cure probability")
        reasoning_factors.append("Historical payment pattern suggests voluntary repayment")

    elif customer_segment == SEGMENT_MEDIUM_RISK:
        if days_past_due < 30:
            action = ACTION_REMINDER
            risk_level = "Medium"
            reasoning_factors.append("Moderate risk — early stage delinquency")
            reasoning_factors.append("Gentle reminder may trigger payment")
        else:
            action = ACTION_RESTRUCTURE
            risk_level = "Medium"
            reasoning_factors.append("Moderate risk with extended overdue period")
            reasoning_factors.append("EMI restructure may improve repayment capacity")

    else:  # HIGH_RISK
        if days_past_due < 60:
            action = ACTION_SETTLEMENT
            risk_level = "High"
            reasoning_factors.append("High risk borrower with significant overdue")
            reasoning_factors.append("Settlement offer may maximize partial recovery")
        else:
            action = ACTION_ESCALATE
            risk_level = "Critical"
            reasoning_factors.append("Critical delinquency — 60+ days past due")
            reasoning_factors.append("Escalation to recovery team recommended")

    # --- Add context-specific reasoning ---
    if payment_consistency < 0.5:
        reasoning_factors.append("Low payment consistency indicates financial stress")
    if self_cure_probability < 0.3:
        reasoning_factors.append("Very low self-cure probability — active intervention needed")

    # --- Financial projections ---
    expected_recovery = calculate_expected_recovery(
        outstanding_balance=outstanding_balance,
        self_cure_probability=self_cure_probability,
    )

    # NPV with different horizons based on risk
    if risk_level in ("Low", "Medium"):
        npv_months = 3
    else:
        npv_months = 6

    estimated_npv = calculate_npv(
        expected_recovery=expected_recovery,
        months=npv_months,
    )

    return {
        "recommended_action": action,
        "risk_level": risk_level,
        "expected_recovery": expected_recovery,
        "estimated_npv": estimated_npv,
        "recovery_horizon_months": npv_months,
        "reasoning_factors": reasoning_factors,
    }

