"""
SQLAlchemy ORM model for the payments table.
Maps to: Payment History Data schema from system design.
"""
from sqlalchemy import Column, String, Float, Date, ForeignKey
from app.db.postgres import Base


class Payment(Base):
    __tablename__ = "payments"

    payment_id = Column(String, primary_key=True, index=True)        # PK  e.g. "PAY-10001"
    loan_id = Column(String, ForeignKey("loans.loan_id"), nullable=False, index=True)  # FK
    payment_date = Column(Date, nullable=False)
    payment_amount = Column(Float, nullable=False)
    payment_method = Column(String, nullable=False)                  # UPI / NEFT / Auto-Debit / Cash / Cheque

    def __repr__(self):
        return f"<Payment {self.payment_id} - Loan {self.loan_id}>"