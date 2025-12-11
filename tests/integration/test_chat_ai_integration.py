"""Integration tests for AI + Chat combined."""

import os
from typing import Any
from unittest.mock import MagicMock, PropertyMock

import pytest

from ai_api import AIInterface
from chat_client_api import ChatInterface, Message


def create_mock_message(message_id: str, content: str, sender_id: str) -> MagicMock:
    """Create a mocked Message object."""
    mock_message: MagicMock = MagicMock(spec=Message)
    type(mock_message).id = PropertyMock(return_value=message_id)
    type(mock_message).content = PropertyMock(return_value=content)
    type(mock_message).sender_id = PropertyMock(return_value=sender_id)
    return mock_message


@pytest.fixture
def ai_service() -> AIInterface:
    """Fixture for your AI service implementation."""
    from openai_client_service.ai_interface_impl import EnvAIImplementation

    required_env_vars = [
        "OPENAI_API_KEY",
    ]

    # If no useful env vars found, skip
    if all(v not in os.environ for v in required_env_vars):
        pytest.skip(f"No Discord credentials found in environment: {required_env_vars}")

    return EnvAIImplementation()


@pytest.fixture
def mock_chat_service() -> MagicMock:
    """Fixture providing a mocked ChatInterface.

    This creates a mock that implements the ChatInterface contract
    without importing any concrete chat implementation.
    """
    # Create mock that satisfies ChatInterface
    mock_chat: MagicMock = MagicMock(spec=ChatInterface)

    # Setup send_message mock
    mock_chat.send_message.return_value = True

    # Setup default get_messages mock
    default_message = create_mock_message(message_id="msg_123", content="What is the capital of France?", sender_id="user_456")
    mock_chat.get_messages.return_value = [default_message]

    # Setup delete_message mock
    mock_chat.delete_message.return_value = True

    return mock_chat


@pytest.fixture
def test_channel_id() -> str:
    """Fixture for test channel."""
    return "test_channel_001"


def test_ai_responds_to_mocked_chat_message(ai_service: AIInterface, mock_chat_service: MagicMock, test_channel_id: str) -> None:
    """Test AI service responding to a mocked chat message."""
    # Setup mock message
    user_question: str = "What is the capital of France?"
    mock_message = create_mock_message(message_id="msg_789", content=user_question, sender_id="user_001")
    mock_chat_service.get_messages.return_value = [mock_message]

    # Retrieve message from mocked chat
    messages: list[Message] = mock_chat_service.get_messages(channel_id=test_channel_id, limit=1)

    # Mock returned correct message
    assert len(messages) == 1
    assert messages[0].content == user_question
    assert messages[0].id == "msg_789"
    assert messages[0].sender_id == "user_001"

    # Generate AI response
    ai_response: str | dict[str, Any] = ai_service.generate_response(
        user_input=messages[0].content, system_prompt="You are a helpful geography assistant.", response_schema=None
    )

    # Verify AI response (from real implementation)
    assert isinstance(ai_response, str), "AI should return a string response"
    assert len(ai_response) > 0, "AI response should not be empty"
    assert "paris" in ai_response.lower(), "AI response should mention Paris"

    # Send AI response back to mocked chat
    send_result: bool = mock_chat_service.send_message(channel_id=test_channel_id, content=ai_response)

    # Verify message was sent to mock
    assert send_result is True
    mock_chat_service.send_message.assert_called_once_with(channel_id=test_channel_id, content=ai_response)


def test_ai_structured_response_with_mocked_chat(
    ai_service: AIInterface, mock_chat_service: MagicMock, test_channel_id: str
) -> None:
    """Test AI generating structured response from mocked chat message."""
    # Setup mock message with booking request
    booking_request: str = "Book a flight to Tokyo on December 25th"
    mock_message = create_mock_message(message_id="msg_booking_001", content=booking_request, sender_id="user_traveler")
    mock_chat_service.get_messages.return_value = [mock_message]

    # Get message from mock
    messages: list[Message] = mock_chat_service.get_messages(channel_id=test_channel_id, limit=1)

    # Generate structured AI response
    booking_schema: dict[str, Any] = {
        "type": "object",
        "properties": {"destination": {"type": "string"}, "date": {"type": "string"}, "action": {"type": "string"}},
        "required": ["destination", "date", "action"],
    }

    ai_response: str | dict[str, Any] = ai_service.generate_response(
        user_input=messages[0].content,
        system_prompt="Extract booking information from user requests.",
        response_schema=booking_schema,
    )

    # Verify structured response from real AI
    assert isinstance(ai_response, dict), "Should return structured dict"
    assert "destination" in ai_response
    assert "date" in ai_response
    assert "action" in ai_response
    assert "tokyo" in ai_response["destination"].lower()

    # Send confirmation to mocked chat
    confirmation: str = f"Booking confirmed: {ai_response['destination']} on {ai_response['date']}"
    mock_chat_service.send_message(channel_id=test_channel_id, content=confirmation)

    # Verify mock was called
    assert mock_chat_service.send_message.call_count == 1
