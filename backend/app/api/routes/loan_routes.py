"""
API routes for Loan data.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.postgres import get_db
from app.models.loan_model import Loan
from app.schemas.loan_schema import LoanResponse, LoanCreate

router = APIRouter(prefix="/loans", tags=["Loans"])


@router.get("/", response_model=List[LoanResponse])
def get_all_loans(db: Session = Depends(get_db)):
    """Get all loans."""
    loans = db.query(Loan).all()
    return loans


@router.get("/{loan_id}", response_model=LoanResponse)
def get_loan(loan_id: str, db: Session = Depends(get_db)):
    """Get a single loan by ID."""
    loan = db.query(Loan).filter(Loan.loan_id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail=f"Loan {loan_id} not found")
    return loan


@router.get("/customer/{customer_id}", response_model=List[LoanResponse])
def get_loans_by_customer(customer_id: str, db: Session = Depends(get_db)):
    """Get all loans for a specific customer."""
    loans = db.query(Loan).filter(Loan.customer_id == customer_id).all()
    if not loans:
        raise HTTPException(status_code=404, detail=f"No loans found for customer {customer_id}")
    return loans


@router.post("/", response_model=LoanResponse, status_code=201)
def create_loan(payload: LoanCreate, db: Session = Depends(get_db)):
    """Create a new loan."""
    existing = db.query(Loan).filter(Loan.loan_id == payload.loan_id).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Loan {payload.loan_id} already exists")

    loan = Loan(**payload.model_dump())
    db.add(loan)
    db.commit()
    db.refresh(loan)
    return loan