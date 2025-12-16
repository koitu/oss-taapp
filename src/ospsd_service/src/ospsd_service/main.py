"""OSPSD Service."""

import asyncio
import json
import logging
import os
import sys
import time
from typing import Any

from ai_api import AIInterface
from chat_client_api import ChatInterface
from discord_client_impl.discord_impl import DiscordGateway
from dotenv import load_dotenv
from kanban_client_api.client import KanbanClient

from .ticket_handlers import execute_tool_call
from .ticket_tools import TICKET_TOOLS_SCHEMA, get_system_prompt_with_tools, validate_tool_call


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


def get_trello_client() -> KanbanClient:
    """Get the Trello client and return it in a generic interface."""
    from trello_client_impl.trello_impl import TrelloClientImpl  # noqa: PLC0415

    token = os.getenv("TRELLO_API_SECRET")  # This is actually the token
    if not token:
        msg = "TRELLO_API_SECRET not set in environment"
        raise ValueError(msg)

    return TrelloClientImpl(token=token)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
]
if all(v not in os.environ for v in required_env_vars):
    sys.exit("Required environment variables are not set.")

ENV = {}
for var in required_env_vars:
    ENV[var] = os.environ[var]

gateway_client: DiscordGateway = DiscordGateway()

chat_client: ChatInterface = get_discord_client()
ai_client: AIInterface = get_claude_client()  # change this between claude/openai!
trello_client: KanbanClient = get_trello_client()

# Get default board and list IDs for ticket operations
# These will be set during initialization
DEFAULT_BOARD_ID = ""
DEFAULT_LIST_ID = ""

bot_id = os.getenv("DISCORD_CLIENT_ID")


async def initialize_trello_defaults() -> tuple[str, str]:
    """Initialize default board and list for Trello operations.

    Creates a default board if none exists, or uses the first available board.
    Creates a default list if none exists in the board.

    Returns:
        Tuple of (board_id, list_id)

    """
    boards = await trello_client.get_boards()

    if not boards:
        # Create a default board if none exists
        logger.info("No boards found, creating default board")
        board = await trello_client.create_board("OSPSD Tickets")
    else:
        # Use the first board
        board = boards[0]
        logger.info(f"Using existing board: {board.name} ({board.id})")

    # Get lists in the board
    lists = await trello_client.get_lists(board.id)

    if not lists:
        # Create a default list if none exists
        logger.info("No lists found, creating default list")
        lst = await trello_client.create_list(board.id, "To Do")
    else:
        # Use the first list
        lst = lists[0]
        logger.info(f"Using existing list: {lst.name} ({lst.id})")

    return board.id, lst.id


# TODO(Andrew): add tests  # noqa: TD003, FIX002
def handle_message(data: dict[str, Any]) -> None:
    """Call this function when a message is sent in the server.

    Args:
        data (dict[str, Any]): The data received from the server

    """
    author_id: str = data["author"]["id"]
    channel_id: str = data["channel_id"]

    # do not respond to messages sent by the bot
    if author_id == bot_id:
        return

    # Get the last message from the user
    user_message = data.get("content", "")

    # Ignore empty messages
    if not user_message or not user_message.strip():
        logger.debug("Ignoring empty message")
        return

    # Generate system prompt with ticket tool definitions
    system_prompt = get_system_prompt_with_tools(DEFAULT_BOARD_ID, DEFAULT_LIST_ID)

    try:
        # Get AI response with structured output using response_schema
        ai_response = ai_client.generate_response(
            user_message,
            system_prompt,
            response_schema=TICKET_TOOLS_SCHEMA,
        )

        # Parse the structured response
        if isinstance(ai_response, str):
            # If AI returned a string, try to parse it as JSON
            try:
                tool_call = json.loads(ai_response)
            except json.JSONDecodeError:
                logger.exception(f"Failed to parse AI response as JSON: {ai_response}")
                chat_client.send_message(
                    channel_id,
                    "❌ Sorry, I couldn't understand that request. Please try again.",
                )
                return
        else:
            tool_call = ai_response

        # Validate the tool call
        is_valid, error_msg = validate_tool_call(tool_call)
        if not is_valid:
            logger.error(f"Invalid tool call: {error_msg}")
            chat_client.send_message(
                channel_id,
                f"❌ Invalid request: {error_msg}",
            )
            return

        # Execute the tool call asynchronously
        result_message = asyncio.run(
            execute_tool_call(
                tool_call,
                trello_client,
                DEFAULT_BOARD_ID,
                DEFAULT_LIST_ID,
            )
        )

        # Send the result back to Discord
        chat_client.send_message(channel_id, result_message)

    except Exception as e:
        logger.exception("Error handling message")
        chat_client.send_message(
            channel_id,
            f"❌ An error occurred: {e}",
        )


# Initialize Trello defaults before starting the gateway
logger.info("Initializing Trello defaults...")
DEFAULT_BOARD_ID, DEFAULT_LIST_ID = asyncio.run(initialize_trello_defaults())
logger.info(f"Trello initialized: board={DEFAULT_BOARD_ID}, list={DEFAULT_LIST_ID}")

gateway_client.subscribe("MESSAGE_CREATE", handle_message)
gateway_client.start()

while True:
    time.sleep(1)
