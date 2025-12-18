"""Unit tests for Discord message and channel implementations."""

from discord_chat_impl.message_impl import DiscordMessage


def test_discord_message_basic_properties() -> None:
    """Test basic Discord message properties."""
    raw_data = {
        "id": "123456789",
        "channel_id": "987654321",
        "content": "Hello, world!",
        "timestamp": "2025-01-15T10:30:00.000000+00:00",
        "edited_timestamp": None,
        "author": {
            "id": "111222333",
            "username": "testuser",
            "global_name": "Test User",
        },
    }

    message = DiscordMessage(raw_data)

    assert message.id == "123456789"
    assert message.channel_id == "987654321"
    assert message.sender_id == "111222333"
    assert message.sender_name == "Test User"
    assert message.content == "Hello, world!"
    assert message.timestamp == "2025-01-15T10:30:00.000000+00:00"
    assert message.edited_timestamp is None


def test_discord_message_edited() -> None:
    """Test Discord message with edit timestamp."""
    raw_data = {
        "id": "123",
        "channel_id": "456",
        "content": "Edited message",
        "timestamp": "2025-01-15T10:30:00.000000+00:00",
        "edited_timestamp": "2025-01-15T10:35:00.000000+00:00",
        "author": {
            "id": "789",
            "username": "editor",
        },
    }

    message = DiscordMessage(raw_data)

    assert message.edited_timestamp == "2025-01-15T10:35:00.000000+00:00"


def test_discord_message_author_fallback() -> None:
    """Test Discord message with username fallback (no global_name)."""
    raw_data = {
        "id": "123",
        "channel_id": "456",
        "content": "Test",
        "timestamp": "2025-01-15T10:30:00.000000+00:00",
        "edited_timestamp": None,
        "author": {
            "id": "789",
            "username": "fallback_user",
        },
    }

    message = DiscordMessage(raw_data)

    assert message.sender_name == "fallback_user"


def test_discord_message_missing_author() -> None:
    """Test Discord message with missing author data."""
    raw_data = {
        "id": "123",
        "channel_id": "456",
        "content": "Test",
        "timestamp": "2025-01-15T10:30:00.000000+00:00",
    }

    message = DiscordMessage(raw_data)

    assert message.sender_id == ""
    assert message.sender_name == "Unknown"
