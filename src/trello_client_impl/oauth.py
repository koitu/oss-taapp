"""Top-level proxy oauth module for tests.

Placing a small stub module at `src/trello_client_impl/oauth.py` ensures
`from trello_client_impl.oauth import TrelloOAuthHandler` works when tests
run with `src` on `PYTHONPATH`.
"""
from __future__ import annotations

from typing import Optional


class TrelloOAuthHandler:
    """Minimal stub used only for tests.

    The real implementation lives under the package's `src` subfolder.
    """

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or ""

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"TrelloOAuthHandler(api_key={'***' if self.api_key else ''})"
