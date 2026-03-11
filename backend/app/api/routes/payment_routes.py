"""
API routes for Payment data.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.postgres import get_db
from app.models.payment_model import Payment
from app.schemas.customer_schema import CustomerResponse  # unused, but keeping imports clean

from pydantic import BaseModel, Field
from datetime import date


# --- Payment Schemas (defined here since they're simple) ---

class PaymentResponse(BaseModel):
    """Payment API response schema."""
    payment_id: str
    loan_id: str
    payment_date: date
    payment_amount: float
    payment_method: str

    class Config:
        from_attributes = True


class PaymentCreate(BaseModel):
    """Payment creation schema."""
    payment_id: str = Field(..., example="PAY-10025")
    loan_id: str = Field(..., example="LN-5001")
    payment_date: date = Field(..., example="2026-03-05")
    payment_amount: float = Field(..., example=16500.0)
    payment_method: str = Field(..., example="UPI")


router = APIRouter(prefix="/payments", tags=["Payments"])


@router.get("/loan/{loan_id}", response_model=List[PaymentResponse])
def get_payments_by_loan(loan_id: str, db: Session = Depends(get_db)):
    """Get all payments for a specific loan."""
    payments = db.query(Payment).filter(Payment.loan_id == loan_id).all()
    if not payments:
        raise HTTPException(status_code=404, detail=f"No payments found for loan {loan_id}")
    return payments


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(payment_id: str, db: Session = Depends(get_db)):
    """Get a single payment by ID."""
    payment = db.query(Payment).filter(Payment.payment_id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail=f"Payment {payment_id} not found")
    return payment


@router.post("/", response_model=PaymentResponse, status_code=201)
def create_payment(payload: PaymentCreate, db: Session = Depends(get_db)):
    """Record a new payment."""
    existing = db.query(Payment).filter(Payment.payment_id == payload.payment_id).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Payment {payload.payment_id} already exists")

    payment = Payment(**payload.model_dump())
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment