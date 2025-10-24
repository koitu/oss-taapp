"""Unit tests for the forward_latest_email function in main.py."""

from unittest.mock import MagicMock, Mock, patch

import pytest


@pytest.mark.unit
def test_forward_latest_email_success() -> None:
    """Test successful forwarding of latest email."""
    # Arrange
    mock_client = Mock()
    mock_message = Mock()
    mock_message.id = "msg_123"
    mock_message.subject = "Test Email"
    mock_message.from_ = "sender@example.com"

    mock_client.get_messages.return_value = iter([mock_message])
    mock_client.forward_message.return_value = True

    # Mock the entire mail_client_api module before importing main
    with patch.dict("sys.modules", {"gmail_client_impl": MagicMock()}):
        with patch("mail_client_api.get_client", return_value=mock_client):
            from main import forward_latest_email

            # Act
            result = forward_latest_email("john.jakobsen@cuny.edu")

            # Assert
            assert result is True
            mock_client.get_messages.assert_called_once_with(max_results=1)
            mock_client.forward_message.assert_called_once_with("msg_123", "john.jakobsen@cuny.edu")


@pytest.mark.unit
def test_forward_latest_email_no_messages() -> None:
    """Test when there are no messages to forward."""
    # Arrange
    mock_client = Mock()
    mock_client.get_messages.return_value = iter([])  # Empty iterator

    with patch.dict("sys.modules", {"gmail_client_impl": MagicMock()}):
        with patch("mail_client_api.get_client", return_value=mock_client):
            from main import forward_latest_email

            # Act
            result = forward_latest_email("john.jakobsen@cuny.edu")

            # Assert
            assert result is False
            mock_client.get_messages.assert_called_once_with(max_results=1)
            mock_client.forward_message.assert_not_called()


@pytest.mark.unit
def test_forward_latest_email_forward_fails() -> None:
    """Test when forward operation fails."""
    # Arrange
    mock_client = Mock()
    mock_message = Mock()
    mock_message.id = "msg_123"
    mock_message.subject = "Test Email"
    mock_message.from_ = "sender@example.com"

    mock_client.get_messages.return_value = iter([mock_message])
    mock_client.forward_message.return_value = False  # Simulate failure

    with patch.dict("sys.modules", {"gmail_client_impl": MagicMock()}):
        with patch("mail_client_api.get_client", return_value=mock_client):
            from main import forward_latest_email

            # Act
            result = forward_latest_email("john.jakobsen@cuny.edu")

            # Assert
            assert result is False
            mock_client.forward_message.assert_called_once()


@pytest.mark.unit
def test_forward_latest_email_default_recipient() -> None:
    """Test that default recipient is john.jakobsen@cuny.edu."""
    # Arrange
    mock_client = Mock()
    mock_message = Mock()
    mock_message.id = "msg_123"
    mock_message.subject = "Test"
    mock_message.from_ = "sender@example.com"

    mock_client.get_messages.return_value = iter([mock_message])
    mock_client.forward_message.return_value = True

    with patch.dict("sys.modules", {"gmail_client_impl": MagicMock()}):
        with patch("mail_client_api.get_client", return_value=mock_client):
            from main import forward_latest_email

            # Act - call without arguments to use default
            result = forward_latest_email()

            # Assert
            assert result is True
            # Verify default email was used
            mock_client.forward_message.assert_called_once_with("msg_123", "john.jakobsen@cuny.edu")


@pytest.mark.unit
def test_forward_latest_email_custom_recipient() -> None:
    """Test forwarding to a custom recipient."""
    # Arrange
    mock_client = Mock()
    mock_message = Mock()
    mock_message.id = "msg_456"
    mock_message.subject = "Custom Test"
    mock_message.from_ = "another@example.com"

    mock_client.get_messages.return_value = iter([mock_message])
    mock_client.forward_message.return_value = True

    custom_email = "custom@example.org"

    with patch.dict("sys.modules", {"gmail_client_impl": MagicMock()}):
        with patch("mail_client_api.get_client", return_value=mock_client):
            from main import forward_latest_email

            # Act
            result = forward_latest_email(custom_email)

            # Assert
            assert result is True
            mock_client.forward_message.assert_called_once_with("msg_456", custom_email)
