"""Discord client implementation with OAuth2 authentication."""

import asyncio
import contextlib
import json
import logging
import os
import threading
from collections.abc import Callable
from enum import IntEnum
from typing import Any

import aiohttp
import httpx
import requests
import websockets
from authlib.integrations.httpx_client import OAuth2Client
from chat_api import ChatInterface, Message

from discord_chat_impl.message_impl import DiscordMessage

logger = logging.getLogger(__name__)


class ChatClientError(Exception):
    """Base exception for all chat client errors."""


class AuthenticationError(ChatClientError):
    """Raised when authentication fails or credentials are invalid."""


class MessageNotFoundError(ChatClientError):
    """Raised when a requested message cannot be found."""


class ChannelNotFoundError(ChatClientError):
    """Raised when a requested channel cannot be found."""


class MessageSendError(ChatClientError):
    """Raised when sending a message fails."""


class MessageDeleteError(ChatClientError):
    """Raised when deleting a message fails."""


class PermissionDeniedError(ChatClientError):
    """Raised when the client lacks permission for an operation."""


class HTTPStatus(IntEnum):
    """HTTP status codes used in Discord API responses."""

    NOT_FOUND = 404


class DiscordGateway:
    """Async Discord Gateway client for receiving real-time events via WebSocket.

    This class manages a persistent WebSocket connection to Discord's Gateway API,
    handling authentication, heartbeat, and event dispatching. It runs in a background
    thread with its own asyncio event loop, allowing it to be used from synchronous code.

    Note:
        The gateway runs as a daemon thread, so it will automatically stop when
        the main program exits. stop() can also be called explicitly for graceful shutdown.

    """

    DISCORD_GATEWAY_URL = "https://discord.com/api/v10/gateway/bot"
    DISPATCH = 0
    HEARTBEAT = 1
    IDENTIFY = 2
    INVALID_SESSION = 9
    HELLO = 10
    HEARTBEAT_ACK = 11

    def __init__(self, token: str | None = None) -> None:
        """Initialize gateway."""
        self.token: str | None = token or os.environ.get("DISCORD_BOT_TOKEN")
        self.ws: websockets.ClientConnection | None = None
        self.sequence: int | None = None
        self.session_id: str | None = None
        self.subscribers: dict[str, list[Callable[[dict[str, Any]], Any]]] = {}
        self.heartbeat_interval: int | None = None
        self._heartbeat_task: asyncio.Task[None] | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self.running: bool = False

    def subscribe(self, event_name: str, callback: Callable[[dict[str, Any]], Any]) -> None:
        """Subscribe a function to a Discord event.

        Args:
            event_name: Discord event type (e.g., 'MESSAGE_CREATE', 'READY')
            callback: Function to call when event occurs (can be sync or async)

        """
        if event_name not in self.subscribers:
            self.subscribers[event_name] = []
        self.subscribers[event_name].append(callback)

    def unsubscribe(self, event_name: str, callback: Callable[[dict[str, Any]], Any]) -> None:
        """Remove a callback from an event."""
        if event_name in self.subscribers:
            self.subscribers[event_name].remove(callback)

    async def _emit(self, event_name: str, data: dict[str, Any]) -> None:
        """Notify all subscribers of an event."""
        if event_name in self.subscribers:
            for callback in self.subscribers[event_name]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        # Run sync callbacks in executor to avoid blocking
                        assert self._loop is not None
                        await self._loop.run_in_executor(None, callback, data)
                except Exception:
                    logger.exception(f"Error in {event_name}")

    async def _heartbeat(self) -> None:
        """Send periodic heartbeat to Discord to keep connection alive.

        Discord will close the connection if heartbeat stops.

        """
        try:
            while self.running:
                assert self.heartbeat_interval is not None
                await asyncio.sleep(self.heartbeat_interval / 1000)
                if self.ws and not self.ws.closed:  # type: ignore[attr-defined]
                    heartbeat = {"op": self.HEARTBEAT, "d": self.sequence}
                    await self.ws.send(json.dumps(heartbeat))
        except asyncio.CancelledError:
            pass

    async def _identify(self) -> None:
        """Tells Discord who you are (your bot token) and what events you want to receive (intents).

        1. Who you are (token authentication).
        2. What permissions/events you want (intents).
        3. Basic client info (for Discord's analytics/debugging).

        """
        identify_payload = {
            "op": self.IDENTIFY,
            "d": {
                "token": self.token,
                "intents": 513,  # 1 (GUILDS) + 512 (GUILD_MESSAGES)
                "properties": {"os": "linux", "browser": "custom_bot", "device": "custom_bot"},
            },
        }
        assert self.ws is not None
        await self.ws.send(json.dumps(identify_payload))

    async def _handle_message(self, message: str) -> None:
        """Process incoming WebSocket messages from Discord."""
        data: dict[str, Any] = json.loads(message)
        op: int = data["op"]  # Opcode determines message type

        # Track sequence for heartbeat and resuming
        if data.get("s"):
            self.sequence = data["s"]

        if op == self.HELLO:  # Discord sends this first
            # Discord tells us how often to heartbeat
            self.heartbeat_interval = data["d"]["heartbeat_interval"]
            self._heartbeat_task = asyncio.create_task(self._heartbeat())

            # Now we identify ourselves
            await self._identify()

        elif op == self.HEARTBEAT_ACK:
            # Discord acknowledges our heartbeat (connection healthy)
            pass

        elif op == self.DISPATCH:  # Actual events we care about
            event_name = data["t"]
            event_data = data["d"]

            # Store session ID for reconnection
            if event_name == "READY":
                self.session_id = event_data["session_id"]
                logger.info(
                    f"Connected as {event_data['user']['username']}"
                    f"#{event_data['user']['discriminator']}"
                )

            # Notify subscribers
            await self._emit(event_name, event_data)

        elif op == self.INVALID_SESSION:  # Invalid Session
            logger.info("Invalid session, reconnecting...")
            await asyncio.sleep(5)
            await self._identify()

    async def _connect_and_listen(self) -> None:
        """Perform WebSocket connection loop."""
        # Get the Gateway URL from Discord API
        async with (
            aiohttp.ClientSession() as session,
            session.get(
                self.DISCORD_GATEWAY_URL, headers={"Authorization": f"Bot {self.token}"}
            ) as response,
        ):
            if response.status != requests.codes.ok:
                raise ConnectionError(f"Failed to get gateway: {response.status}")
            gateway_data = await response.json()
            gateway_url = gateway_data["url"]

        # Connect to the WebSocket
        try:
            async with websockets.connect(
                f"{gateway_url}?v=10&encoding=json",
                max_size=None,  # Remove message size limit
            ) as ws:
                self.ws = ws
                logger.info(f"Connected to Discord Gateway: {gateway_url}")

                # Listen for messages until connection closes
                async for message in ws:
                    if isinstance(message, bytes):
                        await self._handle_message(message.decode())
                    else:
                        await self._handle_message(message)

        except websockets.exceptions.ConnectionClosed as e:
            logger.info(f"WebSocket closed: {e}")
        except Exception:
            logger.exception("WebSocket error")
        finally:
            # Cleanup
            if self._heartbeat_task:
                self._heartbeat_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await self._heartbeat_task

    async def _run_forever(self) -> None:
        """Keep reconnecting if connection drops."""
        while self.running:
            try:
                await self._connect_and_listen()
            except ConnectionError:
                logger.exception("Connection error")

            if self.running:
                logger.info("Reconnecting in 5 seconds...")
                await asyncio.sleep(5)

    def _run_event_loop(self) -> None:
        """Run the asyncio event loop in a thread."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._run_forever())

    def start(self) -> None:
        """Start the gateway connection in a background thread."""
        if self.running:
            return

        self.running = True
        self._thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the gateway connection."""
        self.running = False

        if self._loop and self.ws:
            # Schedule close on the event loop
            asyncio.run_coroutine_threadsafe(self.ws.close(), self._loop)

        if self._thread:
            self._thread.join(timeout=5)


