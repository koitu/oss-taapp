"""FastAPI application for OpenAI Client Service."""

import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI

from openai_client_impl import init_db  # type: ignore[attr-defined]

# Add shared_telemetry to path if not already available
try:
    from shared_telemetry import add_telemetry_middleware
except ImportError:
    # Add src directory to path for local development
    src_path = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(src_path))
    from shared_telemetry import add_telemetry_middleware

from .routes import ai, oauth

# Load .env from project root (4 levels up from this file)
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
env_path = project_root / ".env"
load_dotenv(env_path, override=False)
# Also try loading from current directory as fallback
load_dotenv(override=False)

app = FastAPI(
    title="OpenAI Client Service",
    description="A service for managing OpenAI API interactions with secure credential storage",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add telemetry middleware
add_telemetry_middleware(app, service_name="openai-service")


@app.on_event("startup")  # type: ignore[misc]
async def startup_event() -> None:
    """Initialize database on application startup."""
    init_db()

app.include_router(oauth.router, prefix="/auth", tags=["Authentication"])
app.include_router(ai.router, prefix="/ai", tags=["AI Operations"])


@app.get("/health")  # type: ignore[misc]
def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "service": "openai-client-service"}
