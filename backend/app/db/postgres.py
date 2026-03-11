"""
Database connection and session management using SQLAlchemy.
Currently uses SQLite for local development.
To switch to PostgreSQL later, just change DATABASE_URL in .env file.
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import get_settings

settings = get_settings()

# Build engine — handle SQLite-specific settings
if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        settings.DATABASE_URL,
        echo=settings.APP_DEBUG,
        connect_args={"check_same_thread": False},  # Required for SQLite + FastAPI
    )

    # Enable foreign key enforcement in SQLite (off by default)
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
else:
    # PostgreSQL or other databases
    engine = create_engine(
        settings.DATABASE_URL,
        echo=settings.APP_DEBUG,
        pool_pre_ping=True,
    )

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Base class for all ORM models
Base = declarative_base()


def get_db():
    """
    FastAPI dependency that provides a database session.
    Usage:
        @app.get("/example")
        def example(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Create all tables defined by ORM models.
    Call this at application startup.
    """
    import app.models.customer_model      # noqa: F401
    import app.models.loan_model          # noqa: F401
    import app.models.payment_model       # noqa: F401
    import app.models.interaction_model   # noqa: F401

    Base.metadata.create_all(bind=engine)