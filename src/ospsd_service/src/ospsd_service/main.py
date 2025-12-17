"""OSPSD Service."""

import contextlib
import logging
import os
import sys
import time
from typing import Any

from ai_api import AIInterface
from chat_client_api import ChatInterface, Message
from discord_client_impl.discord_impl import DiscordGateway
from dotenv import load_dotenv
from tickets_api import TicketInterface

from ospsd_service.ticket_tools import (
    TICKET_TOOLS_SCHEMA,
    get_system_prompt_with_tools,
)


# Would be great if this could be moved to a get_..._client method in the API
def get_discord_client() -> ChatInterface:
    """Get the Discord client and return it in a generic interface."""
    from discord_client_impl import DiscordClient  # noqa: PLC0415

    return DiscordClient()


def get_openai_client() -> AIInterface:
    """Get the OpenAI client and return it in a generic interface."""
    from openai_client_service import EnvAIImplementation  # noqa: PLC0415

    return EnvAIImplementation()


def get_claude_client() -> AIInterface:
    """Get the Claude client and return it in a generic interface."""
    from claude_client_service import EnvAIImplementation  # noqa: PLC0415

    return EnvAIImplementation()


def get_trello_client() -> TicketInterface:
    """Get the Trello client and return it in a generic interface."""
    from trello_ticket_impl import TrelloTicketClientImpl  # noqa: PLC0415

    return TrelloTicketClientImpl()


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

with contextlib.suppress(FileNotFoundError):
    load_dotenv()
required_env_vars = [
    "DISCORD_BOT_TOKEN",
    "DISCORD_CLIENT_ID",
    "DISCORD_CLIENT_SECRET",
    "DISCORD_PUBLIC_KEY",
    "OPENAI_API_KEY",
    "CLAUDE_API_KEY",
    "TRELLO_API_KEY",
    "TRELLO_API_SECRET",  # This is actually the token
    "TRELLO_BOARD_ID",
]
if all(v not in os.environ for v in required_env_vars):
    sys.exit("Required environment variables are not set.")

gateway_client: DiscordGateway = DiscordGateway()

chat_client: ChatInterface = get_discord_client()
ai_client: AIInterface = get_claude_client()  # change this between claude/openai!
ticket_client: TicketInterface = get_trello_client()

bot_id = os.getenv("DISCORD_CLIENT_ID")

# Description preview length for list_tickets
DESC_PREVIEW_LENGTH = 50


# TODO(Andrew): add tests  # noqa: TD003, FIX002
def handle_message(data: dict[str, Any]) -> None:  # noqa: C901, PLR0912, PLR0915
    """Call this function when a message is sent in the server.

    Args:
        data (dict[str, Any]): The data received from the server

    """
    author: str = data["author"]["username"]
    author_id: str = data["author"]["id"]
    channel_id: str = data["channel_id"]

    # do not respond to messages sent by the bot
    if author_id == bot_id:
        return

    # TODO(Steven): change the prompt to look at previous messages  # noqa: TD003, FIX002
    msgs: list[Message] = chat_client.get_messages(channel_id, limit=1)
    chat_log = ""
    for msg in reversed(msgs):
        if msg.sender_id == author_id:
            chat_log += author
        elif msg.sender_id == bot_id:
            chat_log += "Bot"
        else:
            chat_log += msg.sender_id
        chat_log += ": " + msg.content + "\n"
    logger.debug(chat_log)

    # Generate system prompt with ticket tool definitions
    system_prompt = get_system_prompt_with_tools()
    ai_response = ai_client.generate_response(
        chat_log,
        system_prompt,
        response_schema=TICKET_TOOLS_SCHEMA,
    )
    logger.info(ai_response)

    if ai_response["action"] == "chat_response":
        chat_client.send_message(channel_id, ai_response["parameters"]["message"])

    elif ai_response["action"] == "create_ticket":
        ticket = ticket_client.create_ticket(
            ai_response["parameters"]["title"],
            ai_response["parameters"]["description"],
            ai_response["parameters"].get("assignee", None),
        )
        # Format for Discord markdown
        msg = "✅ **Created Ticket**\n\n"
        msg += f"**{ticket.title}**\n"
        if ticket.description:
            msg += f"> {ticket.description}\n\n"
        msg += f"🆔 ID: `{ticket.id}`"
        chat_client.send_message(channel_id, msg)

    elif ai_response["action"] == "list_tickets":
        tickets = ticket_client.search_tickets()

        if not tickets:
            chat_client.send_message(channel_id, "📋 No open tickets found.")
        else:
            # Format for Discord markdown with better readability
            msg = f"📋 **Recent Tickets** (showing {len(tickets)}):\n\n"
            for i, ticket in enumerate(tickets, 1):
                msg += f"**{i}. {ticket.title}**\n"
                if ticket.description:
                    # Show preview of description
                    desc_preview = ticket.description[:DESC_PREVIEW_LENGTH]
                    if len(ticket.description) > DESC_PREVIEW_LENGTH:
                        desc_preview += "..."
                    msg += f"> {desc_preview}\n"
                msg += f"*ID:* `{ticket.id}` | *Status:* {ticket.status}\n\n"
            chat_client.send_message(channel_id, msg.strip())

    elif ai_response["action"] == "get_ticket":
        ticket_id = ai_response["parameters"]["ticket_id"]
        ticket = ticket_client.get_ticket(ticket_id)
        if ticket is None:
            chat_client.send_message(channel_id, f"❌ Ticket not found: `{ticket_id}`")
        else:
            # Format for Discord markdown
            msg = f"🎫 **Ticket Details**\n\n**{ticket.title}**\n\n"
            if ticket.description:
                msg += f"> {ticket.description}\n\n"
            msg += f"*ID:* `{ticket.id}` | *Status:* {ticket.status}"
            if ticket.assignee:
                msg += f" | *Assignee:* {ticket.assignee}"
            chat_client.send_message(channel_id, msg)

    elif ai_response["action"] == "update_ticket":
        ticket = ticket_client.update_ticket(
            ai_response["parameters"]["ticket_id"],
            status=ai_response["parameters"].get("status"),
            title=ai_response["parameters"].get("title"),
        )
        msg = f"✅ **Updated Ticket**\n\n**{ticket.title}**\n"
        msg += f"*ID:* `{ticket.id}` | *Status:* {ticket.status}"
        chat_client.send_message(channel_id, msg)

    elif ai_response["action"] == "close_ticket":
        ticket_id = ai_response["parameters"]["ticket_id"]
        success = ticket_client.delete_ticket(ticket_id)
        if success:
            chat_client.send_message(channel_id, f"✅ Closed ticket: `{ticket_id}`")
        else:
            chat_client.send_message(channel_id, f"❌ Failed to close ticket: `{ticket_id}`")

    else:
        logger.warning(f"Unknown action: {ai_response.get('action')}")


gateway_client.subscribe("MESSAGE_CREATE", handle_message)
gateway_client.start()

while True:
    time.sleep(1)
