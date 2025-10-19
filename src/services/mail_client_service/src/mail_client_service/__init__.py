"""Mail Client Service - FastAPI wrapper for mail client operations."""

from .api import app
from .mcp import mcp as _  # noqa: F401

__all__ = ["app"]