class DiscordClient(ChatInterface):
    """Discord implementation of chat client with OAuth2 support."""

    DISCORD_API_BASE = "https://discord.com/api/v10"
    OAUTH2_AUTHORIZE_URL = "https://discord.com/api/oauth2/authorize"
    OAUTH2_TOKEN_URL = "https://discord.com/api/oauth2/token"

    def __init__(
        self,
        access_token: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        redirect_uri: str | None = None,
        token_type: str | None = None,
    ) -> None:
        """Initialize Discord client with OAuth2 credentials.

        Args:
            access_token: Discord OAuth2 access token (if already authenticated).
            client_id: Discord application client ID (for OAuth flow).
            client_secret: Discord application client secret (for OAuth flow).
            redirect_uri: OAuth2 redirect URI (for OAuth flow).
            token_type: Authorization header token type to use when sending requests
                (e.g. "Bot" or "Bearer"). If not provided, the environment
                variable `DISCORD_DEFAULT_TOKEN_TYPE` is consulted or defaults
                to "Bot" for backwards compatibility.

        """
        self.client_id = client_id or os.environ.get("DISCORD_CLIENT_ID")
        self.client_secret = client_secret or os.environ.get("DISCORD_CLIENT_SECRET")
        self.redirect_uri = redirect_uri or os.environ.get(
            "DISCORD_REDIRECT_URI", "http://localhost:8001/auth/callback"
        )
        self.access_token = access_token or os.environ.get("DISCORD_BOT_TOKEN")

        # Create HTTP client
        # Token type controls the Authorization header verb (Bearer vs Bot)
        # If not provided, default to Bot for backwards compatibility with previous changes.
        self.token_type = token_type or os.environ.get("DISCORD_DEFAULT_TOKEN_TYPE", "Bot")

        # Create HTTP client
        self._http_client: httpx.Client = httpx.Client(
            base_url=self.DISCORD_API_BASE,
            headers={"Authorization": f"{self.token_type} {self.access_token}"},
            timeout=30.0,
        )

        logger.info("Discord client initialized")

    def _get_authorization_url(self, state: str | None = None) -> tuple[str, str]:
        """Generate OAuth2 authorization URL.

        Args:
            state: Optional state parameter for CSRF protection.

        Returns:
            Tuple of (authorization_url, state).

        Raises:
            ValueError: If client_id is not configured.

        """
        if not self.client_id:
            raise ValueError("DISCORD_CLIENT_ID not configured")

        oauth_client = OAuth2Client(
            client_id=self.client_id,
            redirect_uri=self.redirect_uri,
        )

        # Discord requires specific scopes for reading/sending messages.
        # Requested scopes: identity, guilds, messages.read and bot.
        scopes = ["identify", "guilds", "messages.read", "bot"]

        # For bot installs, request the specific permission bits the bot needs.
        # Use named constants for clarity (lowercase to satisfy local variable naming):
        # view_channel, send_messages, read_message_history.
        view_channel = 0x00000400  # 1024
        send_messages = 0x00000800  # 2048
        read_message_history = 0x00010000  # 65536

        permissions = view_channel | send_messages | read_message_history  # = 68608

        # Integration type: Guild Install (this authorizes the bot for a guild).
        # Build authorization URL. Include explicit response_type to make intent clear.
        authorization_url, state_value = oauth_client.create_authorization_url(
            self.OAUTH2_AUTHORIZE_URL,
            scope=" ".join(scopes),
            state=state,
            permissions=permissions,
            response_type="code",
            prompt="consent",
        )

        return authorization_url, state_value

    def _exchange_code_for_token(self, code: str) -> dict[str, Any]:
        """Exchange authorization code for access token.

        Args:
            code: Authorization code from OAuth callback.

        Returns:
            Token response containing access_token, refresh_token, etc.

        Raises:
            ValueError: If credentials are not configured or exchange fails.

        """
        if not self.client_id or not self.client_secret:
            raise ValueError("DISCORD_CLIENT_ID and DISCORD_CLIENT_SECRET required")

        oauth_client = OAuth2Client(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
        )

        try:
            token = oauth_client.fetch_token(
                self.OAUTH2_TOKEN_URL,
                code=code,
                grant_type="authorization_code",
            )
            self.access_token = token.get("access_token")  # type: ignore[assignment]
            self._update_http_client()
            return dict(token)  # type: ignore[arg-type]
        except Exception as e:
            logger.exception("Failed to exchange code for token")
            raise ValueError(f"Token exchange failed: {e}") from e

    def _refresh_access_token(self, refresh_token: str) -> dict[str, Any]:
        """Refresh the access token using a refresh token.

        Args:
            refresh_token: The refresh token from previous authentication.

        Returns:
            New token response.

        Raises:
            ValueError: If credentials are not configured or refresh fails.

        """
        if not self.client_id or not self.client_secret:
            raise ValueError("DISCORD_CLIENT_ID and DISCORD_CLIENT_SECRET required")

        oauth_client = OAuth2Client(
            client_id=self.client_id,
            client_secret=self.client_secret,
        )

        try:
            token = oauth_client.refresh_token(
                self.OAUTH2_TOKEN_URL,
                refresh_token=refresh_token,
                grant_type="refresh_token",
            )
            self.access_token = token.get("access_token")  # type: ignore[assignment]
            self._update_http_client()
            return dict(token)  # type: ignore[arg-type]
        except Exception as e:
            logger.exception("Failed to refresh token")
            raise ValueError(f"Token refresh failed: {e}") from e

    def _update_http_client(self) -> None:
        """Update HTTP client with new access token."""
        if self.access_token:
            self._http_client.close()
            self._http_client = httpx.Client(
                base_url=self.DISCORD_API_BASE,
                headers={"Authorization": f"{self.token_type} {self.access_token}"},
                timeout=30.0,
            )

    def get_message(self, channel_id: str, message_id: str) -> Message:
        """Retrieve a specific message from a channel.

        Args:
            channel_id: The ID of the channel containing the message.
            message_id: The ID of the message to retrieve.

        Returns:
            Message: The requested message.

        Raises:
            AuthenticationError: If not authenticated.
            MessageNotFoundError: If the message is not found.
            ChatClientError: If the request fails for other reasons.

        """
        try:
            response = self._http_client.get(f"/channels/{channel_id}/messages/{message_id}")
            response.raise_for_status()
            return DiscordMessage(response.json())
        except httpx.HTTPStatusError as e:
            if e.response.status_code == HTTPStatus.NOT_FOUND:
                raise MessageNotFoundError(
                    f"Message {message_id} not found in channel {channel_id}"
                ) from e
            logger.exception("Failed to get message")
            raise MessageNotFoundError(f"Failed to retrieve message: {e}") from e
        except Exception as e:
            logger.exception("Failed to get message")
            raise MessageNotFoundError(f"Failed to retrieve message: {e}") from e

    def get_messages(self, channel_id: str, limit: int = 10) -> list[Message]:
        """Retrieve recent messages from a channel.

        Args:
            channel_id: The ID of the channel to retrieve messages from.
            limit: Maximum number of messages to retrieve (default: 10, max: 100).

        Returns:
            list[Message]: An iterator of messages from the channel.

        """
        # Discord API limits to 100 messages per request
        limit = min(limit, 100)

        try:
            response = self._http_client.get(
                f"/channels/{channel_id}/messages",
                params={"limit": limit},
            )
            response.raise_for_status()
            messages = response.json()
            return [DiscordMessage(msg_data) for msg_data in messages]

        except httpx.HTTPStatusError as e:
            logger.exception("Failed to get messages")
            raise ValueError(f"Failed to retrieve messages: {e}") from e
        except Exception as e:
            logger.exception("Failed to get messages")
            raise ValueError(f"Failed to retrieve messages: {e}") from e

    def send_message(self, channel_id: str, content: str) -> bool:
        """Send a message to a channel.

        Args:
            channel_id: The ID of the channel to send the message to.
            content: The text content of the message.

        Returns:
            bool: True if the message was successfully sent.

        Raises:
            AuthenticationError: If not authenticated.
            MessageSendError: If the message could not be sent.

        """
        if not content.strip():
            raise MessageSendError("Message content cannot be empty")

        try:
            response = self._http_client.post(
                f"/channels/{channel_id}/messages",
                json={"content": content},
            )
            response.raise_for_status()
            return True
        except httpx.HTTPStatusError as e:
            logger.exception("Failed to send message")
            raise MessageSendError(f"Failed to send message: {e}") from e
        except Exception as e:
            logger.exception("Failed to send message")
            raise MessageSendError(f"Failed to send message: {e}") from e

    def delete_message(self, channel_id: str, message_id: str) -> bool:
        """Delete a message from a channel.

        Args:
            channel_id: The ID of the channel containing the message.
            message_id: The ID of the message to delete.

        Returns:
            bool: True if the message was successfully deleted.

        Raises:
            AuthenticationError: If not authenticated.
            MessageNotFoundError: If the message does not exist.
            MessageDeleteError: If deletion fails for other reasons.

        """
        try:
            response = self._http_client.delete(f"/channels/{channel_id}/messages/{message_id}")
            response.raise_for_status()
            return True
        except httpx.HTTPStatusError as e:
            if e.response.status_code == HTTPStatus.NOT_FOUND:
                raise MessageNotFoundError(
                    f"Message {message_id} not found in channel {channel_id}"
                ) from e
            logger.exception("Failed to delete message")
            raise MessageDeleteError(f"Failed to delete message: {e}") from e
        except Exception as e:
            logger.exception("Failed to delete message")
            raise MessageDeleteError(f"Failed to delete message: {e}") from e

    def close(self) -> None:
        """Close the HTTP client."""
        self._http_client.close()

    def __enter__(self) -> "DiscordClient":
        """Context manager entry."""
        return self

    def __exit__(self, *args: object) -> None:
        """Context manager exit."""
        self.close()

    def leave_guild(self, guild_id: str) -> bool:
        """Make the bot leave a guild.

        Returns True on success, raises an exception on failure.
        """
        # For bot token clients, DELETE /users/@me/guilds/{guild_id} removes the
        # current user (bot) from the guild.
        try:
            response = self._http_client.delete(f"/users/@me/guilds/{guild_id}")
            response.raise_for_status()
            return True
        except httpx.HTTPStatusError as e:
            logger.exception("Failed to leave guild %s", guild_id)
            raise ValueError(f"Failed to leave guild {guild_id}: {e}") from e
        except Exception as e:
            logger.exception("Failed to leave guild %s", guild_id)
            raise ValueError(f"Failed to leave guild {guild_id}: {e}") from e
