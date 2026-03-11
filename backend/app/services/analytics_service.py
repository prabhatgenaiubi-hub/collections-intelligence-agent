"""
Analytics Service — Deterministic financial calculations.

All calculations here are pure Python (no LLM).
The LLM will later EXPLAIN these results, not compute them.

Calculations:
- Days Past Due (DPD) classification
- Payment trend analysis (late payments, consistency)
- Financial exposure estimation
- Net Present Value (NPV) of expected recovery
- EMI delay detection
"""
from datetime import date, timedelta
from typing import List, Dict, Any, Optional
from app.core.constants import (
    DAYS_PAST_DUE_LOW, DAYS_PAST_DUE_MEDIUM,
    DAYS_PAST_DUE_HIGH, DAYS_PAST_DUE_CRITICAL,
)


def classify_dpd(days_past_due: int) -> str:
    """
    Classify Days Past Due into risk buckets.

    Buckets:
    - 0 days       → "On-Time"
    - 1-14 days    → "Early Warning"
    - 15-29 days   → "Pre-Delinquent"
    - 30-59 days   → "Delinquent"
    - 60+ days     → "Critical"
    """
    if days_past_due <= DAYS_PAST_DUE_LOW:
        return "On-Time"
    elif days_past_due < DAYS_PAST_DUE_MEDIUM:
        return "Early Warning"
    elif days_past_due < DAYS_PAST_DUE_HIGH:
        return "Pre-Delinquent"
    elif days_past_due < DAYS_PAST_DUE_CRITICAL:
        return "Delinquent"
    else:
        return "Critical"


def analyze_payment_trends(
    payments: List[Dict[str, Any]],
    emi_amount: float,
    emi_due_date: int,
) -> Dict[str, Any]:
    """
    Analyze payment history to detect patterns.

    Returns:
    - total_payments: count of payments
    - on_time_payments: count paid on or before due date
    - late_payments: count paid after due date
    - missed_payments: months with no payment (estimated)
    - average_delay_days: average days late for late payments
    - payment_consistency: ratio of on-time to total (0.0 - 1.0)
    - partial_payments: count of payments less than EMI amount
    - average_payment_amount: mean payment amount
    """
    if not payments:
        return {
            "total_payments": 0,
            "on_time_payments": 0,
            "late_payments": 0,
            "missed_payments": 0,
            "average_delay_days": 0.0,
            "payment_consistency": 0.0,
            "partial_payments": 0,
            "average_payment_amount": 0.0,
        }

    total = len(payments)
    on_time = 0
    late = 0
    delay_days_list = []
    partial = 0
    total_amount = 0.0

    for p in payments:
        pay_date = p["payment_date"]  # date object
        pay_amount = p["payment_amount"]
        total_amount += pay_amount

        # Check if paid on time (on or before due date of that month)
        due_date_that_month = pay_date.replace(day=min(emi_due_date, 28))
        if pay_date <= due_date_that_month:
            on_time += 1
        else:
            late += 1
            delay = (pay_date - due_date_that_month).days
            delay_days_list.append(delay)

        # Check for partial payment
        if pay_amount < emi_amount * 0.95:  # 5% tolerance
            partial += 1

    avg_delay = round(sum(delay_days_list) / len(delay_days_list), 1) if delay_days_list else 0.0
    consistency = round(on_time / total, 2) if total > 0 else 0.0
    avg_amount = round(total_amount / total, 2) if total > 0 else 0.0

    # Estimate missed payments (based on months between first and last payment)
    if total >= 2:
        sorted_dates = sorted([p["payment_date"] for p in payments])
        months_span = (sorted_dates[-1].year - sorted_dates[0].year) * 12 + \
                      (sorted_dates[-1].month - sorted_dates[0].month) + 1
        missed = max(0, months_span - total)
    else:
        missed = 0

    return {
        "total_payments": total,
        "on_time_payments": on_time,
        "late_payments": late,
        "missed_payments": missed,
        "average_delay_days": avg_delay,
        "payment_consistency": consistency,
        "partial_payments": partial,
        "average_payment_amount": avg_amount,
    }


