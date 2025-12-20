"""OSPSD Service."""

import contextlib
import logging
import os
import sys
import time
from typing import Any

import uvicorn
from ai_api import AIInterface
from chat_api import ChatInterface, Message
from discord_chat_impl.discord_impl import DiscordGateway
from dotenv import load_dotenv
from fastapi import FastAPI, Response
from tickets_api import Ticket, TicketInterface, TicketStatus

from ospsd_service.metrics import get_metrics, record_latency
from ospsd_service.ticket_tools import (
    TICKET_DESC_PREVIEW_LEN,
    TICKET_SYS_PROMPT,
    TICKET_TOOLS_SCHEMA,
)


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
    "TRELLO_API_SECRET",
    "TRELLO_BOARD_ID",
]
if all(v not in os.environ for v in required_env_vars):
    sys.exit("Required environment variables are not set.")

chat_client: ChatInterface = get_discord_client()
ticket_client: TicketInterface = get_trello_client()
ai_client: AIInterface = get_claude_client()


class MessageHandler:
    """Handles Discord messages and coordinates AI/ticket operations."""

    def __init__(self, bot_id: str, default_model: str) -> None:
        """Initialize the message handler.

        Args:
            bot_id: The bot's Discord ID
            default_model: The default AI model being used

        """
        self.bot_id = bot_id
        self.current_model = default_model

    def handle_message(self, data: dict[str, Any]) -> None:  # noqa: C901
        """Call this function when a message is sent in the server.

        Args:
            data (dict[str, Any]): The data received from the server

        """
        start_time = time.time()

        author: str = data["author"]["username"]
        author_id: str = data["author"]["id"]
        channel_id: str = data["channel_id"]

        # do not respond to messages sent by the bot
        if author_id == self.bot_id:
            return

        # Get recent conversation history (last 10 messages)
        msgs: list[Message] = chat_client.get_messages(channel_id, limit=10)

        # Get the most recent message content (the current message)
        message_content = msgs[0].content.strip() if msgs else ""

        # Handle /model commands for switching AI providers
        if message_content.startswith("/model"):
            self._handle_model_command(channel_id, message_content)
            return

        # Only respond if the latest message starts with /bot
        if not message_content.startswith("/bot"):
            return

        # Build chat log from message history, stripping /bot prefix from user messages
        chat_log = self._build_chat_log(msgs, author, author_id)
        logger.debug(chat_log)

        # Track AI generation latency
        ai_start = time.time()
        try:
            # since system_schema is provided, the response must be a dict
            ai_response: dict[str, Any] = ai_client.generate_response(  # type: ignore[assignment]
                chat_log,
                system_prompt=TICKET_SYS_PROMPT,
                response_schema=TICKET_TOOLS_SCHEMA,
            )
            record_latency("ai_generate", ai_start, success=True)
            logger.info(ai_response)
        except Exception as e:  # noqa: BLE001
            self._handle_ai_exception(channel_id, e, "ai_generate", ai_start)
            return

        action = ai_response["action"]

        if action == "chat_response":
            self._handle_chat_response(channel_id, ai_response)
        elif action == "create_ticket":
            self._handle_create_ticket(channel_id, ai_response)
        elif action == "list_tickets":
            self._handle_list_tickets(channel_id, ai_response)
        elif action == "get_ticket":
            self._handle_get_ticket(channel_id, ai_response)
        elif action == "update_ticket":
            self._handle_update_ticket(channel_id, ai_response)
        elif action == "close_ticket":
            self._handle_close_ticket(channel_id, ai_response)
        else:
            logger.warning(f"Unknown action: {action}")

        # Track overall pipeline latency (end-to-end request handling)
        record_latency("pipeline_total", start_time, success=True)

    def _send_discord_message(self, channel_id: str, message: str) -> None:
        """Send a message to Discord with metrics tracking.

        Args:
            channel_id: The Discord channel ID
            message: The message to send

        """
        discord_start = time.time()
        try:
            chat_client.send_message(channel_id, message)
            record_latency("discord_send_message", discord_start, success=True)
        except Exception:
            record_latency("discord_send_message", discord_start, success=False)
            logger.exception("Failed to send message to Discord")

    def _handle_ai_exception(
        self,
        channel_id: str,
        exc: Exception,
        metric_name: str,
        start_time: float,
    ) -> None:
        """Record AI metric failure and attempt to notify Discord about the error.

        Args:
            channel_id: The Discord channel ID
            exc: The exception that occurred
            metric_name: Name of the metric for tracking
            start_time: When the operation started

        """
        record_latency(metric_name, start_time, success=False)
        logger.exception("AI client error")

        err_text = (str(exc) or "").lower()
        if any(k in err_text for k in ("auth", "authentication", "unauthorized", "401", "403")):
            msg = "❌ Authentication to AI service failed."
        else:
            msg = "❌ AI service error: " + (str(exc) or "unknown error")

        self._send_discord_message(channel_id, msg)

    def _handle_ticket_exception(
        self,
        channel_id: str,
        exc: Exception,
        metric_name: str,
        start_time: float,
    ) -> None:
        """Record ticket metric failure and notify Discord about the error.

        Args:
            channel_id: The Discord channel ID
            exc: The exception that occurred
            metric_name: Name of the metric for tracking
            start_time: When the operation started

        """
        record_latency(metric_name, start_time, success=False)
        logger.exception("Ticket client error")

        err_text = (str(exc) or "").lower()
        if any(k in err_text for k in ("auth", "authentication", "unauthorized", "401", "403")):
            msg = "❌ Authentication to ticket service failed."
        else:
            msg = "❌ Ticket service error: " + (str(exc) or "unknown error")

        self._send_discord_message(channel_id, msg)

    def _handle_model_command(self, channel_id: str, message_content: str) -> None:
        """Handle /model commands for switching AI providers.

        Args:
            channel_id: The Discord channel ID
            message_content: The full message content

        """
        global ai_client  # noqa: PLW0603

        parts = message_content.split()
        if len(parts) == 1 or parts[1].lower() == "status":
            # Show the current model
            self._send_discord_message(channel_id, f"🤖 Current AI model: **{self.current_model}**")
            return

        model_name = parts[1].lower()
        if model_name == "openai":
            init_start = time.time()
            try:
                ai_client = get_openai_client()
                self.current_model = "openai"
            except Exception as e:  # noqa: BLE001
                self._handle_ai_exception(channel_id, e, "ai_switch", init_start)
                return
            else:
                self._send_discord_message(channel_id, "✅ Switched to **OpenAI** model")
                logger.info("Switched to OpenAI model")
                return
        if model_name == "claude":
            init_start = time.time()
            try:
                ai_client = get_claude_client()
                self.current_model = "claude"
            except Exception as e:  # noqa: BLE001
                self._handle_ai_exception(channel_id, e, "ai_switch", init_start)
                return
            else:
                self._send_discord_message(channel_id, "✅ Switched to **Claude** model")
                logger.info("Switched to Claude model")
                return

        self._send_discord_message(
            channel_id,
            f"❌ Unknown model: `{model_name}`\n\n"
            "Available commands:\n"
            "• `/model openai` - Switch to OpenAI\n"
            "• `/model claude` - Switch to Claude\n"
            "• `/model status` - Show current model",
        )

    def _build_chat_log(self, msgs: list[Message], author: str, author_id: str) -> str:
        """Build a chat log from message history.

        Args:
            msgs: List of messages in chronological order (newest first)
            author: Username of the current message author
            author_id: ID of the current message author

        Returns:
            Formatted chat log string

        """
        chat_log = ""
        for m in reversed(msgs):
            if m.sender_id == author_id:
                chat_log += author
            elif m.sender_id == self.bot_id:
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

        return chat_log

    def _handle_chat_response(self, channel_id: str, ai_response: dict[str, Any]) -> None:
        """Handle chat response action from AI.

        Args:
            channel_id: The Discord channel ID
            ai_response: The AI response containing the chat message

        """
        self._send_discord_message(channel_id, ai_response["parameters"]["message"])

    def _format_ticket(self, ticket: Ticket, *, truncate_desc: bool) -> str:
        """Format a ticket for display in Discord."""
        msg = f"**{ticket.title}**\n"
        if ticket.description:
            desc = ticket.description

            if truncate_desc:
                desc = ticket.description[:TICKET_DESC_PREVIEW_LEN]
                if len(ticket.description) > TICKET_DESC_PREVIEW_LEN:
                    desc += "..."

            msg += f"> Description: {desc}\n"
        if ticket.assignee:
            msg += f"> Assignee: {ticket.assignee}\n"
        else:
            msg += "> Assignee: Unassigned\n"
        msg += f"> Status: {ticket.status.value}\n> ID: `{ticket.id}`\n\n"
        return msg

    def _handle_create_ticket(self, channel_id: str, ai_response: dict[str, Any]) -> None:
        """Handle creating ticket from AI.

        Args:
            channel_id: The Discord channel ID
            ai_response: The AI response containing ticket parameters

        """
        ticket_start = time.time()
        try:
            # Extract parameters, using empty string for None values where needed
            params = ai_response["parameters"]
            created_ticket = ticket_client.create_ticket(
                params["title"],
                params.get("description") or "",  # Use empty string if None
                params.get("assignee"),
            )
            record_latency("ticket_create", ticket_start, success=True)

            # Format for Discord Markdown
            msg = "✅ **Created Ticket**\n\n"
            msg += self._format_ticket(created_ticket, truncate_desc=False)

            self._send_discord_message(channel_id, msg)
        except Exception as e:  # noqa: BLE001
            self._handle_ticket_exception(channel_id, e, "ticket_create", ticket_start)

    def _handle_list_tickets(self, channel_id: str, ai_response: dict[str, Any]) -> None:
        """Handle list tickets action from AI.

        Args:
            channel_id: The Discord channel ID
            ai_response: The AI response containing an optional status filter

        """
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
            record_latency("ticket_list", ticket_start, success=True)

            if not tickets:
                status_msg = f" {status_enum.value}" if status_enum else ""
                msg = f"📋 No{status_msg} tickets found."
            else:
                # Format for Discord Markdown with better readability
                status_filter = f" ({status_enum.value})" if status_enum else ""
                msg = f"📋 **Recent Tickets{status_filter}** (showing {len(tickets)}):\n\n"
                for i, ticket in enumerate(tickets, 1):
                    msg += f"{i}. " + self._format_ticket(ticket, truncate_desc=True)

            self._send_discord_message(channel_id, msg.strip())
        except Exception as e:  # noqa: BLE001
            self._handle_ticket_exception(channel_id, e, "ticket_list", ticket_start)

    def _handle_get_ticket(self, channel_id: str, ai_response: dict[str, Any]) -> None:
        """Handle get ticket action from AI.

        Args:
            channel_id: The Discord channel ID
            ai_response: The AI response containing ticket_id

        """
        ticket_start = time.time()
        try:
            ticket_id = ai_response["parameters"]["ticket_id"]
            ticket = ticket_client.get_ticket(ticket_id)
            record_latency("ticket_get", ticket_start, success=True)

            if ticket is None:
                msg = f"❌ Ticket not found: `{ticket_id}`"
            else:
                # Format for Discord Markdown
                msg = "🎫 **Ticket Details**\n\n"
                msg += self._format_ticket(ticket, truncate_desc=False)

            self._send_discord_message(channel_id, msg)
        except Exception as e:  # noqa: BLE001
            self._handle_ticket_exception(channel_id, e, "ticket_get", ticket_start)

    def _handle_update_ticket(self, channel_id: str, ai_response: dict[str, Any]) -> None:
        """Handle update ticket action from AI.

        Args:
            channel_id: The Discord channel ID
            ai_response: The AI response containing update parameters

        """
        ticket_start = time.time()
        try:
            # Convert a status string to TicketStatus enum if provided
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
            record_latency("ticket_update", ticket_start, success=True)

            msg = "✅ **Updated Ticket**\n\n"
            msg += self._format_ticket(ticket, truncate_desc=False)

            self._send_discord_message(channel_id, msg)
        except Exception as e:  # noqa: BLE001
            self._handle_ticket_exception(channel_id, e, "ticket_update", ticket_start)

    def _handle_close_ticket(self, channel_id: str, ai_response: dict[str, Any]) -> None:
        """Handle close ticket action from AI.

        Args:
            channel_id: The Discord channel ID
            ai_response: The AI response containing ticket_id

        """
        ticket_start = time.time()
        try:
            ticket_id = ai_response["parameters"]["ticket_id"]
            success = ticket_client.delete_ticket(ticket_id)
            record_latency("ticket_delete", ticket_start, success=True)

            if success:
                msg = f"✅ Closed ticket: `{ticket_id}`"
            else:
                msg = f"❌ Failed to close ticket: `{ticket_id}`"

            self._send_discord_message(channel_id, msg)
        except Exception as e:  # noqa: BLE001
            self._handle_ticket_exception(channel_id, e, "ticket_delete", ticket_start)


app = FastAPI(title="OSPSD Service")


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


handler = MessageHandler(
    bot_id=os.environ["DISCORD_CLIENT_ID"],
    default_model="claude",
)

# Start Discord gateway (different thread)
gateway_client: DiscordGateway = DiscordGateway()
gateway_client.subscribe("MESSAGE_CREATE", handler.handle_message)
gateway_client.start()

# Run FastAPI server (main thread)
uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")  # noqa: S104 (allow listening to 0.0.0.0)
