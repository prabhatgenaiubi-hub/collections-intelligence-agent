"""
SQLAlchemy ORM model for the interactions table.
Maps to: Interaction History Data schema from system design.
"""
from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from app.db.postgres import Base


class Interaction(Base):
    __tablename__ = "interactions"

    interaction_id = Column(String, primary_key=True, index=True)     # PK  e.g. "INT-20001"
    customer_id = Column(String, ForeignKey("customers.customer_id"), nullable=False, index=True)  # FK
    interaction_type = Column(String, nullable=False)                  # Voice / SMS / Chat / Email
    interaction_time = Column(DateTime, nullable=False)
    conversation_text = Column(String, nullable=False)
    agent_id = Column(String, nullable=True)                          # Collector identifier
    sentiment_score = Column(Float, nullable=True)                    # -1.0 to 1.0
    interaction_outcome = Column(String, nullable=False)              # Promise to Pay / Refusal / etc.

    def __repr__(self):
        return f"<Interaction {self.interaction_id} - Customer {self.customer_id}>"