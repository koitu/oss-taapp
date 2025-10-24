"""Unit tests for chat client API contract."""

import pytest

import chat_client_api


def test_api_exports_client() -> None:
    """Test that the API exports the Client class."""
    assert hasattr(chat_client_api, "Client")
    assert chat_client_api.Client is not None


def test_api_exports_chat_message() -> None:
    """Test that the API exports the ChatMessage class."""
    assert hasattr(chat_client_api, "ChatMessage")
    assert chat_client_api.ChatMessage is not None


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


def test_get_client_raises_not_implemented() -> None:
    """Test that get_client raises NotImplementedError when not overridden."""
    with pytest.raises(NotImplementedError):
        chat_client_api.get_client()


def test_get_message_raises_not_implemented() -> None:
    """Test that get_message raises NotImplementedError when not overridden."""
    with pytest.raises(NotImplementedError):
        chat_client_api.get_message("msg_id", {})


def test_get_channel_raises_not_implemented() -> None:
    """Test that get_channel raises NotImplementedError when not overridden."""
    with pytest.raises(NotImplementedError):
        chat_client_api.get_channel("channel_id", {})


def test_client_is_abstract() -> None:
    """Test that Client cannot be instantiated directly."""
    with pytest.raises(TypeError):
        chat_client_api.Client()  # type: ignore[abstract]


def test_chat_message_is_abstract() -> None:
    """Test that ChatMessage cannot be instantiated directly."""
    with pytest.raises(TypeError):
        chat_client_api.ChatMessage()  # type: ignore[abstract]


def test_channel_is_abstract() -> None:
    """Test that Channel cannot be instantiated directly."""
    with pytest.raises(TypeError):
        chat_client_api.Channel()  # type: ignore[abstract]
