"""Integration tests for service call functionality using dependency overrides.

This suite verifies that the FastAPI `mail_client_service` endpoints are correctly
wired to the adapter and backend client. The backend client is mocked with
a `MagicMock` to isolate tests from external Gmail API calls.
"""

import unittest
from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from mail_client_service.api import app, get_mail_client

from src.mail_client_api.src.mail_client_api import Message


class TestServiceCallIntegration(unittest.TestCase):
    """Test end-to-end service call using FastAPI TestClient and mocked backend."""

    mock_client: MagicMock
    client: TestClient

    @classmethod
    def setUpClass(cls) -> None:
        """Set up dependency overrides for the FastAPI app."""
        cls.mock_client = MagicMock()
        app.dependency_overrides[get_mail_client] = lambda: cls.mock_client
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls) -> None:
        """Clear dependency overrides after tests."""
        app.dependency_overrides.clear()

    def setUp(self) -> None:
        """Reset mock state before each test."""
        self.mock_client.reset_mock()

    def test_get_messages_end_to_end(self) -> None:
        """Verify /messages returns mocked data."""
        # Arrange
        mock_message = MagicMock(spec=Message)
        mock_message.id = "msg1"
        mock_message.subject = "Test Subject"
        mock_message.from_ = "sender@example.com"
        mock_message.date = "2025-10-03"
        self.mock_client.get_messages.return_value = [mock_message]

        # Act
        response = self.client.get("/messages?max_results=5")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "messages" in data
        assert data["count"] == 1

        # Access by ID
        assert "msg1" in data["messages"]
        msg = data["messages"]["msg1"]
        assert msg["subject"] == "Test Subject"
        assert msg["from"] == "sender@example.com"
        assert msg["date"] == "2025-10-03"

        self.mock_client.get_messages.assert_called_once_with(max_results=5)


    def test_get_message_end_to_end(self) -> None:
        """Verify /messages/{id} returns mocked message detail."""
        # Arrange
        mock_message = MagicMock(spec=Message)
        mock_message.id = "msg2"
        mock_message.subject = "Detailed Subject"
        mock_message.from_ = "sender@example.com"
        mock_message.date = "2025-10-04"
        mock_message.body = "This is the message body."
        self.mock_client.get_message.return_value = mock_message

        # Act
        response = self.client.get("/messages/msg2")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "msg2"
        assert data["body"] == "This is the message body."
        self.mock_client.get_message.assert_called_once_with("msg2")

    def test_mark_as_read_end_to_end(self) -> None:
        """Verify /messages/{id}/mark-as-read returns success."""
        # Arrange
        self.mock_client.mark_as_read.return_value = True

        # Act
        response = self.client.post("/messages/msg3/mark-as-read")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "marked as read" in data["message"]
        self.mock_client.mark_as_read.assert_called_once_with("msg3")


    def test_delete_message_end_to_end(self) -> None:
        """Verify DELETE /messages/{id} returns success."""
        # Arrange
        self.mock_client.delete_message.return_value = True

        # Act
        response = self.client.delete("/messages/msg4")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "deleted successfully" in data["message"]


if __name__ == "__main__":
    unittest.main()
