"""Pytest fixtures for the trello_ticket_impl tests.

Provides a mocked oauth handler and a configured `TrelloTicketClientImpl`
that reads credentials from the test environment.
"""

from unittest.mock import MagicMock

import pytest

from trello_ticket_impl.trello_ticket_impl import TrelloTicketClientImpl


@pytest.fixture
def mock_oauth_handler() -> MagicMock:
    """Return a MagicMock to act as an oauth handler in tests."""
    return MagicMock()


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TrelloTicketClientImpl:
    """Provide a `TrelloTicketClientImpl` configured via environment vars.

    Uses `monkeypatch.setenv` so no credentials are hardcoded into the
    client instantiation.
    """
    monkeypatch.setenv("TRELLO_API_SECRET", "test_token")
    monkeypatch.setenv("TRELLO_API_KEY", "test_key")
    monkeypatch.setenv("TRELLO_BOARD_ID", "test_board_123")
    return TrelloTicketClientImpl()
