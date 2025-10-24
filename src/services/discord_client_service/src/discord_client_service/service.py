"""FastAPI service for Discord chat operations with OAuth2 authentication.

This service provides HTTP endpoints for Discord operations and handles
the OAuth2 flow for user authentication.

"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from discord_client_impl.database import get_credential_manager
from fastapi import FastAPI

logger = logging.getLogger(__name__)


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
