"""Integration tests for AI + Ticket combined.

These tests verify that the AI service can generate structured responses
that are then used to perform ticket operations via the Ticket interface.
"""

import os
from typing import Any
from unittest.mock import MagicMock

import pytest
from tickets_api import Ticket, TicketInterface, TicketStatus

from ai_api import AIInterface

pytestmark = pytest.mark.integration


@pytest.fixture(params=["openai", "claude"])
def ai_service(request: pytest.FixtureRequest) -> AIInterface:
    """Fixture for AI service implementation (parametrized for OpenAI and Claude)."""
    if request.param == "openai":
        from openai_client_service.ai_interface_impl import EnvAIImplementation as OpenAIClient

        if "OPENAI_API_KEY" not in os.environ:
            pytest.skip("Missing OPENAI_API_KEY")

        return OpenAIClient()

    if request.param == "claude":
        from claude_client_service.ai_interface_impl import EnvAIImplementation as ClaudeClient

        if "CLAUDE_API_KEY" not in os.environ:
            pytest.skip("Missing CLAUDE_API_KEY")

        return ClaudeClient()

    pytest.skip(f"Invalid Parameter {request.param}")
    return AIInterface()


@pytest.fixture
def mock_ticket_service() -> MagicMock:
    """Fixture providing a mocked TicketInterface.

    This creates a mock that implements the TicketInterface contract
    without importing any concrete ticket implementation.
    """
    # Create mock that satisfies TicketInterface
    mock_ticket: MagicMock = MagicMock(spec=TicketInterface)

    # Create a mock ticket object
    def _make_ticket(ticket_id: str, title: str, description: str, status: TicketStatus) -> MagicMock:
        mock_t = MagicMock(spec=Ticket)
        mock_t.id = ticket_id
        mock_t.title = title
        mock_t.description = description
        mock_t.status = status
        mock_t.assignee = None
        return mock_t

    # Setup create_ticket mock
    def create_ticket_side_effect(title: str, description: str, assignee: str | None = None) -> MagicMock:
        return _make_ticket("ticket_123", title, description, TicketStatus.OPEN)

    mock_ticket.create_ticket.side_effect = create_ticket_side_effect

    # Setup get_ticket mock
    mock_ticket.get_ticket.return_value = _make_ticket(
        "ticket_456", "Existing Ticket", "This is an existing ticket", TicketStatus.OPEN
    )

    # Setup search_tickets mock
    mock_ticket.search_tickets.return_value = [
        _make_ticket("ticket_1", "Bug in login", "Users can't log in", TicketStatus.OPEN),
        _make_ticket("ticket_2", "Feature request", "Add dark mode", TicketStatus.IN_PROGRESS),
    ]

    # Setup update_ticket mock
    def update_ticket_side_effect(
        ticket_id: str,
        status: TicketStatus | None = None,
        title: str | None = None,
    ) -> MagicMock:
        new_status = status if status else TicketStatus.OPEN
        new_title = title if title else "Updated Ticket"
        return _make_ticket(ticket_id, new_title, "Updated description", new_status)

    mock_ticket.update_ticket.side_effect = update_ticket_side_effect

    # Setup delete_ticket mock
    mock_ticket.delete_ticket.return_value = True

    return mock_ticket


@pytest.mark.circleci
def test_ai_creates_ticket_from_user_request(ai_service: AIInterface, mock_ticket_service: MagicMock) -> None:
    """Test AI service parsing user input and creating a ticket via mocked ticket service."""
    # User request in natural language
    user_request = "Create a ticket for fixing the login bug on the homepage"

    # Define schema for ticket creation
    ticket_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["create_ticket", "list_tickets", "get_ticket", "update_ticket", "close_ticket"],
            },
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": ["string", "null"]},
                    "description": {"type": ["string", "null"]},
                    "ticket_id": {"type": ["string", "null"]},
                    "status": {"type": ["string", "null"], "enum": ["open", "in_progress", "closed", None]},
                },
                "required": ["title", "description", "ticket_id", "status"],
                "additionalProperties": False,
            },
        },
        "required": ["action", "parameters"],
        "additionalProperties": False,
    }

    # Generate AI response
    ai_response: str | dict[str, Any] = ai_service.generate_response(
        user_input=user_request,
        system_prompt=(
            "You are a helpful assistant that manages work tickets. "
            "Parse user requests and return structured ticket actions. "
            "For 'create a ticket' requests, return action='create_ticket' with title and description. "
            "Extract a clear title and description from the user's request."
        ),
        response_schema=ticket_schema,
    )

    # Verify AI returned structured response
    assert isinstance(ai_response, dict), "AI should return structured dict"
    assert ai_response["action"] == "create_ticket"
    assert "title" in ai_response["parameters"]
    assert "description" in ai_response["parameters"]

    # Extract parameters and create ticket via mocked service
    params = ai_response["parameters"]
    title = params["title"] or "Untitled"
    description = params["description"] or ""

    created_ticket = mock_ticket_service.create_ticket(title, description)

    # Verify ticket was created correctly
    assert created_ticket.id == "ticket_123"
    assert len(created_ticket.title) > 0
    assert created_ticket.status == TicketStatus.OPEN
    mock_ticket_service.create_ticket.assert_called_once_with(title, description)


