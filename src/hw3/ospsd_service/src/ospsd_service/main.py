"""OSPSD Service."""

import contextlib
import logging
import os
import sys
import threading
import time
from typing import Any

import uvicorn
from ai_api import AIInterface
from chat_api import ChatInterface, Message
from discord_chat_impl.discord_impl import DiscordGateway
from dotenv import load_dotenv
from fastapi import FastAPI, Response
from tickets_api import TicketInterface, TicketStatus

from ospsd_service.metrics import get_metrics, record_latency
from ospsd_service.ticket_tools import (
    TICKET_TOOLS_SCHEMA,
    get_system_prompt_with_tools,
)

# Create FastAPI app for health checks
app = FastAPI(title="OSPSD Service")


# Would be great if this could be moved to a get_..._client method in the API
def get_discord_client() -> ChatInterface:
    """Get the Discord client and return it in a generic interface."""
    from discord_chat_impl import DiscordClient  # noqa: PLC0415

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
ticket_client: TicketInterface = get_trello_client()

bot_id = os.getenv("DISCORD_CLIENT_ID")

# AI client state - can be switched at runtime via Discord commands
current_model: str = "claude"  # Default model
ai_client: AIInterface = get_claude_client()

# Description preview length for list_tickets
DESC_PREVIEW_LENGTH = 50


def _handle_ticket_exception(channel_id: str, exc: Exception, metric_name: str, start_time: float) -> None:
    """Record ticket metric failure and notify Discord about the error.

    If the error message appears authentication-related, send a specific authentication
    failure message; otherwise send a generic ticket-service error.
    """
    duration = (time.time() - start_time) * 1000
    record_latency(metric_name, duration, success=False)
    logger.exception("Ticket client error")

    err_text = (str(exc) or "").lower()
    if any(k in err_text for k in ("auth", "authentication", "unauthorized", "401", "403")):
        msg = "❌ Authentication to ticket service failed."
    else:
        msg = "❌ Ticket service error: " + (str(exc) or "unknown error")

    try:
        chat_client.send_message(channel_id, msg)
    except Exception:
        logger.exception("Failed to send ticket error message to Discord")


def _handle_ai_exception(channel_id: str, exc: Exception, metric_name: str, start_time: float) -> None:
    """Record AI metric failure and notify Discord about the error.

    If the error message appears authentication-related, send a specific authentication
    failure message; otherwise send a generic AI service error.
    """
    duration = (time.time() - start_time) * 1000
    record_latency(metric_name, duration, success=False)
    logger.exception("AI client error")

    err_text = (str(exc) or "").lower()
    if any(k in err_text for k in ("auth", "authentication", "unauthorized", "401", "403", "api key", "invalid_api_key", "forbidden")):
        msg = "❌ Authentication to AI service failed."
    else:
        msg = "❌ AI service error: " + (str(exc) or "unknown error")

    try:
        chat_client.send_message(channel_id, msg)
    except Exception:
        logger.exception("Failed to send AI error message to Discord")


