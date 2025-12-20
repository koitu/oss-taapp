"""Unit tests for DiscordClient HTTP methods with mocked responses."""

import pytest
import respx
from httpx import Response
from respx import MockRouter

from discord_chat_impl.discord_impl import (
    DiscordClient,
    MessageDeleteError,
    MessageNotFoundError,
    MessageSendError,
)

# Test constants
MIN_STATE_LENGTH = 10  # Minimum length for OAuth2 state parameter
DISCORD_TOKEN_EXPIRES_IN = 604800  # Discord token expiration time in seconds (7 days)
EXPECTED_MESSAGE_COUNT = 2  # Expected number of messages in test responses
EXPECTED_CHANNEL_COUNT = 2  # Expected number of channels in test responses


@pytest.fixture
def discord_client() -> DiscordClient:
    """Create a DiscordClient with test credentials."""
    return DiscordClient(
        client_id="test_client_id",
        client_secret="test_client_secret",
        redirect_uri="http://localhost:8000/callback",
        access_token="test_access_token",
    )


@pytest.fixture
def auth_client() -> DiscordClient:
    """Create a DiscordClient without access token for OAuth tests."""
    return DiscordClient(
        client_id="test_client_id",
        client_secret="test_client_secret",
        redirect_uri="http://localhost:8000/callback",
    )


class TestMessageOperations:
    """Tests for Discord message operations."""

    @respx.mock
    def test_get_messages_success(self, discord_client: DiscordClient) -> None:
        """Test getting messages from a channel."""
        mock_messages = [
            {
                "id": "123456",
                "channel_id": "789",
                "author": {"id": "111", "username": "TestUser"},
                "content": "Test message 1",
                "timestamp": "2025-01-01T00:00:00+00:00",
            },
            {
                "id": "123457",
                "channel_id": "789",
                "author": {"id": "222", "username": "AnotherUser"},
                "content": "Test message 2",
                "timestamp": "2025-01-01T00:01:00+00:00",
            },
        ]

        respx.get("https://discord.com/api/v10/channels/789/messages").mock(
            return_value=Response(200, json=mock_messages)
        )

        messages = discord_client.get_messages(channel_id="789", limit=10)

        assert len(messages) == EXPECTED_MESSAGE_COUNT
        assert messages[0].id == "123456"
        assert messages[0].content == "Test message 1"

    @respx.mock
    def test_get_messages_empty_channel(self, discord_client: DiscordClient) -> None:
        """Test getting messages from empty channel."""
        respx.get("https://discord.com/api/v10/channels/789/messages").mock(
            return_value=Response(200, json=[])
        )

        messages = discord_client.get_messages(channel_id="789")

        assert len(messages) == 0

    @respx.mock
    def test_get_message_by_id_success(self, discord_client: DiscordClient) -> None:
        """Test getting a specific message by ID."""
        mock_message = {
            "id": "123456",
            "channel_id": "789",
            "author": {"id": "111", "username": "TestUser"},
            "content": "Specific test message",
            "timestamp": "2025-01-01T00:00:00+00:00",
        }

        respx.get("https://discord.com/api/v10/channels/789/messages/123456").mock(
            return_value=Response(200, json=mock_message)
        )

        message = discord_client.get_message(channel_id="789", message_id="123456")

        assert message.id == "123456"
        assert message.content == "Specific test message"

    @respx.mock
    def test_send_message_success(self, discord_client: DiscordClient) -> None:
        """Test sending a message to a channel."""
        mock_response = {
            "id": "999",
            "channel_id": "789",
            "author": {"id": "111", "username": "BotUser"},
            "content": "Hello Discord!",
            "timestamp": "2025-01-01T00:00:00+00:00",
        }

        respx.post("https://discord.com/api/v10/channels/789/messages").mock(
            return_value=Response(200, json=mock_response)
        )

        result = discord_client.send_message(channel_id="789", content="Hello Discord!")

        assert result is True

    @respx.mock
    def test_send_message_failure(self, discord_client: DiscordClient) -> None:
        """Test sending message with error."""
        respx.post("https://discord.com/api/v10/channels/789/messages").mock(
            return_value=Response(403, json={"message": "Missing Access"})
        )

        with pytest.raises(MessageSendError, match="Failed to send message"):
            discord_client.send_message(channel_id="789", content="Test")

    @respx.mock
    def test_delete_message_success(self, discord_client: DiscordClient) -> None:
        """Test deleting a message."""
        respx.delete("https://discord.com/api/v10/channels/789/messages/123").mock(
            return_value=Response(204)
        )

        result = discord_client.delete_message(channel_id="789", message_id="123")

        assert result is True

    @respx.mock
    def test_delete_message_not_found(self, discord_client: DiscordClient) -> None:
        """Test deleting non-existent message raises MessageNotFoundError."""
        respx.delete("https://discord.com/api/v10/channels/789/messages/999").mock(
            return_value=Response(404, json={"message": "Unknown Message"})
        )

        with pytest.raises(MessageNotFoundError, match="Message 999 not found"):
            discord_client.delete_message(channel_id="789", message_id="999")


class TestErrorHandling:
    """Tests for error handling and edge cases."""

    @respx.mock
    def test_rate_limit_handling(self, discord_client: DiscordClient) -> None:
        """Test handling of 429 Rate Limit."""
        respx.get("https://discord.com/api/v10/channels/789/messages").mock(
            return_value=Response(429, json={"message": "Rate limited"})
        )

        with pytest.raises(ValueError, match="Failed to retrieve messages"):
            list(discord_client.get_messages(channel_id="789"))

    def test_get_message_http_error(
        self, discord_client: DiscordClient, respx_mock: MockRouter
    ) -> None:
        """Test get_message with HTTP error."""
        respx_mock.get("https://discord.com/api/v10/channels/ch1/messages/msg999").mock(
            return_value=Response(500, json={"message": "Internal Server Error"})
        )

        with pytest.raises(MessageNotFoundError, match="Failed to retrieve message"):
            discord_client.get_message(channel_id="ch1", message_id="msg999")

    def test_send_message_http_error(
        self, discord_client: DiscordClient, respx_mock: MockRouter
    ) -> None:
        """Test send_message with HTTP error."""
        respx_mock.post("https://discord.com/api/v10/channels/ch1/messages").mock(
            return_value=Response(500, json={"message": "Internal Server Error"})
        )

        with pytest.raises(MessageSendError, match="Failed to send message"):
            discord_client.send_message(channel_id="ch1", content="Test")

    def test_delete_message_http_error(
        self, discord_client: DiscordClient, respx_mock: MockRouter
    ) -> None:
        """Test delete_message with HTTP error raises exception."""
        respx_mock.delete("https://discord.com/api/v10/channels/ch1/messages/msg1").mock(
            return_value=Response(500, json={"message": "Internal Server Error"})
        )

        with pytest.raises(MessageDeleteError, match="Failed to delete message"):
            discord_client.delete_message(channel_id="ch1", message_id="msg1")
