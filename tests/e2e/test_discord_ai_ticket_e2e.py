"""E2E tests for Discord → AI → Ticket flow.

These tests verify the complete workflow:
1. Discord receives a message
2. AI (OpenAI or Claude) parses the message
3. Ticket system performs the requested action

Tests both OpenAI and Claude AI providers.
"""

import os
from typing import Any
from unittest.mock import MagicMock, PropertyMock

import pytest
from chat_api import ChatInterface, Message

from ai_api import AIInterface
from tickets_api import Ticket, TicketInterface, TicketStatus

pytestmark = pytest.mark.e2e


def create_mock_message(message_id: str, content: str, sender_id: str) -> MagicMock:
    """Create a mocked Message object."""
    mock_message: MagicMock = MagicMock(spec=Message)
    type(mock_message).id = PropertyMock(return_value=message_id)
    type(mock_message).content = PropertyMock(return_value=content)
    type(mock_message).sender_id = PropertyMock(return_value=sender_id)
    return mock_message


def create_mock_ticket(ticket_id: str, title: str, description: str, status: TicketStatus) -> MagicMock:
    """Create a mocked Ticket object."""
    mock_ticket: MagicMock = MagicMock(spec=Ticket)
    type(mock_ticket).id = PropertyMock(return_value=ticket_id)
    type(mock_ticket).title = PropertyMock(return_value=title)
    type(mock_ticket).description = PropertyMock(return_value=description)
    type(mock_ticket).status = PropertyMock(return_value=status)
    type(mock_ticket).assignee = PropertyMock(return_value=None)
    return mock_ticket


@pytest.fixture
def mock_chat_service() -> MagicMock:
    """Fixture providing a mocked ChatInterface (simulates Discord)."""
    mock_chat: MagicMock = MagicMock(spec=ChatInterface)
    mock_chat.send_message.return_value = True
    mock_chat.delete_message.return_value = True

    # Default message
    default_message = create_mock_message(
        message_id="msg_123",
        content="/bot Create a ticket for fixing the login bug",
        sender_id="user_456",
    )
    mock_chat.get_messages.return_value = [default_message]

    return mock_chat


@pytest.fixture
def mock_ticket_service() -> MagicMock:
    """Fixture providing a mocked TicketInterface (simulates Trello)."""
    mock_ticket: MagicMock = MagicMock(spec=TicketInterface)

    # Setup create_ticket mock
    def create_ticket_side_effect(title: str, description: str, assignee: str | None = None) -> MagicMock:
        return create_mock_ticket("ticket_new_123", title, description, TicketStatus.OPEN)

    mock_ticket.create_ticket.side_effect = create_ticket_side_effect

    # Setup search_tickets mock
    mock_ticket.search_tickets.return_value = [
        create_mock_ticket("ticket_1", "Login Bug", "Users can't log in", TicketStatus.OPEN),
        create_mock_ticket("ticket_2", "Dark Mode", "Add dark mode feature", TicketStatus.IN_PROGRESS),
    ]

    # Setup update_ticket mock
    def update_ticket_side_effect(
        ticket_id: str,
        status: TicketStatus | None = None,
        title: str | None = None,
    ) -> MagicMock:
        new_status = status if status else TicketStatus.OPEN
        new_title = title if title else "Updated Ticket"
        return create_mock_ticket(ticket_id, new_title, "Updated description", new_status)

    mock_ticket.update_ticket.side_effect = update_ticket_side_effect

    # Setup delete_ticket mock
    mock_ticket.delete_ticket.return_value = True

    return mock_ticket


@pytest.fixture(params=["openai"])
def openai_service(request: pytest.FixtureRequest) -> AIInterface:
    """Fixture for OpenAI service."""
    from openai_client_service.ai_interface_impl import EnvAIImplementation as OpenAIClient

    if "OPENAI_API_KEY" not in os.environ:
        pytest.skip("Missing OPENAI_API_KEY")

    return OpenAIClient()


