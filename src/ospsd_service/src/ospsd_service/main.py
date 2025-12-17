"""OSPSD Service."""

# ruff: noqa: ERA001

import contextlib
import logging
import os
import sys
import threading
import time
from typing import Any

import uvicorn
from ai_api import AIInterface
from chat_client_api import ChatInterface, Message
from discord_client_impl.discord_impl import DiscordGateway
from dotenv import load_dotenv
from fastapi import FastAPI, Response
from telemetry_api import OperationType, TelemetryInterface
from tickets_api import TicketInterface, TicketStatus

from ospsd_service import prometheus_metrics
from ospsd_service.ticket_tools import (
    TICKET_TOOLS_SCHEMA,
    get_system_prompt_with_tools,
)

# Create FastAPI app for health checks
app = FastAPI(title="OSPSD Service")


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


def get_telemetry_client() -> TelemetryInterface:
    """Get the telemetry client and return it in a generic interface."""
    from telemetry_impl import InMemoryTelemetry  # noqa: PLC0415

    # Export metrics to a JSON file for observability
    export_path = os.getenv("TELEMETRY_EXPORT_PATH", "telemetry/metrics.json")
    return InMemoryTelemetry(export_path=export_path)


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
telemetry: TelemetryInterface = get_telemetry_client()

bot_id = os.getenv("DISCORD_CLIENT_ID")

# Description preview length for list_tickets
DESC_PREVIEW_LENGTH = 50


def record_metrics(
    operation: str, duration_ms: float, *, success: bool = True, error: str | None = None
) -> None:
    """Record metrics to both telemetry and Prometheus.

    Args:
        operation: Operation name (e.g., 'ai_generate', 'ticket_create')
        duration_ms: Duration in milliseconds
        success: Whether the operation succeeded
        error: Error message if failed

    """
    # Map operation names to OperationType enum
    operation_map = {
        "ai_generate": OperationType.AI_GENERATE,
        "ticket_create": OperationType.TICKET_CREATE,
        "ticket_list": OperationType.TICKET_LIST,
        "ticket_get": OperationType.TICKET_GET,
        "ticket_update": OperationType.TICKET_UPDATE,
        "ticket_delete": OperationType.TICKET_DELETE,
        "chat_message": OperationType.CHAT_MESSAGE,
    }

    # Record to telemetry
    telemetry_op = operation_map.get(operation, OperationType.CHAT_MESSAGE)
    telemetry.record_latency(telemetry_op, duration_ms, success=success, error_message=error)
    if not success and error:
        telemetry.record_failure(telemetry_op, error)

    # Record to Prometheus
    prometheus_metrics.record_latency(operation, duration_ms, success=success)


# TODO(Andrew): add tests  # noqa: TD003, FIX002
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
    chat_log = ""
    for m in reversed(msgs):
        if m.sender_id == author_id:
            chat_log += author
        elif m.sender_id == bot_id:
            chat_log += "Bot"
        else:
            chat_log += m.sender_id
        chat_log += ": " + m.content + "\n"
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
        record_metrics("ai_generate", ai_duration, success=True)
        logger.info(ai_response)
    except Exception as e:
        ai_duration = (time.time() - ai_start) * 1000
        record_metrics("ai_generate", ai_duration, success=False, error=str(e))
        raise

    if ai_response["action"] == "chat_response":
        chat_client.send_message(channel_id, ai_response["parameters"]["message"])

    elif ai_response["action"] == "create_ticket":
        ticket_start = time.time()
        try:
            created_ticket = ticket_client.create_ticket(
                ai_response["parameters"]["title"],
                ai_response["parameters"]["description"],
                ai_response["parameters"].get("assignee", None),
            )
            ticket_duration = (time.time() - ticket_start) * 1000
            record_metrics("ticket_create", ticket_duration, success=True)

            # Format for Discord markdown
            msg = "✅ **Created Ticket**\n\n"
            msg += f"**{created_ticket.title}**\n"
            if created_ticket.description:
                msg += f"> {created_ticket.description}\n\n"
            msg += f"🆔 ID: `{created_ticket.id}`"
            chat_client.send_message(channel_id, msg)
        except Exception as e:
            ticket_duration = (time.time() - ticket_start) * 1000
            record_metrics("ticket_create", ticket_duration, success=False, error=str(e))
            raise

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
            record_metrics("ticket_list", ticket_duration, success=True)

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
            ticket_duration = (time.time() - ticket_start) * 1000
            record_metrics("ticket_list", ticket_duration, success=False, error=str(e))
            raise

    elif ai_response["action"] == "get_ticket":
        ticket_start = time.time()
        try:
            ticket_id = ai_response["parameters"]["ticket_id"]
            ticket = ticket_client.get_ticket(ticket_id)
            ticket_duration = (time.time() - ticket_start) * 1000
            record_metrics("ticket_get", ticket_duration, success=True)

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
            ticket_duration = (time.time() - ticket_start) * 1000
            record_metrics("ticket_get", ticket_duration, success=False, error=str(e))
            raise

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
            record_metrics("ticket_update", ticket_duration, success=True)

            msg = f"✅ **Updated Ticket**\n\n**{ticket.title}**\n"
            msg += f"*ID:* `{ticket.id}` | *Status:* {ticket.status.value}"
            chat_client.send_message(channel_id, msg)
        except Exception as e:
            ticket_duration = (time.time() - ticket_start) * 1000
            record_metrics("ticket_update", ticket_duration, success=False, error=str(e))
            raise

    elif ai_response["action"] == "close_ticket":
        ticket_start = time.time()
        try:
            ticket_id = ai_response["parameters"]["ticket_id"]
            success = ticket_client.delete_ticket(ticket_id)
            ticket_duration = (time.time() - ticket_start) * 1000
            record_metrics("ticket_delete", ticket_duration, success=True)

            if success:
                chat_client.send_message(channel_id, f"✅ Closed ticket: `{ticket_id}`")
            else:
                chat_client.send_message(channel_id, f"❌ Failed to close ticket: `{ticket_id}`")
        except Exception as e:
            ticket_duration = (time.time() - ticket_start) * 1000
            record_metrics("ticket_delete", ticket_duration, success=False, error=str(e))
            raise

    else:
        logger.warning(f"Unknown action: {ai_response.get('action')}")

    # Track overall message handling latency
    total_duration = (time.time() - start_time) * 1000
    record_metrics("chat_message", total_duration, success=True)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint for container orchestration."""
    return {"status": "healthy", "service": "ospsd"}


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": "OSPSD Service is running", "status": "ok"}


@app.get("/metrics")
async def metrics() -> Response:
    """Prometheus metrics endpoint."""
    return Response(content=prometheus_metrics.get_metrics(), media_type="text/plain")


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


# from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
# from fastapi import FastAPI, Response
#
# app = FastAPI()
#
# # Metrics
# REQUEST_COUNT = Counter('app_requests_total', 'Total request count')
# REQUEST_DURATION = Histogram('app_request_duration_seconds', 'Request duration')
#
# @app.get("/metrics")
# async def metrics():
#     REQUEST_COUNT.inc()
#     return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
#
# @app.get("/health")
# async def health():
#     return {"status": "healthy"}
