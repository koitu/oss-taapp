"""Database package for Discord OAuth2 credential storage.

This package provides SQLAlchemy models and async database management
for storing per-user Discord OAuth2 credentials.

Usage:
    from discord_client_impl.database import get_credential_manager

    manager = get_credential_manager()
    await manager.init_db()

    # Store credentials
    await manager.store_credentials(
        user_id="user123",
        access_token="token...",
        refresh_token="refresh...",
        expires_in=3600
    )

    # Retrieve credentials
    creds = await manager.get_credentials("user123")

"""

from discord_client_impl.database.manager import CredentialManager, get_credential_manager
from discord_client_impl.database.models import Base, DiscordCredential

