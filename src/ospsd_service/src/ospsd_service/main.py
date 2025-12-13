"""OSPSD Service."""

import logging
import os
import sys
import time
from typing import Any

from ai_api import AIInterface
from chat_client_api import ChatInterface, Message
from discord_client_impl.discord_impl import DiscordGateway
from dotenv import load_dotenv


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
]
if all(v not in os.environ for v in required_env_vars):
    sys.exit("Required environment variables are not set.")

ENV = {}
for var in required_env_vars:
    ENV[var] = os.environ[var]

gateway_client: DiscordGateway = DiscordGateway()

chat_client: ChatInterface = get_discord_client()
ai_client: AIInterface = get_claude_client()  # change this between claude/openai!

SYS_PROMPT = (
    "Please respond to the last message sent using the context provided.\n"
    "Please speak only in English and in raw message content "
    "(without any dialogue roles or quotation marks) "
    "and do not repeat messages that you have previously sent."
)

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

    msgs: list[Message] = chat_client.get_messages(channel_id, limit=10)
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
    ai_msg = ai_client.generate_response(chat_log, SYS_PROMPT)

    # we have not given 'generate_response' a response schema yet
    assert isinstance(ai_msg, str)
    chat_client.send_message(channel_id, ai_msg)


gateway_client.subscribe("MESSAGE_CREATE", handle_message)
gateway_client.start()

while True:
    time.sleep(1)
