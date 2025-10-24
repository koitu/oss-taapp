"""Authentication helper for Discord client with database integration."""

import logging

from discord_client_impl.database import get_credential_manager
from discord_client_impl.discord_impl import DiscordClient

logger = logging.getLogger(__name__)


async def get_client_for_user(user_id: str) -> DiscordClient:
    """Get Discord client for a specific user with database-stored credentials.

    Args:
        user_id: Unique user identifier.

    Returns:
        DiscordClient: Configured Discord client with user's access token.

    Raises:
        ValueError: If no credentials found for user or credentials expired without refresh.

    """
    manager = get_credential_manager()
    credentials = await manager.get_credentials(user_id)

    if not credentials:
        error_msg = f"No credentials found for user: {user_id}"
        raise ValueError(error_msg)

    # Check if token is expired and needs refresh
    if credentials.is_expired():
        logger.info("Access token expired for user %s, attempting refresh", user_id)
        client = DiscordClient()

        try:
            # Refresh the token
            new_token_data = client.refresh_access_token(credentials.refresh_token)

            # Update database with new tokens
            # Note: Some OAuth servers return a new refresh token
            await manager.update_tokens(
                user_id=user_id,
                access_token=new_token_data["access_token"],
                expires_in=new_token_data.get("expires_in", 3600),
                refresh_token=new_token_data.get("refresh_token"),
            )

            # Return client with new token
            return DiscordClient(access_token=new_token_data["access_token"])

        except Exception as e:
            logger.exception("Failed to refresh token for user %s", user_id)
            error_msg = f"Failed to refresh expired token for user {user_id}: {e}"
            raise ValueError(error_msg) from e

    # Token is still valid, use it directly
    return DiscordClient(access_token=credentials.access_token)


async def store_user_credentials(
    user_id: str,
    token_data: dict[str, object],
) -> None:
    """Store OAuth2 credentials for a user in the database.

    Args:
        user_id: Unique user identifier.
        token_data: Token response from OAuth2 server containing:
                   - access_token: OAuth2 access token
                   - refresh_token: OAuth2 refresh token
                   - expires_in: Token expiry in seconds
                   - token_type: Token type (usually "Bearer")
                   - scope: Granted scopes

    """
    manager = get_credential_manager()

    expires_in_value = token_data.get("expires_in", 3600)
    expires_in = int(expires_in_value) if isinstance(expires_in_value, (int, str)) else 3600

    await manager.store_credentials(
        user_id=user_id,
        access_token=str(token_data["access_token"]),
        refresh_token=str(token_data["refresh_token"]),
        expires_in=expires_in,
        token_type=str(token_data.get("token_type", "Bearer")),
        scope=str(token_data.get("scope", "")) if token_data.get("scope") else None,
    )

    logger.info("Stored credentials for user: %s", user_id)


async def delete_user_credentials(user_id: str) -> bool:
    """Delete stored credentials for a user.

    Args:
        user_id: Unique user identifier.

    Returns:
        True if credentials were deleted, False if not found.

    """
    manager = get_credential_manager()
    deleted = await manager.delete_credentials(user_id)

    if deleted:
        logger.info("Deleted credentials for user: %s", user_id)
    else:
        logger.warning("No credentials found to delete for user: %s", user_id)

    return deleted


async def check_user_authenticated(user_id: str) -> bool:
    """Check if a user has valid credentials stored.

    Args:
        user_id: Unique user identifier.

    Returns:
        True if user has credentials (even if expired), False otherwise.

    """
    manager = get_credential_manager()
    credentials = await manager.get_credentials(user_id)
    return credentials is not None
