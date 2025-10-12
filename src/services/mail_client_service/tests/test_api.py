"""Unit tests for the mail_client_service FastAPI API.

This module uses a fake client implementation to test API routes
such as fetching, reading, marking as read, and deleting messages.
"""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from mail_client_service import api


# --- Fake client setup ---
class FakeMessage:
    """Represents a simplified email message for testing."""

    def __init__(self, id_: str, subject: str, from_: str, date: str, body: str = "") -> None:
        """Initialize a fake message.

        Args:
            id_: Unique identifier for the message.
            subject: Email subject.
            from_: Sender email address.
            date: Date string.
            body: Message body content.

        """
        self.id = id_
        self.subject = subject
        self.from_ = from_
        self.date = date
        self.body = body


class FakeClient:
    """Fake client implementation to simulate mail client behavior."""

    def __init__(self) -> None:
        """Initialize the fake client with a predefined list of messages."""
        self.messages = [
            FakeMessage("1", "Hello", "alice@example.com", "2025-10-01", body="Email body"),
            FakeMessage("2", "World", "bob@example.com", "2025-10-02", body="Another body"),
        ]

    def get_messages(self, max_results: int = 10) -> list[FakeMessage]:
        """Return up to `max_results` messages."""
        return self.messages[:max_results]

    def get_message(self, message_id: str) -> FakeMessage:
        """Return a message by ID or raise ValueError if not found."""
        for msg in self.messages:
            if msg.id == message_id:
                return msg
        raise ValueError(f"Message {message_id} not found")

    def mark_as_read(self, message_id: str) -> bool:
        """Mark a message as read if it exists."""
        return any(msg.id == message_id for msg in self.messages)

    def delete_message(self, message_id: str) -> bool:
        """Delete a message by ID, returning True if found and deleted."""
        for i, msg in enumerate(self.messages):
            if msg.id == message_id:
                del self.messages[i]
                return True
        return False


# --- Pytest fixture for isolated overrides ---
@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Fixture that provides a test client with a fake mail client override."""

    def override_get_mail_client() -> FakeClient:
        return FakeClient()

    api.app.dependency_overrides[api.get_mail_client] = override_get_mail_client
    test_client = TestClient(api.app)
    yield test_client
    api.app.dependency_overrides.clear()


# --- Tests ---
@pytest.mark.unit
def test_get_messages_success(client: TestClient) -> None:
    """Test retrieving all messages returns expected results."""
    response = client.get("/messages")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2
    assert data["messages"]["1"]["subject"] == "Hello"
    assert data["messages"]["2"]["from"] == "bob@example.com"


@pytest.mark.unit
def test_get_messages_with_max_results(client: TestClient) -> None:
    """Test retrieving messages with max_results parameter works correctly."""
    response = client.get("/messages?max_results=1")
    assert response.status_code == 200
    assert response.json()["count"] == 1


@pytest.mark.unit
def test_get_message_success(client: TestClient) -> None:
    """Test retrieving a single message by ID succeeds."""
    response = client.get("/messages/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "1"
    assert data["body"] == "Email body"


@pytest.mark.unit
def test_get_message_not_found(client: TestClient) -> None:
    """Test retrieving a non-existent message returns 404."""
    response = client.get("/messages/999")
    assert response.status_code == 404
    assert "detail" in response.json()


@pytest.mark.unit
def test_mark_as_read_success(client: TestClient) -> None:
    """Test marking a message as read succeeds."""
    response = client.post("/messages/1/mark-as-read")
    assert response.status_code == 200
    assert response.json()["status"] == "success"


@pytest.mark.unit
def test_mark_as_read_not_found(client: TestClient) -> None:
    """Test marking a non-existent message as read returns 404."""
    response = client.post("/messages/999/mark-as-read")
    assert response.status_code == 404


@pytest.mark.unit
def test_delete_message_success(client: TestClient) -> None:
    """Test deleting a message by ID succeeds."""
    response = client.delete("/messages/1")
    assert response.status_code == 200
    assert response.json()["status"] == "success"


@pytest.mark.unit
def test_delete_message_not_found(client: TestClient) -> None:
    """Test deleting a non-existent message returns 404."""
    response = client.delete("/messages/999")
    assert response.status_code == 404


@pytest.mark.unit
def test_health_check(client: TestClient) -> None:
    """Test the health check endpoint returns healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