def handle_message(data: dict[str, Any]) -> None:  # noqa: C901, PLR0912, PLR0915
    """Call this function when a message is sent in the server.

    Args:
        data (dict[str, Any]): The data received from the server

    """
    start_time = time.time()

    author: str = data["author"]["username"]
    author_id: str = data["author"]["id"]
    channel_id: str = data["channel_id"]

    # do not respond to messages sent by the bot
    if author_id == bot_id:
        return

    # Get recent conversation history (last 10 messages)
    msgs: list[Message] = chat_client.get_messages(channel_id, limit=10)

    # Get the most recent message content (the current message)
    message_content = msgs[0].content.strip() if msgs else ""

    # Handle /model commands for switching AI providers
    if message_content.startswith("/model"):
        global ai_client, current_model  # noqa: PLW0603

        parts = message_content.split()
        if len(parts) == 1 or parts[1].lower() == "status":
            # Show current model
            chat_client.send_message(channel_id, f"🤖 Current AI model: **{current_model}**")
            return

        model_name = parts[1].lower()
        if model_name == "openai":
            init_start = time.time()
            try:
                ai_client = get_openai_client()
                current_model = "openai"
                chat_client.send_message(channel_id, "✅ Switched to **OpenAI** model")
                logger.info("Switched to OpenAI model")
                return
            except Exception as e:
                _handle_ai_exception(channel_id, e, "ai_switch", init_start)
                return
        if model_name == "claude":
            init_start = time.time()
            try:
                ai_client = get_claude_client()
                current_model = "claude"
                chat_client.send_message(channel_id, "✅ Switched to **Claude** model")
                logger.info("Switched to Claude model")
                return
            except Exception as e:
                _handle_ai_exception(channel_id, e, "ai_switch", init_start)
                return

        chat_client.send_message(
            channel_id,
            f"❌ Unknown model: `{model_name}`\n\n"
            "Available commands:\n"
            "• `/model openai` - Switch to OpenAI\n"
            "• `/model claude` - Switch to Claude\n"
            "• `/model status` - Show current model",
        )
        return

    # Only respond to messages that start with /bot
    if not message_content.startswith("/bot"):
        return

    # Build chat log from message history, stripping /bot prefix from user messages
    chat_log = ""
    for m in reversed(msgs):
        if m.sender_id == author_id:
            chat_log += author
        elif m.sender_id == bot_id:
            chat_log += "Bot"
        else:
            chat_log += m.sender_id

        # Strip /bot prefix from message content if present
        content = m.content
        if content.startswith("/bot "):
            content = content[5:]  # Remove "/bot " (5 characters including space)
        elif content.startswith("/bot"):
            content = content[4:].strip()  # Remove "/bot" and any whitespace

        chat_log += ": " + content + "\n"
    logger.debug(chat_log)

    # Generate system prompt with ticket tool definitions
    system_prompt = get_system_prompt_with_tools()

    # Track AI generation latency
    ai_start = time.time()
    try:
        ai_response: Any = ai_client.generate_response(
            chat_log,
            system_prompt,
            response_schema=TICKET_TOOLS_SCHEMA,
        )
        ai_duration = (time.time() - ai_start) * 1000
        record_latency("ai_generate", ai_duration, success=True)
        logger.info(ai_response)
    except Exception as e:
        _handle_ai_exception(channel_id, e, "ai_generate", ai_start)
        return

    if ai_response["action"] == "chat_response":
        chat_client.send_message(channel_id, ai_response["parameters"]["message"])

    elif ai_response["action"] == "create_ticket":
        ticket_start = time.time()
        try:
            # Extract parameters, using empty string for None values where needed
            params = ai_response["parameters"]
            created_ticket = ticket_client.create_ticket(
                params["title"],
                params.get("description") or "",  # Use empty string if None
                params.get("assignee"),
            )
            ticket_duration = (time.time() - ticket_start) * 1000
            record_latency("ticket_create", ticket_duration, success=True)

            # Format for Discord markdown
            msg = "✅ **Created Ticket**\n\n"
            msg += f"**{created_ticket.title}**\n"
            if created_ticket.description:
                msg += f"> {created_ticket.description}\n\n"
            msg += f"🆔 ID: `{created_ticket.id}`"
            chat_client.send_message(channel_id, msg)
        except Exception as e:
            _handle_ticket_exception(channel_id, e, "ticket_create", ticket_start)
            return

    elif ai_response["action"] == "list_tickets":
        ticket_start = time.time()
        try:
            # Extract and normalize status if provided
            status_param = ai_response["parameters"].get("status")
            status_enum = None
            if status_param:
                # Normalize status string (replace spaces with underscores and lowercase)
                normalized_status = status_param.lower().replace(" ", "_")
                status_enum = TicketStatus(normalized_status)

            tickets = ticket_client.search_tickets(status=status_enum)
            ticket_duration = (time.time() - ticket_start) * 1000
            record_latency("ticket_list", ticket_duration, success=True)

            if not tickets:
                status_msg = f" {status_enum.value}" if status_enum else ""
                chat_client.send_message(channel_id, f"📋 No{status_msg} tickets found.")
            else:
                # Format for Discord markdown with better readability
                status_filter = f" ({status_enum.value})" if status_enum else ""
                msg = f"📋 **Recent Tickets{status_filter}** (showing {len(tickets)}):\n\n"
                for i, t in enumerate(tickets, 1):
                    msg += f"**{i}. {t.title}**\n"
                    if t.description:
                        # Show preview of description
                        desc_preview = t.description[:DESC_PREVIEW_LENGTH]
                        if len(t.description) > DESC_PREVIEW_LENGTH:
                            desc_preview += "..."
                        msg += f"> {desc_preview}\n"
                    msg += f"*ID:* `{t.id}` | *Status:* {t.status.value}\n\n"
                chat_client.send_message(channel_id, msg.strip())
        except Exception as e:
            _handle_ticket_exception(channel_id, e, "ticket_list", ticket_start)
            return

    elif ai_response["action"] == "get_ticket":
        ticket_start = time.time()
        try:
            ticket_id = ai_response["parameters"]["ticket_id"]
            ticket = ticket_client.get_ticket(ticket_id)
            ticket_duration = (time.time() - ticket_start) * 1000
            record_latency("ticket_get", ticket_duration, success=True)

            if ticket is None:
                chat_client.send_message(channel_id, f"❌ Ticket not found: `{ticket_id}`")
            else:
                # Format for Discord markdown
                msg = f"🎫 **Ticket Details**\n\n**{ticket.title}**\n\n"
                if ticket.description:
                    msg += f"> {ticket.description}\n\n"
                msg += f"*ID:* `{ticket.id}` | *Status:* {ticket.status.value}"
                if ticket.assignee:
                    msg += f" | *Assignee:* {ticket.assignee}"
                chat_client.send_message(channel_id, msg)
        except Exception as e:
            _handle_ticket_exception(channel_id, e, "ticket_get", ticket_start)
            return

    elif ai_response["action"] == "update_ticket":
        ticket_start = time.time()
        try:
            # Convert status string to TicketStatus enum if provided
            status_param = ai_response["parameters"].get("status")
            status_enum = None
            if status_param:
                # Normalize status string (replace spaces with underscores and lowercase)
                normalized_status = status_param.lower().replace(" ", "_")
                status_enum = TicketStatus(normalized_status)

            ticket = ticket_client.update_ticket(
                ai_response["parameters"]["ticket_id"],
                status=status_enum,
                title=ai_response["parameters"].get("title"),
            )
            ticket_duration = (time.time() - ticket_start) * 1000
            record_latency("ticket_update", ticket_duration, success=True)

            msg = f"✅ **Updated Ticket**\n\n**{ticket.title}**\n"
            msg += f"*ID:* `{ticket.id}` | *Status:* {ticket.status.value}"
            chat_client.send_message(channel_id, msg)
        except Exception as e:
            _handle_ticket_exception(channel_id, e, "ticket_update", ticket_start)
            return

    elif ai_response["action"] == "close_ticket":
        ticket_start = time.time()
        try:
            ticket_id = ai_response["parameters"]["ticket_id"]
            success = ticket_client.delete_ticket(ticket_id)
            ticket_duration = (time.time() - ticket_start) * 1000
            record_latency("ticket_delete", ticket_duration, success=True)

            if success:
                chat_client.send_message(channel_id, f"✅ Closed ticket: `{ticket_id}`")
            else:
                chat_client.send_message(channel_id, f"❌ Failed to close ticket: `{ticket_id}`")
        except Exception as e:
            _handle_ticket_exception(channel_id, e, "ticket_delete", ticket_start)
            return

    else:
        logger.warning(f"Unknown action: {ai_response.get('action')}")

    # Track overall message handling latency
    total_duration = (time.time() - start_time) * 1000
    record_latency("chat_message", total_duration, success=True)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": "OSPSD Service is running", "status": "ok"}


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint for container orchestration."""
    return {"status": "healthy", "service": "ospsd"}


@app.get("/metrics")
async def metrics() -> Response:
    """Prometheus metrics endpoint."""
    return Response(content=get_metrics(), media_type="text/plain")


def run_discord_gateway() -> None:
    """Run the Discord gateway in a separate thread."""
    gateway_client.subscribe("MESSAGE_CREATE", handle_message)
    gateway_client.start()

    while True:
        time.sleep(1)


def run_fastapi_server() -> None:
    """Run the FastAPI server for health checks."""
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")  # noqa: S104


# Start Discord gateway in a separate thread
gateway_thread = threading.Thread(target=run_discord_gateway, daemon=True)
gateway_thread.start()

# Run FastAPI server in the main thread
run_fastapi_server()
