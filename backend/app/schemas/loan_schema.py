"""
Pydantic schemas for Loan data — used in API request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional


class LoanBase(BaseModel):
    """Shared fields for loan."""
    customer_id: str = Field(..., example="CUST-1001")
    loan_type: str = Field(..., example="Personal")
    loan_amount: float = Field(..., example=500000.0)
    interest_rate: float = Field(..., example=10.5)
    emi_amount: float = Field(..., example=16500.0)
    emi_due_date: int = Field(..., ge=1, le=28, example=5)
    outstanding_balance: float = Field(..., example=420000.0)
    days_past_due: int = Field(0, ge=0, example=10)


class LoanCreate(LoanBase):
    """Schema for creating a new loan."""
    loan_id: str = Field(..., example="LN-5001")


class LoanResponse(LoanBase):
    """Schema for loan API response."""
    loan_id: str

    class Config:
        from_attributes = True