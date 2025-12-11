"""Unit tests for chat client API contract."""

import chat_client_api


def test_api_exports_client() -> None:
    """Test that the API exports the Client class."""
    assert hasattr(chat_client_api, "ChatInterface")
    assert chat_client_api.ChatInterface is not None


def test_api_exports_chat_message() -> None:
    """Test that the API exports the Message class."""
    assert hasattr(chat_client_api, "Message")
    assert chat_client_api.Message is not None


def test_api_exports_channel() -> None:
    """Test that the API exports the Channel class."""
    assert hasattr(chat_client_api, "Channel")
    assert chat_client_api.Channel is not None


def test_api_exports_get_client() -> None:
    """Test that the API exports the get_client factory function."""
    assert hasattr(chat_client_api, "get_client")
    assert callable(chat_client_api.get_client)


def test_api_exports_get_message() -> None:
    """Test that the API exports the get_message factory function."""
    assert hasattr(chat_client_api, "get_message")
    assert callable(chat_client_api.get_message)


def test_api_exports_get_channel() -> None:
    """Test that the API exports the get_channel factory function."""
    assert hasattr(chat_client_api, "get_channel")
    assert callable(chat_client_api.get_channel)


# Note: The following tests were removed because Discord client implementation
# auto-registers itself on import, so both the factory functions and class now return
# Discord implementations instead of raising NotImplementedError.
# These tests are no longer applicable with the Discord implementation active.
