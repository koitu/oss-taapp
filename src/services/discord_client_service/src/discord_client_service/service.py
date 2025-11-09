"""FastAPI service for Discord chat operations with OAuth2 authentication.

This service provides HTTP endpoints for Discord operations and handles
the OAuth2 flow for user authentication.

"""

import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from discord_client_impl.database import get_credential_manager
from fastapi import FastAPI

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
    # Startup: Initialize database
    logger.info("Initializing Discord service...")
    manager = get_credential_manager()
    await manager.init_db()
    logger.info("Database initialized successfully")

    yield

    # Shutdown: Close database connections
    logger.info("Shutting down Discord service...")
    await manager.close()
    logger.info("Service shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Discord Client Service",
    description="RESTful API for Discord chat operations with OAuth2 authentication",
    version="0.1.0",
    lifespan=lifespan,
)


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
