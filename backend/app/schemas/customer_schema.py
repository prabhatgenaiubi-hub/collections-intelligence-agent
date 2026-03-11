"""
Pydantic schemas for Customer data — used in API request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional


class CustomerBase(BaseModel):
    """Shared fields for customer."""
    customer_name: str = Field(..., example="Rajesh Kumar")
    mobile_number: str = Field(..., example="9876543210")
    email_id: Optional[str] = Field(None, example="rajesh@email.com")
    preferred_language: str = Field("English", example="Hindi")
    employment_type: str = Field(..., example="Salaried")
    company_name: Optional[str] = Field(None, example="Infosys Ltd")
    monthly_income: float = Field(..., example=75000.0)
    credit_score: int = Field(..., example=720)


class CustomerCreate(CustomerBase):
    """Schema for creating a new customer."""
    customer_id: str = Field(..., example="CUST-1001")


class CustomerResponse(CustomerBase):
    """Schema for customer API response."""
    customer_id: str

    class Config:
        from_attributes = True  # Pydantic v2: allows ORM model → schema conversion