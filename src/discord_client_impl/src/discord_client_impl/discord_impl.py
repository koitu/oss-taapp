"""Discord client implementation with OAuth2 authentication."""

import logging
import os
from collections.abc import Iterator
from typing import Any

import httpx
from authlib.integrations.httpx_client import OAuth2Client
from chat_client_api.client import Client
from chat_client_api.message import Channel, ChatMessage

from discord_client_impl.message_impl import DiscordChannel, DiscordMessage

logger = logging.getLogger(__name__)


class DiscordClient(Client):
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
    ) -> None:
        """Initialize Discord client with OAuth2 credentials.

        Args:
            access_token: Discord OAuth2 access token (if already authenticated).
            client_id: Discord application client ID (for OAuth flow).
            client_secret: Discord application client secret (for OAuth flow).
            redirect_uri: OAuth2 redirect URI (for OAuth flow).

        """
        self.client_id = client_id or os.environ.get("DISCORD_CLIENT_ID")
        self.client_secret = client_secret or os.environ.get("DISCORD_CLIENT_SECRET")
        self.redirect_uri = redirect_uri or os.environ.get(
            "DISCORD_REDIRECT_URI", "http://localhost:8001/auth/callback"
        )
        self.access_token = access_token

        # Create HTTP client
        if self.access_token:
            self._http_client: httpx.Client = httpx.Client(
                base_url=self.DISCORD_API_BASE,
                headers={"Authorization": f"Bearer {self.access_token}"},
                timeout=30.0,
            )
        else:
            self._http_client = httpx.Client(
                base_url=self.DISCORD_API_BASE,
                timeout=30.0,
            )

        logger.info("Discord client initialized")

    def get_authorization_url(self, state: str | None = None) -> tuple[str, str]:
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

        # Discord requires specific scopes for reading/sending messages
        scopes = ["identify", "guilds", "messages.read"]

        authorization_url, state_value = oauth_client.create_authorization_url(
            self.OAUTH2_AUTHORIZE_URL,
            scope=" ".join(scopes),
            state=state,
        )

        return authorization_url, state_value

    def exchange_code_for_token(self, code: str) -> dict[str, Any]:
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

    def refresh_access_token(self, refresh_token: str) -> dict[str, Any]:
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
                headers={"Authorization": f"Bearer {self.access_token}"},
                timeout=30.0,
            )

    def _ensure_authenticated(self) -> None:
        """Ensure client has valid access token.

        Raises:
            ValueError: If not authenticated.

        """
        if not self.access_token:
            raise ValueError("Not authenticated. Call exchange_code_for_token first.")

    def get_message(self, channel_id: str, message_id: str) -> ChatMessage:
        """Retrieve a specific message from a channel.

        Args:
            channel_id: The ID of the channel containing the message.
            message_id: The ID of the message to retrieve.

        Returns:
            ChatMessage: The requested message.

        Raises:
            ValueError: If the message is not found or request fails.

        """
        self._ensure_authenticated()

        try:
            response = self._http_client.get(f"/channels/{channel_id}/messages/{message_id}")
            response.raise_for_status()
            return DiscordMessage(response.json())
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ValueError(f"Message {message_id} not found in channel {channel_id}") from e
            logger.exception("Failed to get message")
            raise ValueError(f"Failed to retrieve message: {e}") from e
        except Exception as e:
            logger.exception("Failed to get message")
            raise ValueError(f"Failed to retrieve message: {e}") from e

    def get_messages(self, channel_id: str, max_results: int = 10) -> Iterator[ChatMessage]:
        """Retrieve recent messages from a channel.

        Args:
            channel_id: The ID of the channel to retrieve messages from.
            max_results: Maximum number of messages to retrieve (default: 10, max: 100).

        Returns:
            Iterator[ChatMessage]: An iterator of messages from the channel.

        """
        self._ensure_authenticated()

        # Discord API limits to 100 messages per request
        limit = min(max_results, 100)

        try:
            response = self._http_client.get(
                f"/channels/{channel_id}/messages",
                params={"limit": limit},
            )
            response.raise_for_status()
            messages = response.json()

            for msg_data in messages:
                yield DiscordMessage(msg_data)

        except httpx.HTTPStatusError as e:
            logger.exception("Failed to get messages")
            raise ValueError(f"Failed to retrieve messages: {e}") from e
        except Exception as e:
            logger.exception("Failed to get messages")
            raise ValueError(f"Failed to retrieve messages: {e}") from e

    def send_message(self, channel_id: str, content: str) -> ChatMessage:
        """Send a message to a channel.

        Args:
            channel_id: The ID of the channel to send the message to.
            content: The text content of the message.

        Returns:
            ChatMessage: The sent message.

        Raises:
            ValueError: If the message could not be sent.

        """
        self._ensure_authenticated()

        if not content.strip():
            raise ValueError("Message content cannot be empty")

        try:
            response = self._http_client.post(
                f"/channels/{channel_id}/messages",
                json={"content": content},
            )
            response.raise_for_status()
            return DiscordMessage(response.json())
        except httpx.HTTPStatusError as e:
            logger.exception("Failed to send message")
            raise ValueError(f"Failed to send message: {e}") from e
        except Exception as e:
            logger.exception("Failed to send message")
            raise ValueError(f"Failed to send message: {e}") from e

    def delete_message(self, channel_id: str, message_id: str) -> bool:
        """Delete a message from a channel.

        Args:
            channel_id: The ID of the channel containing the message.
            message_id: The ID of the message to delete.

        Returns:
            bool: True if the message was successfully deleted, False otherwise.

        """
        self._ensure_authenticated()

        try:
            response = self._http_client.delete(f"/channels/{channel_id}/messages/{message_id}")
            response.raise_for_status()
            return True
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning("Message %s not found in channel %s", message_id, channel_id)
                return False
            logger.exception("Failed to delete message")
            return False
        except Exception:
            logger.exception("Failed to delete message")
            return False

    def get_channels(self) -> Iterator[Channel]:
        """Retrieve all accessible channels.

        Note: This returns DM channels for the authenticated user.
        For guild channels, use get_guild_channels().

        Returns:
            Iterator[Channel]: An iterator of available DM channels.

        """
        self._ensure_authenticated()

        try:
            # Get user's DM channels
            response = self._http_client.get("/users/@me/channels")
            response.raise_for_status()
            channels = response.json()

            for channel_data in channels:
                yield DiscordChannel(channel_data)

        except httpx.HTTPStatusError as e:
            logger.exception("Failed to get channels")
            raise ValueError(f"Failed to retrieve channels: {e}") from e
        except Exception as e:
            logger.exception("Failed to get channels")
            raise ValueError(f"Failed to retrieve channels: {e}") from e

    def get_channel(self, channel_id: str) -> Channel:
        """Retrieve information about a specific channel.

        Args:
            channel_id: The ID of the channel to retrieve.

        Returns:
            Channel: The requested channel.

        Raises:
            ValueError: If the channel is not found.

        """
        self._ensure_authenticated()

        try:
            response = self._http_client.get(f"/channels/{channel_id}")
            response.raise_for_status()
            return DiscordChannel(response.json())
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ValueError(f"Channel {channel_id} not found") from e
            logger.exception("Failed to get channel")
            raise ValueError(f"Failed to retrieve channel: {e}") from e
        except Exception as e:
            logger.exception("Failed to get channel")
            raise ValueError(f"Failed to retrieve channel: {e}") from e

    def close(self) -> None:
        """Close the HTTP client."""
        self._http_client.close()

    def __enter__(self) -> "DiscordClient":
        """Context manager entry."""
        return self

    def __exit__(self, *args: object) -> None:
        """Context manager exit."""
        self.close()
