"""OSPSD Service."""

import asyncio
import contextlib
import json
import logging
import os
import sys
import time
from typing import Any

from ai_api import AIInterface
from chat_client_api import ChatInterface, Message
from tickets_api import TicketInterface, Ticket
from discord_client_impl.discord_impl import DiscordGateway
from dotenv import load_dotenv

# from ospsd_service.ticket_handlers import execute_tool_call
from ospsd_service.ticket_tools import TICKET_TOOLS_SCHEMA, get_system_prompt_with_tools, validate_tool_call


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
    from trello_ticket_impl import TrelloTicketClientImpl # noqa: PLC0415

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


# TODO(Andrew): add tests  # noqa: TD003, FIX002
def handle_message(data: dict[str, Any]) -> None:
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

    # TODO: change the prompt so that it can also look at the previous messages (but bias towards last message)
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

    if ai_response['action'] == 'chat_response':
        chat_client.send_message(channel_id, ai_response['parameters']['message'])
    elif ai_response['action'] == 'create_ticket':
        ticket = ticket_client.create_ticket(
            ai_response['parameters']['title'],
            ai_response['parameters']['description'],
            ai_response['parameters'].get('assignee', None),
        )
        chat_client.send_message(channel_id, "ticket created: " + ticket.title)

    elif ai_response['action'] == 'list_tickets':
        tickets = ticket_client.search_tickets()
        res = ""
        for ticket in reversed(tickets):
            res += ticket.title + ": " + ticket.description + "\n"
        chat_client.send_message(channel_id, res)
    else:
        logger.info("???")


    # try:
    #     # Get AI response with structured output using response_schema
    #     ai_response = ai_client.generate_response(
    #         user_message,
    #         system_prompt,
    #         response_schema=TICKET_TOOLS_SCHEMA,
    #     )
    #
    #     # Parse the structured response
    #     if isinstance(ai_response, str):
    #         # If AI returned a string, try to parse it as JSON
    #         try:
    #             tool_call = json.loads(ai_response)
    #         except json.JSONDecodeError:
    #             logger.exception(f"Failed to parse AI response as JSON: {ai_response}")
    #             chat_client.send_message(
    #                 channel_id,
    #                 "❌ Sorry, I couldn't understand that request. Please try again.",
    #             )
    #             return
    #     else:
    #         tool_call = ai_response
    #
    #     # Validate the tool call
    #     is_valid, error_msg = validate_tool_call(tool_call)
    #     if not is_valid:
    #         logger.error(f"Invalid tool call: {error_msg}")
    #         chat_client.send_message(
    #             channel_id,
    #             f"❌ Invalid request: {error_msg}",
    #         )
    #         return
    #
    #     # Execute the tool call asynchronously
    #     result_message = asyncio.run(
    #         execute_tool_call(
    #             tool_call,
    #             trello_client,
    #             DEFAULT_BOARD_ID,
    #             DEFAULT_LIST_ID,
    #         )
    #     )
    #
    #     # Send the result back to Discord
    #     chat_client.send_message(channel_id, result_message)
    #
    # except Exception as e:
    #     logger.exception("Error handling message")
    #     chat_client.send_message(
    #         channel_id,
    #         f"❌ An error occurred: {e}",
    #     )

gateway_client.subscribe("MESSAGE_CREATE", handle_message)
gateway_client.start()

while True:
    time.sleep(1)