@pytest.fixture(params=["claude"])
def claude_service(request: pytest.FixtureRequest) -> AIInterface:
    """Fixture for Claude service."""
    from claude_client_service.ai_interface_impl import EnvAIImplementation as ClaudeClient

    if "CLAUDE_API_KEY" not in os.environ:
        pytest.skip("Missing CLAUDE_API_KEY")

    return ClaudeClient()


# Ticket schema used by the AI
TICKET_TOOLS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "action": {
            "type": "string",
            "enum": ["create_ticket", "list_tickets", "close_ticket", "update_ticket", "get_ticket", "chat_response"],
            "description": "The action to perform",
        },
        "parameters": {
            "type": "object",
            "description": "Parameters for the action",
            "properties": {
                "title": {"type": ["string", "null"], "description": "Ticket title/name"},
                "description": {"type": ["string", "null"], "description": "Ticket description"},
                "ticket_id": {"type": ["string", "null"], "description": "ID of the ticket"},
                "status": {
                    "type": ["string", "null"],
                    "enum": ["open", "in_progress", "closed", None],
                    "description": "Ticket status",
                },
                "limit": {"type": ["integer", "null"], "description": "Number of tickets to return"},
                "message": {"type": ["string", "null"], "description": "Chat response message"},
            },
            "required": ["title", "description", "ticket_id", "status", "limit", "message"],
            "additionalProperties": False,
        },
    },
    "required": ["action", "parameters"],
    "additionalProperties": False,
}

SYSTEM_PROMPT = """You are a helpful assistant that manages work tickets via natural language.

You have access to the following ticket operations:

1. **create_ticket**: Create a new ticket
   - Required: title
   - Optional: description

2. **list_tickets**: List recent tickets
   - Optional: limit, status

3. **update_ticket**: Update a ticket's title or status
   - Required: ticket_id
   - Optional: title, status

4. **close_ticket**: Close/archive a ticket
   - Required: ticket_id

5. **chat_response**: Just respond conversationally
   - Use this for greetings or general chat

When a user sends a message, analyze their intent and respond with:
- action: The operation to perform
- parameters: The extracted data

Always respond with valid JSON matching the schema."""


@pytest.mark.circleci
def test_discord_to_openai_create_ticket_e2e(
    openai_service: AIInterface,
    mock_chat_service: MagicMock,
    mock_ticket_service: MagicMock,
) -> None:
    """E2E: Discord → OpenAI → Create Ticket.

    Simulates the complete flow:
    1. User sends Discord message: '/bot Create a ticket for login bug'
    2. OpenAI parses the message and returns structured action
    3. Ticket service creates the ticket
    4. Response is sent back to Discord
    """
    channel_id = "test_channel_001"

    # Step 1: User sends message to Discord (already in mock)
    user_message = "/bot Create a ticket for fixing the login bug on the homepage"
    mock_message = create_mock_message("msg_create_001", user_message, "user_123")
    mock_chat_service.get_messages.return_value = [mock_message]

    # Step 2: Get message from Discord
    messages = mock_chat_service.get_messages(channel_id=channel_id, limit=1)
    assert len(messages) == 1
    assert messages[0].content == user_message

    # Step 3: AI parses the message
    chat_log = f"User: {messages[0].content}"
    ai_response: str | dict[str, Any] = openai_service.generate_response(
        user_input=chat_log,
        system_prompt=SYSTEM_PROMPT,
        response_schema=TICKET_TOOLS_SCHEMA,
    )

    # Step 4: Verify AI response is structured correctly
    assert isinstance(ai_response, dict), "OpenAI should return structured dict"
    assert ai_response["action"] == "create_ticket"
    assert ai_response["parameters"]["title"] is not None
    assert len(ai_response["parameters"]["title"]) > 0

    # Step 5: Create ticket via ticket service
    params = ai_response["parameters"]
    created_ticket = mock_ticket_service.create_ticket(
        params["title"] or "Untitled",
        params.get("description") or "",
    )

    # Step 6: Verify ticket was created
    assert created_ticket.id == "ticket_new_123"
    assert created_ticket.status == TicketStatus.OPEN
    mock_ticket_service.create_ticket.assert_called_once()

    # Step 7: Send confirmation to Discord
    confirmation_msg = f"✅ Created Ticket: {created_ticket.title} (ID: {created_ticket.id})"
    result = mock_chat_service.send_message(channel_id=channel_id, content=confirmation_msg)

    # Step 8: Verify message was sent
    assert result is True
    mock_chat_service.send_message.assert_called_once_with(channel_id=channel_id, content=confirmation_msg)


