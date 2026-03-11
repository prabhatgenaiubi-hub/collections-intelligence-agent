"""
Seed script to load CSV data into SQLite database.
Run from backend folder:  python -m scripts.seed_data
"""
import sys
import os
import pandas as pd
from datetime import datetime

# Add backend directory to Python path so imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.postgres import SessionLocal, init_db
from app.models.customer_model import Customer
from app.models.loan_model import Loan
from app.models.payment_model import Payment
from app.models.interaction_model import Interaction


def seed_customers(db, csv_path: str):
    """Load customers from CSV."""
    df = pd.read_csv(csv_path)
    count = 0
    for _, row in df.iterrows():
        existing = db.query(Customer).filter(Customer.customer_id == row["customer_id"]).first()
        if not existing:
            customer = Customer(
                customer_id=row["customer_id"],
                customer_name=row["customer_name"],
                mobile_number=str(row["mobile_number"]),
                email_id=row["email_id"],
                preferred_language=row["preferred_language"],
                employment_type=row["employment_type"],
                company_name=row["company_name"],
                monthly_income=float(row["monthly_income"]),
                credit_score=int(row["credit_score"]),
            )
            db.add(customer)
            count += 1
    db.commit()
    print(f"  ✅ Customers seeded: {count} new records")


def seed_loans(db, csv_path: str):
    """Load loans from CSV."""
    df = pd.read_csv(csv_path)
    count = 0
    for _, row in df.iterrows():
        existing = db.query(Loan).filter(Loan.loan_id == row["loan_id"]).first()
        if not existing:
            loan = Loan(
                loan_id=row["loan_id"],
                customer_id=row["customer_id"],
                loan_type=row["loan_type"],
                loan_amount=float(row["loan_amount"]),
                interest_rate=float(row["interest_rate"]),
                emi_amount=float(row["emi_amount"]),
                emi_due_date=int(row["emi_due_date"]),
                outstanding_balance=float(row["outstanding_balance"]),
                days_past_due=int(row["days_past_due"]),
            )
            db.add(loan)
            count += 1
    db.commit()
    print(f"  ✅ Loans seeded: {count} new records")


def seed_payments(db, csv_path: str):
    """Load payments from CSV."""
    df = pd.read_csv(csv_path)
    count = 0
    for _, row in df.iterrows():
        existing = db.query(Payment).filter(Payment.payment_id == row["payment_id"]).first()
        if not existing:
            payment = Payment(
                payment_id=row["payment_id"],
                loan_id=row["loan_id"],
                payment_date=datetime.strptime(row["payment_date"], "%Y-%m-%d").date(),
                payment_amount=float(row["payment_amount"]),
                payment_method=row["payment_method"],
            )
            db.add(payment)
            count += 1
    db.commit()
    print(f"  ✅ Payments seeded: {count} new records")


def seed_interactions(db):
    """Seed sample interaction history data (hardcoded since no CSV yet)."""
    sample_interactions = [
        {
            "interaction_id": "INT-20001",
            "customer_id": "CUST-1001",
            "interaction_type": "Voice",
            "interaction_time": datetime(2026, 3, 10, 10, 30),
            "conversation_text": "Customer promised to pay EMI next week due to salary delay.",
            "agent_id": "AGT-101",
            "sentiment_score": 0.3,
            "interaction_outcome": "Promise to Pay",
        },
        {
            "interaction_id": "INT-20002",
            "customer_id": "CUST-1001",
            "interaction_type": "SMS",
            "interaction_time": datetime(2026, 2, 5, 9, 0),
            "conversation_text": "Reminder SMS sent for upcoming EMI due on 5th Feb.",
            "agent_id": "AGT-102",
            "sentiment_score": 0.0,
            "interaction_outcome": "No Response",
        },
        {
            "interaction_id": "INT-20003",
            "customer_id": "CUST-1003",
            "interaction_type": "Voice",
            "interaction_time": datetime(2026, 2, 20, 14, 15),
            "conversation_text": "Customer stated business is slow. Requested EMI restructure.",
            "agent_id": "AGT-101",
            "sentiment_score": -0.2,
            "interaction_outcome": "Restructure Agreed",
        },
        {
            "interaction_id": "INT-20004",
            "customer_id": "CUST-1004",
            "interaction_type": "Chat",
            "interaction_time": datetime(2026, 1, 25, 11, 0),
            "conversation_text": "Customer refused to pay. Claimed job loss.",
            "agent_id": "AGT-103",
            "sentiment_score": -0.7,
            "interaction_outcome": "Refusal",
        },
        {
            "interaction_id": "INT-20005",
            "customer_id": "CUST-1007",
            "interaction_type": "Voice",
            "interaction_time": datetime(2026, 1, 15, 16, 45),
            "conversation_text": "Customer not reachable. Voicemail left.",
            "agent_id": "AGT-102",
            "sentiment_score": 0.0,
            "interaction_outcome": "No Response",
        },
        {
            "interaction_id": "INT-20006",
            "customer_id": "CUST-1009",
            "interaction_type": "SMS",
            "interaction_time": datetime(2026, 3, 1, 8, 0),
            "conversation_text": "Reminder sent. Customer replied will pay by 10th.",
            "agent_id": "AGT-101",
            "sentiment_score": 0.4,
            "interaction_outcome": "Promise to Pay",
        },
        {
            "interaction_id": "INT-20007",
            "customer_id": "CUST-1010",
            "interaction_type": "Voice",
            "interaction_time": datetime(2026, 2, 15, 13, 30),
            "conversation_text": "Customer agreed to partial payment of ₹15,000 this month.",
            "agent_id": "AGT-103",
            "sentiment_score": 0.1,
            "interaction_outcome": "Partial Payment",
        },
    ]

    count = 0
    for data in sample_interactions:
        existing = db.query(Interaction).filter(
            Interaction.interaction_id == data["interaction_id"]
        ).first()
        if not existing:
            interaction = Interaction(**data)
            db.add(interaction)
            count += 1
    db.commit()
    print(f"  ✅ Interactions seeded: {count} new records")


def main():
    """Run all seed functions."""
    print("\n🌱 Seeding database...\n")

    # Initialize tables
    init_db()
    print("  ✅ Tables created\n")

    # Get data directory path
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")

    db = SessionLocal()
    try:
        seed_customers(db, os.path.join(data_dir, "sample_customer.csv"))
        seed_loans(db, os.path.join(data_dir, "sample_loans.csv"))
        seed_payments(db, os.path.join(data_dir, "sample_payments.csv"))
        seed_interactions(db)
    finally:
        db.close()

    print("\n✅ All data seeded successfully!\n")


if __name__ == "__main__":
    main()