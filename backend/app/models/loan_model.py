"""
SQLAlchemy ORM model for the loans table.
Maps to: Loan Account Data schema from system design.
"""
from sqlalchemy import Column, String, Float, Integer, Date, ForeignKey
from app.db.postgres import Base


class Loan(Base):
    __tablename__ = "loans"

    loan_id = Column(String, primary_key=True, index=True)           # PK  e.g. "LN-5001"
    customer_id = Column(String, ForeignKey("customers.customer_id"), nullable=False, index=True)  # FK
    loan_type = Column(String, nullable=False)                       # Personal / Home / Auto / Education
    loan_amount = Column(Float, nullable=False)
    interest_rate = Column(Float, nullable=False)                    # e.g. 10.5 means 10.5%
    emi_amount = Column(Float, nullable=False)
    emi_due_date = Column(Integer, nullable=False)                   # Day of month (1-28)
    outstanding_balance = Column(Float, nullable=False)
    days_past_due = Column(Integer, default=0)

    def __repr__(self):
        return f"<Loan {self.loan_id} - Customer {self.customer_id}>"