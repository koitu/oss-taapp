"""Database manager for Discord OAuth2 credentials."""

import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from discord_client_impl.database.models import Base, DiscordCredential

logger = logging.getLogger(__name__)


class CredentialManager:
    """Manage Discord OAuth2 credentials in the database."""

    def __init__(self, database_url: str | None = None) -> None:
        """Initialize credential manager.

        Args:
            database_url: Database connection URL. If None, uses DATABASE_URL env var.
                         Default: sqlite+aiosqlite:///./discord_auth.db

        """
        self.database_url = database_url or os.environ.get(
            "DATABASE_URL", "sqlite+aiosqlite:///./discord_auth.db"
        )
        self.engine: AsyncEngine = create_async_engine(
            self.database_url,
            echo=False,  # Set to True for SQL debugging
        )
        self.async_session_maker: async_sessionmaker[AsyncSession] = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        logger.info("Credential manager initialized with database: %s", self.database_url)

    async def init_db(self) -> None:
        """Initialize database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized")

    async def close(self) -> None:
        """Close database connection."""
        await self.engine.dispose()
        logger.info("Database connection closed")

    @asynccontextmanager
    async def get_session(self) -> AsyncIterator[AsyncSession]:
        """Get async database session as context manager.

        Yields:
            AsyncSession: Database session.

        """
        async with self.async_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def store_credentials(
        self,
        guild_id: str,
        access_token: str,
        refresh_token: str,
        expires_in: int,
        token_type: str = "Bearer",
        scope: str | None = None,
    ) -> DiscordCredential:
        """Store or update Discord credentials for a user.

        Args:
            user_id: Unique user identifier.
            access_token: OAuth2 access token.
            refresh_token: OAuth2 refresh token.
            expires_in: Token expiry time in seconds.
            token_type: Token type (default: Bearer).
            scope: OAuth2 scopes granted.

        Returns:
            DiscordCredential: Stored credential object.
        
        """
        expires_at = datetime.now(UTC) + timedelta(seconds=expires_in)

        async with self.get_session() as session:
            # Check if credential exists
            result = await session.execute(
                select(DiscordCredential).where(DiscordCredential.guild_id == guild_id)
            )
            credential = result.scalar_one_or_none()

            if credential:
                # Update existing credential
                credential.access_token = access_token
                credential.refresh_token = refresh_token
                credential.token_type = token_type
                credential.expires_at = expires_at
                credential.scope = scope
                credential.updated_at = datetime.now(UTC)
                logger.info("Updated credentials for guild: %s", guild_id)
            else:
                # Create new credential
                credential = DiscordCredential(
                    guild_id=guild_id,
                    access_token=access_token,
                    refresh_token=refresh_token,
                    token_type=token_type,
                    expires_at=expires_at,
                    scope=scope,
                )
                session.add(credential)
                logger.info("Created new credentials for guild: %s", guild_id)

            await session.flush()
            await session.refresh(credential)
            return credential

    async def get_credentials(self, guild_id: str) -> DiscordCredential | None:
        """Retrieve credentials for a guild.

        Args:
            guild_id: Unique guild identifier.

        Returns:
            DiscordCredential if found, None otherwise.

        """
        async with self.get_session() as session:
            result = await session.execute(
                select(DiscordCredential).where(DiscordCredential.guild_id == guild_id)
            )
            credential = result.scalar_one_or_none()

            if credential:
                logger.info("Retrieved credentials for guild: %s", guild_id)
            else:
                logger.warning("No credentials found for guild: %s", guild_id)

            return credential

    async def delete_credentials(self, guild_id: str) -> bool:
        """Delete credentials for a guild.

        Args:
            guild_id: Unique guild identifier.

        Returns:
            True if deleted, False if not found.

        """
        async with self.get_session() as session:
            result = await session.execute(
                select(DiscordCredential).where(DiscordCredential.guild_id == guild_id)
            )
            credential = result.scalar_one_or_none()

            if credential:
                await session.delete(credential)
                logger.info("Deleted credentials for guild: %s", guild_id)
                return True

            logger.warning("No credentials to delete for guild: %s", guild_id)
            return False

    async def update_tokens(
        self,
        guild_id: str,
        access_token: str,
        expires_in: int,
        refresh_token: str | None = None,
    ) -> DiscordCredential | None:
        """Update access token after refresh.

        Args:
            guild_id: Unique guild identifier.
            access_token: New OAuth2 access token.
            expires_in: Token expiry time in seconds.
            refresh_token: New refresh token (if provided by OAuth server).

        Returns:
            Updated DiscordCredential if found, None otherwise.

        """
        expires_at = datetime.now(UTC) + timedelta(seconds=expires_in)

        async with self.get_session() as session:
            result = await session.execute(
                select(DiscordCredential).where(DiscordCredential.guild_id == guild_id)
            )
            credential = result.scalar_one_or_none()

            if credential:
                credential.access_token = access_token
                credential.expires_at = expires_at
                if refresh_token:
                    credential.refresh_token = refresh_token
                credential.updated_at = datetime.now(UTC)
                logger.info("Updated tokens for guild: %s", guild_id)
                await session.flush()
                await session.refresh(credential)
                return credential

            logger.warning("No credentials found to update for guild: %s", guild_id)
            return None

    async def list_all_credentials(self) -> list[DiscordCredential]:
        """List all stored credentials.

        Returns:
            List of all DiscordCredential objects.

        """
        async with self.get_session() as session:
            result = await session.execute(select(DiscordCredential))
            credentials = list(result.scalars().all())
            logger.info("Retrieved %d credentials", len(credentials))
            return credentials


# Global credential manager instance
_credential_manager: CredentialManager | None = None


def get_credential_manager(database_url: str | None = None) -> CredentialManager:
    """Get or create the global credential manager instance.

    Args:
        database_url: Database connection URL (only used on first call).

    Returns:
        CredentialManager: Global credential manager instance.

    """
    global _credential_manager
    if _credential_manager is None:
        _credential_manager = CredentialManager(database_url)
    return _credential_manager
