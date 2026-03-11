"""
Pydantic schemas for Interaction History data — used in API request/response validation.
Note: The Interaction ORM model will be added later (Step 3+).
      This schema is defined now so the API contract is clear.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class InteractionBase(BaseModel):
    """Shared fields for interaction history."""
    customer_id: str = Field(..., example="CUST-1001")
    interaction_type: str = Field(..., example="Voice")          # Voice / SMS / Chat / Email
    interaction_time: datetime = Field(..., example="2026-03-10T10:30:00")
    conversation_text: str = Field(..., example="Customer promised payment next week")
    agent_id: Optional[str] = Field(None, example="AGT-101")
    sentiment_score: Optional[float] = Field(None, ge=-1.0, le=1.0, example=0.3)
    interaction_outcome: str = Field(..., example="Promise to Pay")


class InteractionCreate(InteractionBase):
    """Schema for creating a new interaction."""
    interaction_id: str = Field(..., example="INT-20001")


class InteractionResponse(InteractionBase):
    """Schema for interaction API response."""
    interaction_id: str

    class Config:
        from_attributes = True