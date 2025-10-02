"""Unit tests for FastAPI mail client service endpoints.

This module tests the service endpoints using a fake client implementation
to avoid requiring actual Gmail API credentials during testing.
"""

import pytest
from fastapi.testclient import TestClient


class FakeMessage:
    """Fake message class for unit testing."""

    def __init__(
        self,
        id_: str,
        subject: str,
        from_: str,
        date: str,
        body: str = "",
    ) -> None:
        """Initialize a fake message.

        Args:
            id_: Message ID
            subject: Email subject
            from_: Sender email
            date: Message date
            body: Email body content

        """
        self.id = id_
        self.subject = subject
        self.from_ = from_
        self.date = date
        self.body = body


class FakeClient:
    """Fake client class for unit testing."""

    def __init__(self) -> None:
        """Initialize a fake client with sample messages."""
        self.messages = [
            FakeMessage(
                "1",
                "Hello",
                "alice@example.com",
                "2025-10-01",
                body="Email body",
            ),
            FakeMessage(
                "2",
                "World",
                "bob@example.com",
                "2025-10-02",
                body="Another body",
            ),
        ]

    def get_messages(self, max_results: int = 10) -> list[FakeMessage]:
        """Get a list of fake messages.

        Args:
            max_results: Maximum number of messages to return

        Returns:
            List of fake messages

        """
        return self.messages[:max_results]

    def get_message(self, message_id: str) -> FakeMessage:
        """Get a fake message by ID.

        Args:
            message_id: Message ID to retrieve

        Returns:
            Fake message object

        Raises:
            ValueError: If message not found

        """
        for msg in self.messages:
            if msg.id == message_id:
                return msg
        raise ValueError(f"Message {message_id} not found")

    def mark_as_read(self, message_id: str) -> bool:
        """Mark a fake message as read.

        Args:
            message_id: Message ID to mark as read

        Returns:
            True if successful, False otherwise

        """
        for msg in self.messages:
            if msg.id == message_id:
                return True
        return False

    def delete_message(self, message_id: str) -> bool:
        """Delete a fake message.

        Args:
            message_id: Message ID to delete

        Returns:
            True if successful, False otherwise

        """
        for i, msg in enumerate(self.messages):
            if msg.id == message_id:
                del self.messages[i]
                return True
        return False


# Import and mock the client
from mail_client_service import api


def override_get_mail_client() -> FakeClient:
    """Override dependency to return fake client."""
    return FakeClient()


# Override the dependency
api.app.dependency_overrides[api.get_mail_client] = override_get_mail_client

client_app = TestClient(api.app)


# --- Tests ---
@pytest.mark.unit
def test_get_messages_success() -> None:
    """Test getting a list of messages."""
    response = client_app.get("/messages")
    assert response.status_code == 200
    data = response.json()
    assert "messages" in data
    assert "count" in data
    assert data["count"] == 2
    assert "1" in data["messages"]
    assert data["messages"]["1"]["subject"] == "Hello"
    assert data["messages"]["2"]["from"] == "bob@example.com"


@pytest.mark.unit
def test_get_messages_with_max_results() -> None:
    """Test getting messages with custom max_results parameter."""
    response = client_app.get("/messages?max_results=1")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1


@pytest.mark.unit
def test_get_message_success() -> None:
    """Test getting the contents of a message by ID."""
    response = client_app.get("/messages/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "1"
    assert data["body"] == "Email body"
    assert data["subject"] == "Hello"


@pytest.mark.unit
def test_get_message_not_found() -> None:
    """Test getting a message that doesn't exist."""
    response = client_app.get("/messages/999")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


@pytest.mark.unit
def test_mark_as_read_success() -> None:
    """Test marking a message as read successfully."""
    response = client_app.post("/messages/1/mark-as-read")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "message" in data


@pytest.mark.unit
def test_mark_as_read_not_found() -> None:
    """Test marking a non-existent message as read."""
    response = client_app.post("/messages/999/mark-as-read")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


@pytest.mark.unit
def test_delete_message_success() -> None:
    """Test deleting a message successfully."""
    # Note: Each test gets a fresh FakeClient due to dependency override
    response = client_app.delete("/messages/1")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "message" in data


@pytest.mark.unit
def test_delete_message_not_found() -> None:
    """Test deleting a non-existent message."""
    response = client_app.delete("/messages/999")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


@pytest.mark.unit
def test_health_check() -> None:
    """Test the health check endpoint."""
    response = client_app.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
