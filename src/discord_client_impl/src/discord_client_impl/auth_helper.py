"""Authentication helper for Discord client with database integration."""

import logging

from discord_client_impl.database import get_credential_manager
from discord_client_impl.discord_impl import DiscordClient

logger = logging.getLogger(__name__)


async def get_client_for_user(guild_id: str) -> DiscordClient:
    """Get Discord client for a specific guild with database-stored credentials.

    Args:
        guild_id: Unique guild identifier.

    Returns:
        DiscordClient: Configured Discord client with guild's access token.

    Raises:
        ValueError: If no credentials found for guild or credentials expired without refresh.

    """
    manager = get_credential_manager()
    credentials = await manager.get_credentials(guild_id)

    if not credentials:
        error_msg = f"No credentials found for guild: {guild_id}"
        raise ValueError(error_msg)

    # If the stored credential exists but is not a Bot token, prefer using
    # the application bot token (DISCORD_BOT_TOKEN) for guild-level operations
    # because OAuth access tokens are not valid as bot tokens.
    app_bot_token = None
    try:
        import os

        app_bot_token = os.environ.get("DISCORD_BOT_TOKEN")
    except Exception:
        app_bot_token = None

    if credentials and getattr(credentials, "token_type", "").lower() != "bot" and app_bot_token:
        logger.info(
            "Stored token for guild %s is not a bot token; falling back to application bot token",
            guild_id,
        )
        return DiscordClient(access_token=app_bot_token, token_type="Bot")

    # Check if token is expired and needs refresh
    if credentials.is_expired():
        logger.info("Access token expired for guild %s, attempting refresh", guild_id)
        client = DiscordClient()

        try:
            # Refresh the token
            new_token_data = client._refresh_access_token(credentials.refresh_token)

            # Update database with new tokens
            # Note: Some OAuth servers return a new refresh token
            await manager.update_tokens(
                guild_id=guild_id,
                access_token=new_token_data["access_token"],
                expires_in=new_token_data.get("expires_in", 3600),
                refresh_token=new_token_data.get("refresh_token"),
            )

            # Return client with new token and use returned token_type when present
            return DiscordClient(
                access_token=new_token_data["access_token"],
                token_type=new_token_data.get("token_type", "Bearer"),
            )

        except Exception as e:
            logger.exception("Failed to refresh token for guild %s", guild_id)
            error_msg = f"Failed to refresh expired token for guild {guild_id}: {e}"
            raise ValueError(error_msg) from e

    # Token is still valid, use it directly. Respect the stored token_type.
    return DiscordClient(access_token=credentials.access_token, token_type=getattr(credentials, "token_type", "Bearer"))


async def get_bot_client_for_guild(guild_id: str) -> DiscordClient:
    """Return a DiscordClient configured with a bot token suitable for guild-level operations.

    Priority:
    1. Use application bot token from environment variable DISCORD_BOT_TOKEN if present.
    2. Otherwise, use stored credentials for the guild if they exist and are token_type 'bot'.
    3. Otherwise raise ValueError.

    """
    # 1) application-level bot token (recommended for bot installs)
    import os

    app_bot_token = os.environ.get("DISCORD_BOT_TOKEN")
    if app_bot_token:
        return DiscordClient(access_token=app_bot_token, token_type="Bot")

    # 2) fallback to stored credentials if they are bot tokens
    manager = get_credential_manager()
    credentials = await manager.get_credentials(guild_id)
    if credentials and getattr(credentials, "token_type", "").lower() == "bot":
        return DiscordClient(access_token=credentials.access_token, token_type="Bot")

    raise ValueError("No bot token available for guild. Set DISCORD_BOT_TOKEN or install the bot to the guild.")


async def store_user_credentials(
    guild_id: str,
    token_data: dict[str, object],
) -> None:
    """Store OAuth2 credentials for a guild in the database.

    Args:
        guild_id: Unique guild identifier.
        token_data: Token response from OAuth2 server containing:
                   - access_token: OAuth2 access token
                   - refresh_token: OAuth2 refresh token
                   - expires_in: Token expiry in seconds
                   - token_type: Token type (usually "Bot")
                   - scope: Granted scopes

    """
    manager = get_credential_manager()

    expires_in_value = token_data.get("expires_in", 3600)
    expires_in = int(expires_in_value) if isinstance(expires_in_value, (int, str)) else 3600

    await manager.store_credentials(
        guild_id=guild_id,
        access_token=str(token_data["access_token"]),
        refresh_token=str(token_data["refresh_token"]),
        expires_in=expires_in,
        token_type=str(token_data.get("token_type", "Bearer")),
        scope=str(token_data.get("scope", "")) if token_data.get("scope") else None,
    )

    logger.info("Stored credentials for guild: %s", guild_id)


async def delete_user_credentials(guild_id: str) -> bool:
    """Delete stored credentials for a guild.

    Args:
        guild_id: Unique guild identifier.

    Returns:
        True if credentials were deleted, False if not found.

    """
    manager = get_credential_manager()
    deleted = await manager.delete_credentials(guild_id)

    if deleted:
        logger.info("Deleted credentials for guild: %s", guild_id)
    else:
        logger.warning("No credentials found to delete for guild: %s", guild_id)

    return deleted


async def check_user_authenticated(guild_id: str) -> bool:
    """Check if a guild has valid credentials stored.

    Args:
        guild_id: Unique guild identifier.

    Returns:
        True if guild has credentials (even if expired), False otherwise.

    """
    manager = get_credential_manager()
    credentials = await manager.get_credentials(guild_id)
    return credentials is not None
