"""
API routes for Interaction History data.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.postgres import get_db
from app.models.interaction_model import Interaction
from app.schemas.interaction_schema import InteractionResponse, InteractionCreate

router = APIRouter(prefix="/interactions", tags=["Interactions"])


@router.get("/customer/{customer_id}", response_model=List[InteractionResponse])
def get_interactions_by_customer(customer_id: str, db: Session = Depends(get_db)):
    """Get all interactions for a specific customer (sorted by time desc)."""
    interactions = (
        db.query(Interaction)
        .filter(Interaction.customer_id == customer_id)
        .order_by(Interaction.interaction_time.desc())
        .all()
    )
    if not interactions:
        raise HTTPException(
            status_code=404,
            detail=f"No interactions found for customer {customer_id}",
        )
    return interactions


@router.get("/{interaction_id}", response_model=InteractionResponse)
def get_interaction(interaction_id: str, db: Session = Depends(get_db)):
    """Get a single interaction by ID."""
    interaction = (
        db.query(Interaction)
        .filter(Interaction.interaction_id == interaction_id)
        .first()
    )
    if not interaction:
        raise HTTPException(
            status_code=404, detail=f"Interaction {interaction_id} not found"
        )
    return interaction


@router.post("/", response_model=InteractionResponse, status_code=201)
def create_interaction(payload: InteractionCreate, db: Session = Depends(get_db)):
    """Record a new interaction."""
    existing = (
        db.query(Interaction)
        .filter(Interaction.interaction_id == payload.interaction_id)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Interaction {payload.interaction_id} already exists",
        )

    interaction = Interaction(**payload.model_dump())
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    return interaction