"""Unit tests for FastAPI mail client service endpoints. This simulates a fake client using the FakeClient class written here and only tests the endpoints of the FastAPI app."""

import pytest
from fastapi.testclient import TestClient


class FakeEmail:
    """Fake email class for unit testing."""

    def __init__(self, id_: str, subject: str, from_: str, date: str, body: str ="") -> None:
        """Initialize a fake email."""
        self.id = id_
        self.subject = subject
        self.from_ = from_
        self.date = date
        self.body = body


class FakeClient:
    """Fake client class for unit testing."""

    def __init__(self) -> None:
        """Initialize a fake client."""
        self.messages = [
            FakeEmail("1", "Hello", "alice@example.com", "2025-10-01", body="Email body"),
            FakeEmail("2", "World", "bob@example.com", "2025-10-02", body="Another body"),
        ]

    def get_messages(self, max_results: int = 10) -> list[FakeEmail]:
        """Get a list of fake emails."""
        return self.messages[:max_results]

    def get_message(self, message_id: str) -> FakeEmail:
        """Get a fake email."""
        for msg in self.messages:
            if msg.id == message_id:
                return msg
        return (404, "Email not found")

    def mark_as_read(self, message_id: str) -> bool:
        """Mark a fake email as read."""
        for msg in self.messages:
            if msg.id == message_id:
                return True
        return False

    def delete_message(self, message_id: str) -> bool:
        """Delete a fake email."""
        for i, msg in enumerate(self.messages):
            if msg.id == message_id:
                del self.messages[i]
                return True
        return False


# Use the fake client
from src.services.mail_client_service import api

api.client = FakeClient()

client_app = TestClient(api.app)

# --- Tests ---
@pytest.mark.unit
def test_get_emails() -> None:
    """Test getting a list of emails."""
    response = client_app.get("/messages")
    assert response.status_code == 200
    data = response.json()
    assert "1" in data
    assert data["1"]["Subject"] == "Hello"
    assert data["2"]["From"] == "bob@example.com"

@pytest.mark.unit
def test_get_email_contents_success() -> None:
    """Test getting the contents of an email given an email ID."""
    response = client_app.get("/messages/1")
    assert response.status_code == 200
    data = response.json()
    assert data["ID"] == "1"
    assert data["Body"] == "Email body"

@pytest.mark.unit
def test_get_email_contents_not_found() -> None:
    """Test getting the contents of an email that doesn't exist."""
    response = client_app.get("/messages/999")
    assert response.status_code == 404

@pytest.mark.unit
def test_mark_email_read_success() -> None:
    """Test marking an email as read when it succeeds."""
    response = client_app.post("/messages/1/mark-as-read")
    assert response.status_code == 200
    assert response.json()["Status"] == "Success"

@pytest.mark.unit
def test_mark_email_read_fail() -> None:
    """Test marking an email as read when it fails."""
    response = client_app.post("/messages/999/mark-as-read")
    assert response.status_code == 404

@pytest.mark.unit
def test_delete_email_success() -> None:
    """Test deleting an email when it succeeds."""
    response = client_app.delete("/messages/1")
    assert response.status_code == 200
    assert response.json()["Status"] == "Success"

@pytest.mark.unit
def test_delete_email_fail() -> None:
    """Test deleting an email when it fails."""
    response = client_app.delete("/messages/999")
    assert response.status_code == 404
