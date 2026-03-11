"""
Risk Segmentation Service — Micro-segmentation and self-cure probability.

Assigns each borrower to a risk segment based on multiple factors:
- Days Past Due
- Credit score
- Payment consistency
- Income-to-EMI ratio
- Employment type
- Delay trend

All logic is deterministic Python — no LLM.
"""
from typing import Dict, Any
from app.core.constants import (
    SEGMENT_SELF_CURE, SEGMENT_MEDIUM_RISK, SEGMENT_HIGH_RISK,
    SELF_CURE_THRESHOLD_HIGH, SELF_CURE_THRESHOLD_MEDIUM,
    EMPLOYMENT_SALARIED,
)


def calculate_self_cure_probability(
    days_past_due: int,
    credit_score: int,
    payment_consistency: float,
    income_to_emi_ratio: float,
    employment_type: str,
    delay_trend: str,
) -> float:
    """
    Calculate the probability that a borrower will self-cure (pay without intervention).

    Scoring model (weighted):
    - DPD score:            25% weight
    - Credit score:         20% weight
    - Payment consistency:  20% weight
    - Income/EMI ratio:     15% weight
    - Employment stability: 10% weight
    - Delay trend:          10% weight

    Returns: probability between 0.0 and 1.0
    """
    # --- DPD Score (lower DPD = better) ---
    if days_past_due == 0:
        dpd_score = 1.0
    elif days_past_due <= 10:
        dpd_score = 0.8
    elif days_past_due <= 20:
        dpd_score = 0.6
    elif days_past_due <= 30:
        dpd_score = 0.4
    elif days_past_due <= 60:
        dpd_score = 0.2
    else:
        dpd_score = 0.05

    # --- Credit Score (higher = better) ---
    if credit_score >= 750:
        credit_factor = 1.0
    elif credit_score >= 700:
        credit_factor = 0.8
    elif credit_score >= 650:
        credit_factor = 0.6
    elif credit_score >= 600:
        credit_factor = 0.4
    else:
        credit_factor = 0.2

    # --- Payment Consistency (direct use, 0-1) ---
    consistency_factor = payment_consistency

    # --- Income to EMI Ratio (higher = more capacity) ---
    if income_to_emi_ratio >= 5:
        income_factor = 1.0
    elif income_to_emi_ratio >= 3:
        income_factor = 0.7
    elif income_to_emi_ratio >= 2:
        income_factor = 0.5
    else:
        income_factor = 0.2

    # --- Employment Stability ---
    employment_factor = 0.8 if employment_type == EMPLOYMENT_SALARIED else 0.5

    # --- Delay Trend ---
    if delay_trend == "Improving":
        trend_factor = 0.9
    elif delay_trend == "Stable":
        trend_factor = 0.6
    elif delay_trend == "Worsening":
        trend_factor = 0.2
    else:  # Insufficient Data
        trend_factor = 0.5

    # --- Weighted Probability ---
    probability = (
        dpd_score * 0.25 +
        credit_factor * 0.20 +
        consistency_factor * 0.20 +
        income_factor * 0.15 +
        employment_factor * 0.10 +
        trend_factor * 0.10
    )

    return round(min(max(probability, 0.0), 1.0), 2)


def assign_segment(self_cure_probability: float) -> str:
    """
    Assign borrower to a risk segment based on self-cure probability.

    Segments:
    - Self-Cure:    probability >= 0.7  (likely to pay on their own)
    - Medium Risk:  0.4 <= probability < 0.7  (needs gentle nudge)
    - High Risk:    probability < 0.4  (needs active intervention)
    """
    if self_cure_probability >= SELF_CURE_THRESHOLD_HIGH:
        return SEGMENT_SELF_CURE
    elif self_cure_probability >= SELF_CURE_THRESHOLD_MEDIUM:
        return SEGMENT_MEDIUM_RISK
    else:
        return SEGMENT_HIGH_RISK


def calculate_value_at_risk(
    outstanding_balance: float,
    self_cure_probability: float,
) -> float:
    """
    Calculate Value-at-Risk (VaR) — expected potential loss.

    Formula:
        VaR = Outstanding Balance × (1 - self_cure_probability)

    Higher VaR = more money at risk of non-recovery.
    """
    var = outstanding_balance * (1 - self_cure_probability)
    return round(var, 2)


def generate_risk_profile(
    days_past_due: int,
    credit_score: int,
    payment_consistency: float,
    income_to_emi_ratio: float,
    employment_type: str,
    delay_trend: str,
    outstanding_balance: float,
) -> Dict[str, Any]:
    """
    Generate a complete risk profile for a borrower.

    Returns dict with:
    - self_cure_probability
    - customer_segment
    - value_at_risk
    - risk_factors (breakdown of individual scores)
    """
    # Calculate self-cure probability
    self_cure_prob = calculate_self_cure_probability(
        days_past_due=days_past_due,
        credit_score=credit_score,
        payment_consistency=payment_consistency,
        income_to_emi_ratio=income_to_emi_ratio,
        employment_type=employment_type,
        delay_trend=delay_trend,
    )

    # Assign segment
    segment = assign_segment(self_cure_prob)

    # Calculate VaR
    var = calculate_value_at_risk(outstanding_balance, self_cure_prob)

    return {
        "self_cure_probability": self_cure_prob,
        "customer_segment": segment,
        "value_at_risk": var,
        "risk_factors": {
            "days_past_due": days_past_due,
            "credit_score": credit_score,
            "payment_consistency": payment_consistency,
            "income_to_emi_ratio": round(income_to_emi_ratio, 2),
            "employment_type": employment_type,
            "delay_trend": delay_trend,
        },
    }