@pytest.mark.circleci
def test_discord_to_claude_create_ticket_e2e(
    claude_service: AIInterface,
    mock_chat_service: MagicMock,
    mock_ticket_service: MagicMock,
) -> None:
    """E2E: Discord → Claude → Create Ticket.

    Simulates the complete flow with Claude as the AI provider.
    """
    channel_id = "test_channel_002"

    # Step 1: User sends message to Discord
    user_message = "/bot Create a ticket for database performance issue"
    mock_message = create_mock_message("msg_create_002", user_message, "user_456")
    mock_chat_service.get_messages.return_value = [mock_message]

    # Step 2: Get message from Discord
    messages = mock_chat_service.get_messages(channel_id=channel_id, limit=1)
    assert len(messages) == 1

    # Step 3: Claude parses the message
    chat_log = f"User: {messages[0].content}"
    ai_response: str | dict[str, Any] = claude_service.generate_response(
        user_input=chat_log,
        system_prompt=SYSTEM_PROMPT,
        response_schema=TICKET_TOOLS_SCHEMA,
    )

    # Step 4: Verify Claude response
    assert isinstance(ai_response, dict), "Claude should return structured dict"
    assert ai_response["action"] == "create_ticket"
    assert ai_response["parameters"]["title"] is not None

    # Step 5: Create ticket
    params = ai_response["parameters"]
    created_ticket = mock_ticket_service.create_ticket(
        params["title"] or "Untitled",
        params.get("description") or "",
    )

    # Step 6: Verify and send confirmation
    assert created_ticket.status == TicketStatus.OPEN
    confirmation_msg = f"✅ Created Ticket: {created_ticket.title}"
    mock_chat_service.send_message(channel_id=channel_id, content=confirmation_msg)

    assert mock_ticket_service.create_ticket.call_count == 1
    assert mock_chat_service.send_message.call_count == 1


@pytest.mark.circleci
def test_discord_to_openai_list_tickets_e2e(
    openai_service: AIInterface,
    mock_chat_service: MagicMock,
    mock_ticket_service: MagicMock,
) -> None:
    """E2E: Discord → OpenAI → List Tickets."""
    channel_id = "test_channel_003"

    # User asks to list tickets
    user_message = "/bot Show me all open tickets"
    mock_message = create_mock_message("msg_list_001", user_message, "user_789")
    mock_chat_service.get_messages.return_value = [mock_message]

    # Get message and parse with OpenAI
    messages = mock_chat_service.get_messages(channel_id=channel_id, limit=1)
    chat_log = f"User: {messages[0].content}"

    ai_response: str | dict[str, Any] = openai_service.generate_response(
        user_input=chat_log,
        system_prompt=SYSTEM_PROMPT,
        response_schema=TICKET_TOOLS_SCHEMA,
    )

    # Verify AI wants to list tickets
    assert isinstance(ai_response, dict)
    assert ai_response["action"] == "list_tickets"

    # List tickets via ticket service
    params = ai_response["parameters"]
    status_filter = params.get("status")

    if status_filter:
        tickets = mock_ticket_service.search_tickets(status=TicketStatus(status_filter))
    else:
        tickets = mock_ticket_service.search_tickets()

    # Verify tickets retrieved
    assert len(tickets) == 2
    assert tickets[0].title == "Login Bug"

    # Send response to Discord
    ticket_list = "\n".join([f"- {t.title} ({t.status.value})" for t in tickets])
    response_msg = f"📋 Tickets:\n{ticket_list}"
    mock_chat_service.send_message(channel_id=channel_id, content=response_msg)

    assert mock_ticket_service.search_tickets.call_count == 1
    assert mock_chat_service.send_message.call_count == 1


