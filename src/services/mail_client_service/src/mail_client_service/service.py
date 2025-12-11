"""Mail client and application initialization.

This module provides a centralized client instance that can be used by both FastAPI and MCP servers
"""

import logging
import sys
import typing
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastmcp import FastMCP

import gmail_client_impl  # noqa: F401 - Register implementation
import mail_client_api

# Add shared_telemetry to path if not already available
try:
    from shared_telemetry import add_telemetry_middleware
except ImportError:
    # Add src directory to path for local development
    src_path = Path(__file__).parent.parent.parent.parent.parent
    sys.path.insert(0, str(src_path))
    from shared_telemetry import add_telemetry_middleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global client instance (initialized lazily)
_client_instance: mail_client_api.Client | None = None


def get_mail_client() -> mail_client_api.Client:
    """Get or create the mail client instance.

    This function provides lazy initialization of the mail client.
    The client is created once on first access and reused for all
    subsequent calls.

    Returns:
        mail_client_api.Client: The mail client instance.

    Raises:
        RuntimeError: If client initialization fails.

    """
    global _client_instance  # noqa: PLW0603
    if _client_instance is None:
        try:
            _client_instance = mail_client_api.get_client(interactive=False)
            logger.info("Mail client initialized successfully")
        except Exception as e:
            logger.exception("Failed to initialize mail client")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Mail client initialization failed: {e!s}",
            ) from e
    return _client_instance


# Lifespan management
@asynccontextmanager
async def app_lifespan() -> typing.AsyncIterator[None]:
    """FastAPI application lifespan."""
    # Startup
    logger.info("Starting up the app...")
    # Initialize database, cache, etc.
    yield
    # Shutdown
    logger.info("Shutting down the app...")


# Create MCP application
mcp = FastMCP("Mail Client MCP Server")
mcp_app = mcp.http_app(path="/")


@asynccontextmanager
async def combined_lifespan(app: FastAPI) -> typing.AsyncIterator[None]:
    """Combine lifespan for both FastAPI and MCP."""
    async with app_lifespan(), mcp_app.lifespan(app):
        yield


# Create FastAPI application
app = FastAPI(
    title="Mail Client Service",
    description="RESTful API for email operations using Gmail",
    version="0.1.0",
    lifespan=combined_lifespan,
)

# Add telemetry middleware
add_telemetry_middleware(app, service_name="mail-service")
logger.info("Telemetry middleware added to Mail service")

app.mount("/mcp/", mcp_app)