def calculate_financial_exposure(
    outstanding_balance: float,
    emi_amount: float,
    days_past_due: int,
) -> Dict[str, float]:
    """
    Calculate financial exposure metrics.

    Returns:
    - outstanding_balance: current balance
    - overdue_amount: EMIs missed × EMI amount
    - exposure_ratio: overdue / outstanding (higher = worse)
    """
    # Approximate missed EMIs from DPD
    missed_emis = max(0, days_past_due // 30)
    overdue_amount = round(missed_emis * emi_amount, 2)
    exposure_ratio = round(overdue_amount / outstanding_balance, 4) if outstanding_balance > 0 else 0.0

    return {
        "outstanding_balance": outstanding_balance,
        "overdue_amount": overdue_amount,
        "missed_emi_count": missed_emis,
        "exposure_ratio": exposure_ratio,
    }


def calculate_npv(
    expected_recovery: float,
    discount_rate: float = 0.12,
    months: int = 6,
) -> float:
    """
    Calculate Net Present Value of expected recovery.

    Uses simple NPV formula:
        NPV = FV / (1 + r/12)^n

    Args:
        expected_recovery: total expected recovery amount
        discount_rate: annual discount rate (default 12%)
        months: expected recovery horizon in months

    Returns:
        NPV value rounded to 2 decimals
    """
    monthly_rate = discount_rate / 12
    npv = expected_recovery / ((1 + monthly_rate) ** months)
    return round(npv, 2)


def calculate_expected_recovery(
    outstanding_balance: float,
    self_cure_probability: float,
    recovery_rate: float = 0.85,
) -> float:
    """
    Estimate expected recovery amount.

    Formula:
        Expected Recovery = Outstanding × (self_cure_prob × 1.0 + (1 - self_cure_prob) × recovery_rate)

    Higher self-cure probability → expect full recovery
    Lower self-cure → apply a recovery rate discount
    """
    weighted_rate = (self_cure_probability * 1.0) + ((1 - self_cure_probability) * recovery_rate)
    return round(outstanding_balance * weighted_rate, 2)


def detect_emi_delay_pattern(
    payments: List[Dict[str, Any]],
    emi_due_date: int,
) -> Dict[str, Any]:
    """
    Detect if there's a worsening delay pattern (delays increasing over time).

    Returns:
    - is_worsening: True if delays are increasing
    - recent_delay_days: delay in most recent payment
    - delay_trend: "Improving" / "Stable" / "Worsening"
    """
    if len(payments) < 2:
        return {
            "is_worsening": False,
            "recent_delay_days": 0,
            "delay_trend": "Insufficient Data",
        }

    # Sort by payment date
    sorted_payments = sorted(payments, key=lambda p: p["payment_date"])

    delays = []
    for p in sorted_payments:
        pay_date = p["payment_date"]
        due_date = pay_date.replace(day=min(emi_due_date, 28))
        delay = max(0, (pay_date - due_date).days)
        delays.append(delay)

    recent_delay = delays[-1]

    # Check trend: compare first half average vs second half average
    mid = len(delays) // 2
    first_half_avg = sum(delays[:mid]) / mid if mid > 0 else 0
    second_half_avg = sum(delays[mid:]) / (len(delays) - mid) if (len(delays) - mid) > 0 else 0

    if second_half_avg > first_half_avg + 2:  # 2-day tolerance
        trend = "Worsening"
        is_worsening = True
    elif first_half_avg > second_half_avg + 2:
        trend = "Improving"
        is_worsening = False
    else:
        trend = "Stable"
        is_worsening = False

    return {
        "is_worsening": is_worsening,
        "recent_delay_days": recent_delay,
        "delay_trend": trend,
    }
