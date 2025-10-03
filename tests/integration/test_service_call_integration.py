"""
Integration tests for service call functionality using dependency overrides.

This module verifies that the FastAPI `mail_client_service` endpoints are correctly
wired to the adapter and backend client. The backend client is mocked with
a `MagicMock` to isolate tests from external Gmail API calls.
"""

import logging
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from mail_client_service.api import app, get_mail_client
from src.mail_client_api.src.mail_client_api import Message

# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration

logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def mock_client() -> MagicMock:
    """Provide a module-scoped MagicMock and override FastAPI dependency."""
    mock = MagicMock()
    app.dependency_overrides[get_mail_client] = lambda: mock
    yield mock
    app.dependency_overrides.clear()


@pytest.fixture(scope="module")
def client(mock_client: MagicMock) -> TestClient:
    """Provide a TestClient using the mocked backend."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_mock_before_each_test(mock_client: MagicMock):
    """Automatically reset mock before each test."""
    mock_client.reset_mock()


@pytest.mark.circleci
def test_get_messages_end_to_end(client: TestClient, mock_client: MagicMock) -> None:
    """Verify /messages returns mocked data."""
    mock_message = MagicMock(spec=Message)
    mock_message.id = "msg1"
    mock_message.subject = "Test Subject"
    mock_message.from_ = "sender@example.com"
    mock_message.date = "2025-10-03"
    mock_client.get_messages.return_value = [mock_message]

    response = client.get("/messages?max_results=5")
    assert response.status_code == 200

    data = response.json()
    assert "messages" in data
    assert data["count"] == 1
    assert "msg1" in data["messages"]
    msg = data["messages"]["msg1"]
    assert msg["subject"] == "Test Subject"
    assert msg["from"] == "sender@example.com"
    assert msg["date"] == "2025-10-03"

    mock_client.get_messages.assert_called_once_with(max_results=5)


@pytest.mark.circleci
def test_get_message_end_to_end(client: TestClient, mock_client: MagicMock) -> None:
    """Verify /messages/{id} returns mocked message detail."""
    mock_message = MagicMock(spec=Message)
    mock_message.id = "msg2"
    mock_message.subject = "Detailed Subject"
    mock_message.from_ = "sender@example.com"
    mock_message.date = "2025-10-04"
    mock_message.body = "This is the message body."
    mock_client.get_message.return_value = mock_message

    response = client.get("/messages/msg2")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "msg2"
    assert data["body"] == "This is the message body."
    mock_client.get_message.assert_called_once_with("msg2")


@pytest.mark.circleci
def test_mark_as_read_end_to_end(client: TestClient, mock_client: MagicMock) -> None:
    """Verify /messages/{id}/mark-as-read returns success."""
    mock_client.mark_as_read.return_value = True
    response = client.post("/messages/msg3/mark-as-read")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "success"
    assert "marked as read" in data["message"]
    mock_client.mark_as_read.assert_called_once_with("msg3")


@pytest.mark.circleci
def test_delete_message_end_to_end(client: TestClient, mock_client: MagicMock) -> None:
    """Verify DELETE /messages/{id} returns success."""
    mock_client.delete_message.return_value = True
    response = client.delete("/messages/msg4")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "success"
    assert "deleted successfully" in data["message"]
    mock_client.delete_message.assert_called_once_with("msg4")