@pytest.mark.circleci
def test_discord_to_claude_list_tickets_e2e(
    claude_service: AIInterface,
    mock_chat_service: MagicMock,
    mock_ticket_service: MagicMock,
) -> None:
    """E2E: Discord → Claude → List Tickets."""
    channel_id = "test_channel_004"

    # User asks to list tickets
    user_message = "/bot List all tickets"
    mock_message = create_mock_message("msg_list_002", user_message, "user_999")
    mock_chat_service.get_messages.return_value = [mock_message]

    messages = mock_chat_service.get_messages(channel_id=channel_id, limit=1)
    chat_log = f"User: {messages[0].content}"

    ai_response: str | dict[str, Any] = claude_service.generate_response(
        user_input=chat_log,
        system_prompt=SYSTEM_PROMPT,
        response_schema=TICKET_TOOLS_SCHEMA,
    )

    assert isinstance(ai_response, dict)
    assert ai_response["action"] == "list_tickets"

    tickets = mock_ticket_service.search_tickets()
    assert len(tickets) == 2

    mock_chat_service.send_message(channel_id=channel_id, content="Found 2 tickets")
    assert mock_chat_service.send_message.call_count == 1


@pytest.mark.circleci
def test_discord_to_openai_update_ticket_e2e(
    openai_service: AIInterface,
    mock_chat_service: MagicMock,
    mock_ticket_service: MagicMock,
) -> None:
    """E2E: Discord → OpenAI → Update Ticket Status."""
    channel_id = "test_channel_005"

    user_message = "/bot Mark ticket abc123 as in progress"
    mock_message = create_mock_message("msg_update_001", user_message, "user_555")
    mock_chat_service.get_messages.return_value = [mock_message]

    messages = mock_chat_service.get_messages(channel_id=channel_id, limit=1)
    chat_log = f"User: {messages[0].content}"

    ai_response: str | dict[str, Any] = openai_service.generate_response(
        user_input=chat_log,
        system_prompt=SYSTEM_PROMPT,
        response_schema=TICKET_TOOLS_SCHEMA,
    )

    assert isinstance(ai_response, dict)
    assert ai_response["action"] == "update_ticket"

    params = ai_response["parameters"]
    ticket_id = params.get("ticket_id")
    status = params.get("status")

    assert ticket_id is not None
    assert status in ["in_progress", "in progress", "in_progress"]

    # Normalize status
    normalized_status = status.lower().replace(" ", "_") if status else "open"
    status_enum = TicketStatus(normalized_status)

    updated_ticket = mock_ticket_service.update_ticket(ticket_id, status=status_enum)

    assert updated_ticket.status == TicketStatus.IN_PROGRESS
    mock_chat_service.send_message(channel_id=channel_id, content=f"✅ Updated ticket {ticket_id}")

    assert mock_ticket_service.update_ticket.call_count == 1


@pytest.mark.circleci
def test_discord_to_claude_close_ticket_e2e(
    claude_service: AIInterface,
    mock_chat_service: MagicMock,
    mock_ticket_service: MagicMock,
) -> None:
    """E2E: Discord → Claude → Close Ticket."""
    channel_id = "test_channel_006"

    user_message = "/bot Close ticket xyz789"
    mock_message = create_mock_message("msg_close_001", user_message, "user_777")
    mock_chat_service.get_messages.return_value = [mock_message]

    messages = mock_chat_service.get_messages(channel_id=channel_id, limit=1)
    chat_log = f"User: {messages[0].content}"

    ai_response: str | dict[str, Any] = claude_service.generate_response(
        user_input=chat_log,
        system_prompt=SYSTEM_PROMPT,
        response_schema=TICKET_TOOLS_SCHEMA,
    )

    assert isinstance(ai_response, dict)
    assert ai_response["action"] == "close_ticket"

    params = ai_response["parameters"]
    ticket_id = params.get("ticket_id")

    assert ticket_id is not None

    result = mock_ticket_service.delete_ticket(ticket_id)

    assert result is True
    mock_chat_service.send_message(channel_id=channel_id, content=f"✅ Closed ticket {ticket_id}")

    assert mock_ticket_service.delete_ticket.call_count == 1
