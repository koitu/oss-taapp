"""Unit tests for the mail_client_service FastAPI API.

This module uses a fake client implementation to test API routes
such as fetching, reading, marking as read, and deleting messages.
"""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from mail_client_service import service

from .test_fake_mail import FakeMailClient


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Fixture that provides a test client with a fake mail client override."""

    def override_get_mail_client() -> FakeMailClient:
        return FakeMailClient()

    service.app.dependency_overrides[service.get_mail_client] = override_get_mail_client
    test_client = TestClient(service.app)
    yield test_client
    service.app.dependency_overrides.clear()


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
