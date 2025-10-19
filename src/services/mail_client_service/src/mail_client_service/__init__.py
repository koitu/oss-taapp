"""Mail Client Service - FastAPI wrapper for mail client operations."""

from .api import app
from .mcp import mcp

__all__ = ["app", "mcp"]
