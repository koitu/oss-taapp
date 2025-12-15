"""Handlers for executing ticket operations against Trello."""

from typing import Any

from kanban_client_api.client import KanbanClient
from kanban_client_api.exceptions import (
    KanbanAuthenticationError,
    KanbanError,
    KanbanNotFoundError,
)


async def handle_create_ticket(
    client: KanbanClient,
    params: dict[str, Any],
    default_list_id: str,
) -> str:
    """Handle create_ticket action.

    Args:
        client: The Kanban client instance
        params: Parameters from AI tool call
        default_list_id: Default list ID to use if not specified

    Returns:
        Success message for the user

    """
    title = params["title"]
    description = params.get("description")
    list_id = params.get("list_id", default_list_id)

    try:
        card = await client.create_card(
            list_id=list_id,
            name=title,
            description=description,
        )
        msg = f"✅ Created ticket: **{card.name}**"
        if description:
            msg += f"\n📝 Description: {description}"
            msg += f"\n🆔 ID: `{card.id}`"
        else:
            msg += f"\n🆔 ID: `{card.id}`"
        return msg  # noqa: TRY300
    except KanbanAuthenticationError:
        return "❌ Authentication failed. Please check Trello credentials."
    except KanbanNotFoundError:
        return f"❌ List not found: `{list_id}`"
    except KanbanError as e:
        return f"❌ Failed to create ticket: {e}"


async def handle_list_tickets(
    client: KanbanClient,
    params: dict[str, Any],
    default_board_id: str,
) -> str:
    """Handle list_tickets action.

    Args:
        client: The Kanban client instance
        params: Parameters from AI tool call
        default_board_id: Default board ID to use if not specified

    Returns:
        Formatted list of tickets

    """
    limit = params.get("limit", 3)
    board_id = params.get("board_id", default_board_id)

    try:
        boards = await client.get_boards()
        board = next((b for b in boards if b.id == board_id), None)

        if not board:
            return f"❌ Board not found: `{board_id}`"

        lists = await client.get_lists(board_id)
        all_cards = []

        for lst in lists:
            cards = await client.get_cards(lst.id)
            all_cards.extend(cards)

        # Get the most recent cards (up to limit)
        recent_cards = all_cards[:limit]

        if not recent_cards:
            return "📋 No open tickets found."

        msg = f"📋 **Recent Tickets** (showing {len(recent_cards)}):\n\n"
        desc_preview_length = 50
        for i, card in enumerate(recent_cards, 1):
            msg += f"{i}. **{card.name}**\n"
            msg += f"   🆔 ID: `{card.id}`\n"
            if card.description:
                desc_preview = card.description[:desc_preview_length]
                if len(card.description) > desc_preview_length:
                    desc_preview += "..."
                msg += f"   📝 {desc_preview}\n"
            msg += "\n"

        return msg.strip()
    except KanbanAuthenticationError:
        return "❌ Authentication failed. Please check Trello credentials."
    except KanbanError as e:
        return f"❌ Failed to list tickets: {e}"


async def handle_get_ticket(
    client: KanbanClient,
    params: dict[str, Any],
) -> str:
    """Handle get_ticket action.

    Args:
        client: The Kanban client instance
        params: Parameters from AI tool call

    Returns:
        Detailed ticket information

    """
    ticket_id = params["ticket_id"]

    try:
        card = await client.get_card(ticket_id)

        msg = "🎫 **Ticket Details**\n\n"
        msg += f"**Title:** {card.name}\n"
        msg += f"🆔 **ID:** `{card.id}`\n"

        if card.description:
            msg += f"\n📝 **Description:**\n{card.description}\n"
            return msg
        return msg  # noqa: TRY300
    except KanbanAuthenticationError:
        return "❌ Authentication failed. Please check Trello credentials."
    except KanbanNotFoundError:
        return f"❌ Ticket not found: `{ticket_id}`"
    except KanbanError as e:
        return f"❌ Failed to get ticket: {e}"


async def handle_close_ticket(
    client: KanbanClient,
    params: dict[str, Any],
) -> str:
    """Handle close_ticket action.

    Args:
        client: The Kanban client instance
        params: Parameters from AI tool call

    Returns:
        Success message

    """
    ticket_id = params["ticket_id"]

    try:
        # First get the card to show its name
        card = await client.get_card(ticket_id)
        card_name = card.name

        # Delete the card
        success = await client.delete_card(ticket_id)

        if success:
            return f"✅ Closed ticket: **{card_name}** (`{ticket_id}`)"
        return f"❌ Failed to close ticket: `{ticket_id}`"  # noqa: TRY300
    except KanbanAuthenticationError:
        return "❌ Authentication failed. Please check Trello credentials."
    except KanbanNotFoundError:
        return f"❌ Ticket not found: `{ticket_id}`"
    except KanbanError as e:
        return f"❌ Failed to close ticket: {e}"


async def handle_update_ticket(
    client: KanbanClient,
    params: dict[str, Any],
) -> str:
    """Handle update_ticket action.

    Args:
        client: The Kanban client instance
        params: Parameters from AI tool call

    Returns:
        Success message

    """
    ticket_id = params["ticket_id"]
    new_title = params.get("title")
    new_description = params.get("description")

    try:
        card = await client.update_card(
            card_id=ticket_id,
            name=new_title,
            description=new_description,
        )

        msg = f"✅ Updated ticket: **{card.name}** (`{ticket_id}`)\n"
        if new_title:
            msg += f"📝 New title: {new_title}\n"
        if new_description:
            msg += f"📝 New description: {new_description}\n"

        return msg.strip()
    except KanbanAuthenticationError:
        return "❌ Authentication failed. Please check Trello credentials."
    except KanbanNotFoundError:
        return f"❌ Ticket not found: `{ticket_id}`"
    except KanbanError as e:
        return f"❌ Failed to update ticket: {e}"


def handle_chat_response(params: dict[str, Any]) -> str:
    """Handle chat_response action (no ticket operation).

    Args:
        params: Parameters from AI tool call

    Returns:
        The chat message

    """
    result: str = params.get("message", "Hello! How can I help you with your tickets today?")
    return result


async def execute_tool_call(  # noqa: PLR0911
    tool_call: dict[str, Any],
    client: KanbanClient,
    default_board_id: str,
    default_list_id: str,
) -> str:
    """Execute a tool call from the AI and return the result.

    Args:
        tool_call: The validated tool call from AI
        client: The Kanban client instance
        default_board_id: Default board ID for operations
        default_list_id: Default list ID for creating tickets

    Returns:
        Message to send back to the user

    """
    action = tool_call["action"]
    params = tool_call.get("parameters", {})

    if action == "create_ticket":
        return await handle_create_ticket(client, params, default_list_id)
    if action == "list_tickets":
        return await handle_list_tickets(client, params, default_board_id)
    if action == "get_ticket":
        return await handle_get_ticket(client, params)
    if action == "close_ticket":
        return await handle_close_ticket(client, params)
    if action == "update_ticket":
        return await handle_update_ticket(client, params)
    if action == "chat_response":
        return handle_chat_response(params)
    return f"❌ Unknown action: {action}"
