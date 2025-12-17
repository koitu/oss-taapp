"""Minimal OAuth handler stub for Trello client implementation.

This provides a lightweight `TrelloOAuthHandler` so tests can import and
create MagicMocks against it. The real implementation lives elsewhere.
"""
from __future__ import annotations

from typing import Optional


class TrelloOAuthHandler:
    """Simple stub representing Trello OAuth handler.

    Tests only rely on the presence of an `api_key` attribute, so keep this
    minimal and extend later if needed.
    """

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or ""

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"TrelloOAuthHandler(api_key={'***' if self.api_key else ''})"
