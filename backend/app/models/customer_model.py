"""
SQLAlchemy ORM model for the customers table.
Maps to: Customer Data schema from system design.
"""
from sqlalchemy import Column, String, Float, Integer
from app.db.postgres import Base


class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(String, primary_key=True, index=True)       # PK  e.g. "CUST-1001"
    customer_name = Column(String, nullable=False)
    mobile_number = Column(String, nullable=False)
    email_id = Column(String, nullable=True)
    preferred_language = Column(String, default="English")            # English / Hindi / Tamil etc.
    employment_type = Column(String, nullable=False)                  # Salaried / Self-Employed
    company_name = Column(String, nullable=True)
    monthly_income = Column(Float, nullable=False)
    credit_score = Column(Integer, nullable=False)

    def __repr__(self):
        return f"<Customer {self.customer_id} - {self.customer_name}>"
    