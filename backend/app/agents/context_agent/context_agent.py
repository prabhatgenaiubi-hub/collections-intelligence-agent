"""
Context Agent — Gathers all relevant data for a customer.

Retrieves:
- Customer record from SQLite
- Loan details from SQLite
- Payment history from SQLite
- Past interactions from ChromaDB (via RAG)
- Relevant policies from ChromaDB (via RAG)
"""
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.customer_model import Customer
from app.models.loan_model import Loan
from app.models.payment_model import Payment
from app.rag.retriever import retrieve_full_context


def gather_context(db: Session, customer_id: str, query: str = "") -> Dict[str, Any]:
    """
    Gather all context needed for the collections workflow.

    Args:
        db: SQLAlchemy session
        customer_id: e.g. "CUST-1001"
        query: optional search query for RAG retrieval

    Returns:
        Dict with customer, loan, payments, and RAG context
    """
    # --- SQL Data ---
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        return {"error": f"Customer {customer_id} not found"}

    loans = db.query(Loan).filter(Loan.customer_id == customer_id).all()
    if not loans:
        return {"error": f"No loans found for {customer_id}", "customer": _customer_dict(customer)}

    # Use the first loan (primary) for analysis
    loan = loans[0]

    payments = (
        db.query(Payment)
        .filter(Payment.loan_id == loan.loan_id)
        .order_by(Payment.payment_date)
        .all()
    )

    # --- RAG Context ---
    rag_query = query or f"collections strategy for {customer.customer_name} {loan.loan_type} loan"
    rag_context = retrieve_full_context(
        query=rag_query,
        customer_id=customer_id,
        top_k_interactions=3,
        top_k_policies=3,
    )

    return {
        "customer": _customer_dict(customer),
        "loan": _loan_dict(loan),
        "payments": [_payment_dict(p) for p in payments],
        "rag_context": rag_context,
    }


def _customer_dict(customer: Customer) -> Dict[str, Any]:
    """Convert Customer ORM object to dict."""
    return {
        "customer_id": customer.customer_id,
        "customer_name": customer.customer_name,
        "mobile_number": customer.mobile_number,
        "email_id": customer.email_id,
        "preferred_language": customer.preferred_language,
        "employment_type": customer.employment_type,
        "company_name": customer.company_name,
        "monthly_income": customer.monthly_income,
        "credit_score": customer.credit_score,
    }


def _loan_dict(loan: Loan) -> Dict[str, Any]:
    """Convert Loan ORM object to dict."""
    return {
        "loan_id": loan.loan_id,
        "customer_id": loan.customer_id,
        "loan_type": loan.loan_type,
        "loan_amount": loan.loan_amount,
        "outstanding_balance": loan.outstanding_balance,
        "emi_amount": loan.emi_amount,
        "interest_rate": loan.interest_rate,
        "emi_due_date": loan.emi_due_date,
        "days_past_due": loan.days_past_due,
    }


def _payment_dict(payment: Payment) -> Dict[str, Any]:
    """Convert Payment ORM object to dict."""
    return {
        "payment_id": payment.payment_id,
        "loan_id": payment.loan_id,
        "payment_date": payment.payment_date,
        "payment_amount": payment.payment_amount,
        "payment_method": payment.payment_method,
    }