@pytest.mark.circleci
def test_ai_lists_tickets_from_user_request(ai_service: AIInterface, mock_ticket_service: MagicMock) -> None:
    """Test AI service parsing list tickets request and calling mocked ticket service."""
    user_request = "Show me all open tickets"

    ticket_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["create_ticket", "list_tickets", "get_ticket", "update_ticket", "close_ticket"],
            },
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": ["string", "null"]},
                    "description": {"type": ["string", "null"]},
                    "ticket_id": {"type": ["string", "null"]},
                    "status": {"type": ["string", "null"], "enum": ["open", "in_progress", "closed", None]},
                },
                "required": ["title", "description", "ticket_id", "status"],
                "additionalProperties": False,
            },
        },
        "required": ["action", "parameters"],
        "additionalProperties": False,
    }

    ai_response: str | dict[str, Any] = ai_service.generate_response(
        user_input=user_request,
        system_prompt=(
            "You are a helpful assistant that manages work tickets. "
            "Parse user requests and return structured ticket actions. "
            "For 'show tickets' or 'list tickets' requests, return action='list_tickets' with optional status filter."
        ),
        response_schema=ticket_schema,
    )

    assert isinstance(ai_response, dict)
    assert ai_response["action"] == "list_tickets"

    # Call mocked ticket service to list tickets
    params = ai_response["parameters"]
    status_filter = params.get("status")

    if status_filter:
        status_enum = TicketStatus(status_filter)
        tickets = mock_ticket_service.search_tickets(status=status_enum)
    else:
        tickets = mock_ticket_service.search_tickets()

    assert len(tickets) == 2
    assert tickets[0].title == "Bug in login"
    assert tickets[1].title == "Feature request"


@pytest.mark.circleci
def test_ai_updates_ticket_status(ai_service: AIInterface, mock_ticket_service: MagicMock) -> None:
    """Test AI service parsing update ticket request and updating via mocked service."""
    user_request = "Mark ticket abc123 as in progress"

    ticket_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["create_ticket", "list_tickets", "get_ticket", "update_ticket", "close_ticket"],
            },
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": ["string", "null"]},
                    "description": {"type": ["string", "null"]},
                    "ticket_id": {"type": ["string", "null"]},
                    "status": {"type": ["string", "null"], "enum": ["open", "in_progress", "closed", None]},
                },
                "required": ["title", "description", "ticket_id", "status"],
                "additionalProperties": False,
            },
        },
        "required": ["action", "parameters"],
        "additionalProperties": False,
    }

    ai_response: str | dict[str, Any] = ai_service.generate_response(
        user_input=user_request,
        system_prompt=(
            "You are a helpful assistant that manages work tickets. "
            "Parse user requests and return structured ticket actions. "
            "For 'mark as' or 'update status' requests, return action='update_ticket' with ticket_id and status."
        ),
        response_schema=ticket_schema,
    )

    assert isinstance(ai_response, dict)
    assert ai_response["action"] == "update_ticket"

    params = ai_response["parameters"]
    ticket_id = params.get("ticket_id")
    status = params.get("status")

    assert ticket_id is not None
    assert status == "in_progress"

    # Update ticket via mocked service
    status_enum = TicketStatus(status)
    updated_ticket = mock_ticket_service.update_ticket(ticket_id, status=status_enum)

    assert updated_ticket.status == TicketStatus.IN_PROGRESS
    mock_ticket_service.update_ticket.assert_called_once_with(ticket_id, status=status_enum)


@pytest.mark.circleci
def test_ai_closes_ticket(ai_service: AIInterface, mock_ticket_service: MagicMock) -> None:
    """Test AI service parsing close ticket request and deleting via mocked service."""
    user_request = "Close ticket xyz789"

    ticket_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["create_ticket", "list_tickets", "get_ticket", "update_ticket", "close_ticket"],
            },
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": ["string", "null"]},
                    "description": {"type": ["string", "null"]},
                    "ticket_id": {"type": ["string", "null"]},
                    "status": {"type": ["string", "null"], "enum": ["open", "in_progress", "closed", None]},
                },
                "required": ["title", "description", "ticket_id", "status"],
                "additionalProperties": False,
            },
        },
        "required": ["action", "parameters"],
        "additionalProperties": False,
    }

    ai_response: str | dict[str, Any] = ai_service.generate_response(
        user_input=user_request,
        system_prompt=(
            "You are a helpful assistant that manages work tickets. "
            "Parse user requests and return structured ticket actions. "
            "For 'close ticket' requests, return action='close_ticket' with ticket_id."
        ),
        response_schema=ticket_schema,
    )

    assert isinstance(ai_response, dict)
    assert ai_response["action"] == "close_ticket"

    params = ai_response["parameters"]
    ticket_id = params.get("ticket_id")

    assert ticket_id is not None

    # Delete ticket via mocked service
    result = mock_ticket_service.delete_ticket(ticket_id)

    assert result is True
    mock_ticket_service.delete_ticket.assert_called_once_with(ticket_id)
