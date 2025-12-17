from unittest.mock import MagicMock

import pytest

from trello_ticket_impl.trello_ticket_impl import TrelloTicketClientImpl


@pytest.fixture
def mock_oauth_handler() -> MagicMock:
    return MagicMock()


@pytest.fixture
def client(monkeypatch) -> TrelloTicketClientImpl:
    monkeypatch.setenv("TRELLO_API_SECRET", "test_token")
    monkeypatch.setenv("TRELLO_API_KEY", "test_key")
    monkeypatch.setenv("TRELLO_BOARD_ID", "test_board_123")
    return TrelloTicketClientImpl(token="test_token", api_key="test_key", board_id="test_board_123")
