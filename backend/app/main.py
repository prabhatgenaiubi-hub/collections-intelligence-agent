"""
Collections Intelligence Agent — FastAPI Application Entry Point.
"""
from fastapi import FastAPI
from app.core.config import get_settings

# Import route modules
from app.api.routes import customer_routes, loan_routes, payment_routes, interaction_routes, analytics_routes, rag_routes, reasoning_routes, workflow_routes
settings = get_settings()

app = FastAPI(
    title="Collections Intelligence Agent",
    description=(
        "Pre-delinquency collections AI system.\n\n"
        "Analyzes loan & borrower data to predict repayment behavior "
        "and recommend recovery strategies with explainable AI reasoning."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# --- Register API Routes ---
app.include_router(customer_routes.router)
app.include_router(loan_routes.router)
app.include_router(payment_routes.router)
app.include_router(interaction_routes.router)
app.include_router(analytics_routes.router)
app.include_router(rag_routes.router)
app.include_router(reasoning_routes.router)
app.include_router(workflow_routes.router)


@app.on_event("startup")
async def on_startup():
    """Initialize database tables on application startup."""
    from app.db.postgres import init_db
    init_db()
    print("✅ Database tables initialized")


@app.get("/", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {
        "status": "running",
        "app": "Collections Intelligence Agent",
        "version": "1.0.0",
        "environment": settings.APP_ENV,
    }