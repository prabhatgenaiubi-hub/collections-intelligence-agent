"""
Seed script to populate ChromaDB with:
1. Customer interaction summaries (from SQLite interaction history)
2. Collection policies and regulatory guidelines (from text file)

Run from backend folder:  python -m scripts.seed_vector_db
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.vector_db import (
    get_interaction_memory_collection,
    get_policy_knowledge_collection,
    reset_collection,
)
from app.rag.embeddings import generate_embeddings
from app.db.postgres import SessionLocal
from app.models.interaction_model import Interaction


def seed_interaction_memory():
    """
    Load interaction summaries from SQLite into ChromaDB.
    Each interaction's conversation_text becomes a searchable document.
    """
    print("  📝 Seeding interaction memory...")

    # Reset collection for clean seed
    collection = reset_collection("interaction_memory")

    # Fetch all interactions from SQLite
    db = SessionLocal()
    try:
        interactions = db.query(Interaction).all()
    finally:
        db.close()

    if not interactions:
        print("  ⚠️  No interactions found in database. Run seed_data.py first.")
        return

    # Prepare data for ChromaDB
    ids = []
    documents = []
    metadatas = []

    for interaction in interactions:
        ids.append(interaction.interaction_id)
        documents.append(interaction.conversation_text)
        metadatas.append({
            "customer_id": interaction.customer_id,
            "interaction_type": interaction.interaction_type,
            "interaction_outcome": interaction.interaction_outcome,
            "sentiment_score": interaction.sentiment_score or 0.0,
            "timestamp": interaction.interaction_time.isoformat(),
        })

    # Generate embeddings in batch
    embeddings = generate_embeddings(documents)

    # Add to ChromaDB
    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    print(f"  ✅ Interaction memory seeded: {len(ids)} documents")


def seed_policy_knowledge():
    """
    Load collection policies from text file into ChromaDB.
    Each policy block (separated by ---) becomes a searchable document.
    """
    print("  📜 Seeding policy knowledge...")

    # Reset collection for clean seed
    collection = reset_collection("policy_knowledge")

    # Read policy file
    policy_file = os.path.join(
        os.path.dirname(__file__), "..", "data", "collection_policies.txt"
    )

    if not os.path.exists(policy_file):
        print(f"  ⚠️  Policy file not found: {policy_file}")
        return

    with open(policy_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Split into individual policies
    policy_blocks = [block.strip() for block in content.split("---") if block.strip()]

    if not policy_blocks:
        print("  ⚠️  No policies found in file.")
        return

    # Prepare data
    ids = []
    documents = []
    metadatas = []

    for i, policy_text in enumerate(policy_blocks):
        # Detect category from prefix
        if policy_text.startswith("POLICY:"):
            category = "recovery_policy"
            doc_type = "policy"
        elif policy_text.startswith("REGULATION:"):
            category = "regulatory"
            doc_type = "regulation"
        elif policy_text.startswith("PROCEDURE:"):
            category = "procedure"
            doc_type = "procedure"
        elif policy_text.startswith("GUIDELINE:"):
            category = "guideline"
            doc_type = "guideline"
        else:
            category = "general"
            doc_type = "general"

        # Extract title (first line after prefix)
        first_line = policy_text.split("\n")[0]
        title = first_line.split(":", 1)[1].strip() if ":" in first_line else first_line

        ids.append(f"POL-{i+1:03d}")
        documents.append(policy_text)
        metadatas.append({
            "category": category,
            "document_type": doc_type,
            "title": title,
            "source": "collection_policies.txt",
        })

    # Generate embeddings in batch
    embeddings = generate_embeddings(documents)

    # Add to ChromaDB
    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    print(f"  ✅ Policy knowledge seeded: {len(ids)} documents")


def main():
    print("\n🧠 Seeding Vector Database (ChromaDB)...\n")
    seed_interaction_memory()
    seed_policy_knowledge()
    print("\n✅ Vector database seeded successfully!\n")


if __name__ == "__main__":
    main()