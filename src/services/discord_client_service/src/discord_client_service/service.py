"""FastAPI service for Discord chat operations with OAuth2 authentication.

This service provides HTTP endpoints for Discord operations and handles
the OAuth2 flow for user authentication.

"""

import logging
import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

# Database-backed credential storage has been removed in favor of
# an in-memory session-backed credential store implemented in
# `discord_client_service.auth_session`.
# Previously this module initialized the database on startup; that
# initialization is no longer needed.
from fastapi import FastAPI

# Add shared_telemetry to path if not already available
try:
    from shared_telemetry import add_telemetry_middleware
except ImportError:
    # Add src directory to path for local development
    src_path = Path(__file__).parent.parent.parent.parent.parent
    sys.path.insert(0, str(src_path))
    from shared_telemetry import add_telemetry_middleware

logger = logging.getLogger(__name__)

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    load_dotenv()
    logger.info("Loaded environment variables from .env file")
except ImportError:
    # If python-dotenv is not available, manually load .env file
    env_path = Path(".env")
    if env_path.exists():
        with env_path.open() as f:
            for raw_line in f:
                line = raw_line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key] = value
        logger.info("Manually loaded environment variables from .env file")
    else:
        logger.warning("No .env file found")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Manage application lifespan events.

    Initializes database on startup and cleans up on shutdown.

    Args:
        _app: FastAPI application instance (unused but required by FastAPI).

    Yields:
        None: Control during application runtime.

    """
    # Startup: nothing to initialize for DB (sessions are in-memory)
    logger.info("Initializing Discord service (no database)...")

    yield

    # Shutdown: nothing to close
    logger.info("Shutting down Discord service")
    logger.info("Service shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Discord Client Service",
    description="RESTful API for Discord chat operations with OAuth2 authentication",
    version="0.1.0",
    lifespan=lifespan,
)

# Add telemetry middleware
add_telemetry_middleware(app, service_name="discord-service")
logger.info("Telemetry middleware added to Discord service")


@app.get("/health")
def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        Dictionary with status information.

    """
    return {"status": "healthy", "service": "discord-client-service"}


@app.get("/openapi.json")
def get_openapi_schema() -> dict[str, Any]:
    """Serve the OpenAPI schema.

    Returns:
        The OpenAPI schema as a dictionary.

    """
    return app.openapi()
