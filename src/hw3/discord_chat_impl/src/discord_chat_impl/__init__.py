"""Discord client implementation with OAuth2 authentication.

This module provides a Discord implementation of the chat_client_api contract.
It uses OAuth2 for authentication and the Discord REST API for all operations.

Usage:
    import discord_chat_impl  # Side-effect: registers Discord as implementation
    import chat_client_api

    # Get client for a specific user (will use stored credentials)
    client = chat_client_api.get_client(user_id="user123")

    # Or create client directly with access token
    from discord_chat_impl import DiscordClient
    client = DiscordClient(access_token="your_token")

"""

from discord_chat_impl.discord_impl import AuthenticationError as AuthenticationError
from discord_chat_impl.discord_impl import ChannelNotFoundError as ChannelNotFoundError
from discord_chat_impl.discord_impl import ChatClientError as ChatClientError
from discord_chat_impl.discord_impl import DiscordClient as DiscordClient
from discord_chat_impl.discord_impl import DiscordGateway as DiscordGateway
from discord_chat_impl.discord_impl import MessageDeleteError as MessageDeleteError
from discord_chat_impl.discord_impl import MessageNotFoundError as MessageNotFoundError
from discord_chat_impl.discord_impl import MessageSendError as MessageSendError
from discord_chat_impl.discord_impl import PermissionDeniedError as PermissionDeniedError
from discord_chat_impl.message_impl import DiscordMessage as DiscordMessage
