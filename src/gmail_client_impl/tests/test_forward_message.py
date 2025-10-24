"""Unit tests for the forward_message functionality."""

from unittest.mock import Mock, patch

import pytest

from gmail_client_impl.gmail_impl import GmailClient


@pytest.mark.unit
def test_forward_message_success() -> None:
    """Test that forward_message successfully forwards a message."""
    # Arrange
    mock_service = Mock()
    mock_message_resource = Mock()
    mock_get = Mock()
    mock_send = Mock()

    # Setup the mock chain
    mock_service.users.return_value.messages.return_value = mock_message_resource
    mock_message_resource.get.return_value = mock_get
    mock_get.execute.return_value = {"raw": "base64_encoded_data"}
    mock_message_resource.send.return_value = mock_send
    mock_send.execute.return_value = {"id": "sent_message_id"}

    client = GmailClient(service=mock_service)

    # Mock the get_message call to return a message object
    mock_msg = Mock()
    mock_msg.from_ = "sender@example.com"
    mock_msg.to = "recipient@example.com"
    mock_msg.subject = "Test Subject"
    mock_msg.date = "2025-01-01"
    mock_msg.body = "Test email body"

    with patch.object(client, "get_message", return_value=mock_msg):
        # Act
        result = client.forward_message("msg_123", "john.jakobsen@cuny.edu")

    # Assert
    assert result is True
    mock_message_resource.get.assert_called_once()
    mock_message_resource.send.assert_called_once()


@pytest.mark.unit
def test_forward_message_no_raw_content() -> None:
    """Test that forward_message returns False when no raw content is found."""
    # Arrange
    mock_service = Mock()
    mock_message_resource = Mock()
    mock_get = Mock()

    mock_service.users.return_value.messages.return_value = mock_message_resource
    mock_message_resource.get.return_value = mock_get
    mock_get.execute.return_value = {}  # No 'raw' key

    client = GmailClient(service=mock_service)

    # Act
    result = client.forward_message("msg_123", "john.jakobsen@cuny.edu")

    # Assert
    assert result is False


@pytest.mark.unit
def test_forward_message_http_error() -> None:
    """Test that forward_message handles HttpError gracefully."""
    # Arrange
    from googleapiclient.errors import HttpError

    mock_service = Mock()
    mock_message_resource = Mock()

    mock_service.users.return_value.messages.return_value = mock_message_resource
    mock_message_resource.get.side_effect = HttpError(
        resp=Mock(status=404), content=b"Not found"
    )

    client = GmailClient(service=mock_service)

    # Act
    result = client.forward_message("msg_123", "john.jakobsen@cuny.edu")

    # Assert
    assert result is False


@pytest.mark.unit
def test_forward_message_creates_proper_format() -> None:
    """Test that the forwarded message has proper format."""
    # Arrange
    mock_service = Mock()
    mock_message_resource = Mock()
    mock_get = Mock()
    mock_send = Mock()

    mock_service.users.return_value.messages.return_value = mock_message_resource
    mock_message_resource.get.return_value = mock_get
    mock_get.execute.return_value = {"raw": "base64_encoded_data"}
    mock_message_resource.send.return_value = mock_send
    mock_send.execute.return_value = {"id": "sent_message_id"}

    client = GmailClient(service=mock_service)

    mock_msg = Mock()
    mock_msg.from_ = "sender@example.com"
    mock_msg.to = "recipient@example.com"
    mock_msg.subject = "Original Subject"
    mock_msg.date = "2025-01-01"
    mock_msg.body = "Original body"

    with patch.object(client, "get_message", return_value=mock_msg):
        # Act
        result = client.forward_message("msg_123", "john.jakobsen@cuny.edu")

    # Assert
    assert result is True

    # Verify the send was called with proper structure
    send_call_args = mock_message_resource.send.call_args
    assert send_call_args is not None
    assert "body" in send_call_args[1]
    assert "raw" in send_call_args[1]["body"]


@pytest.mark.unit
def test_forward_message_to_different_recipients() -> None:
    """Test forwarding to different email addresses."""
    # Arrange
    mock_service = Mock()
    mock_message_resource = Mock()
    mock_get = Mock()
    mock_send = Mock()

    mock_service.users.return_value.messages.return_value = mock_message_resource
    mock_message_resource.get.return_value = mock_get
    mock_get.execute.return_value = {"raw": "base64_encoded_data"}
    mock_message_resource.send.return_value = mock_send
    mock_send.execute.return_value = {"id": "sent_message_id"}

    client = GmailClient(service=mock_service)

    mock_msg = Mock()
    mock_msg.from_ = "sender@example.com"
    mock_msg.to = "recipient@example.com"
    mock_msg.subject = "Test"
    mock_msg.date = "2025-01-01"
    mock_msg.body = "Body"

    recipients = [
        "john.jakobsen@cuny.edu",
        "test@example.com",
        "another@domain.org",
    ]

    for recipient in recipients:
        with patch.object(client, "get_message", return_value=mock_msg):
            # Act
            result = client.forward_message("msg_123", recipient)

            # Assert
            assert result is True

    # Verify send was called for each recipient
    assert mock_message_resource.send.call_count == len(recipients)
