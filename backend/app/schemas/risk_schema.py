"""
Pydantic schemas for Risk Analysis API responses.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class PaymentTrendResponse(BaseModel):
    """Payment trend analysis results."""
    total_payments: int
    on_time_payments: int
    late_payments: int
    missed_payments: int
    average_delay_days: float
    payment_consistency: float
    partial_payments: int
    average_payment_amount: float


class DelayPatternResponse(BaseModel):
    """EMI delay pattern analysis."""
    is_worsening: bool
    recent_delay_days: int
    delay_trend: str


class FinancialExposureResponse(BaseModel):
    """Financial exposure metrics."""
    outstanding_balance: float
    overdue_amount: float
    missed_emi_count: int
    exposure_ratio: float


class RiskFactorsResponse(BaseModel):
    """Individual risk factor breakdown."""
    days_past_due: int
    credit_score: int
    payment_consistency: float
    income_to_emi_ratio: float
    employment_type: str
    delay_trend: str


class RiskProfileResponse(BaseModel):
    """Risk segmentation results."""
    self_cure_probability: float
    customer_segment: str
    value_at_risk: float
    risk_factors: RiskFactorsResponse


class StrategyRecommendationResponse(BaseModel):
    """Recovery strategy recommendation."""
    recommended_action: str
    risk_level: str
    expected_recovery: float
    estimated_npv: float
    recovery_horizon_months: int
    reasoning_factors: List[str]


class FullRiskAssessmentResponse(BaseModel):
    """
    Complete risk assessment response combining all analytics.
    This is what the API returns for POST /analytics/risk-assessment/{customer_id}
    """
    # Customer & loan identifiers
    customer_id: str
    customer_name: str
    loan_id: str
    loan_type: str

    # DPD classification
    dpd_classification: str
    days_past_due: int

    # Payment trends
    payment_trends: PaymentTrendResponse

    # Delay pattern
    delay_pattern: DelayPatternResponse

    # Financial exposure
    financial_exposure: FinancialExposureResponse

    # Risk profile
    risk_profile: RiskProfileResponse

    # Strategy recommendation
    strategy: StrategyRecommendationResponse

    