import os
import sys
import time
from typing import Any

# The implementation of ai_api.AIInterface is in openai_client_service
import ai_api
import chat_client_api
import discord_client_impl  # noqa: F401
import openai_client_service  # noqa: F401
from discord_client_impl.discord_impl import DiscordGateway

required_env_vars = [
    "DISCORD_BOT_TOKEN",
    "DISCORD_CLIENT_ID",
    "DISCORD_CLIENT_SECRET",
    "DISCORD_PUBLIC_KEY",
    "OPENAI_API_KEY",
]
if all(v not in os.environ for v in required_env_vars):
    sys.exit("Required environment variables are not set.")

ENV = {}
for var in required_env_vars:
    ENV[var] = os.environ[var]

gateway_client: DiscordGateway = DiscordGateway()

# It would make sense if we could add a get_client to the api
ai_client: ai_api.AIInterface = ai_api.AIInterface()
chat_client: chat_client_api.ChatInterface = chat_client_api.ChatInterface()

SYS_PROMPT = """Please respond to the last message sent using the context provided.
Please speak only in English and in raw message content (without any dialogue roles or quotation marks) and do not repeat messages that you have previously sent."""

bot_id = os.getenv("DISCORD_CLIENT_ID")

def handle_message(data: dict[str, Any]) -> None:
    author: str = data["author"]["username"]
    author_id: str = data["author"]["id"]
    # NOTE: without activating "Message Content Intent" the bot cannot see the message is it being notified about
    # content: str = data['content']
    channel_id: str = data["channel_id"]

    # do not respond to messages sent by the bot
    if author_id == bot_id:
        return

    msgs = chat_client.get_messages(channel_id, limit=10)
    chat_log = ""
    for msg in reversed(msgs):
        if msg.sender_id == author_id:
            chat_log += author
        elif msg.sender_id == bot_id:
            chat_log += "Bot"
        else:
            chat_log += msg.sender_id
        chat_log += ": " + msg.content + "\n"
    print(chat_log)
    ai_msg = ai_client.generate_response(chat_log, SYS_PROMPT)

    chat_client.send_message(channel_id, ai_msg)

gateway_client.subscribe("MESSAGE_CREATE", handle_message)
gateway_client.start()

while True:
    time.sleep(1)
