"""Tests for database credential storage."""

from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest
import pytest_asyncio

from discord_client_impl.database import CredentialManager

# Test constants
EXPECTED_CREDENTIAL_COUNT = 2  # Expected number of credentials in multi-user test


@pytest_asyncio.fixture
async def db_manager() -> AsyncIterator[CredentialManager]:
    """Create test database manager with in-memory SQLite."""
    manager = CredentialManager(database_url="sqlite+aiosqlite:///:memory:")
    await manager.init_db()
    yield manager
    await manager.close()


@pytest.mark.asyncio
async def test_store_new_credentials(db_manager: CredentialManager) -> None:
    """Test storing new credentials."""
    credential = await db_manager.store_credentials(
        user_id="user123",
        access_token="access_token_value",
        refresh_token="refresh_token_value",
        expires_in=3600,
        scope="identify guilds",
    )

    assert credential.user_id == "user123"
    assert credential.access_token == "access_token_value"
    assert credential.refresh_token == "refresh_token_value"
    assert credential.scope == "identify guilds"
    assert not credential.is_expired()


@pytest.mark.asyncio
async def test_update_existing_credentials(db_manager: CredentialManager) -> None:
    """Test updating existing credentials."""
    # Store initial credentials
    await db_manager.store_credentials(
        user_id="user123",
        access_token="old_token",
        refresh_token="old_refresh",
        expires_in=3600,
    )

    # Update with new credentials
    updated = await db_manager.store_credentials(
        user_id="user123",
        access_token="new_token",
        refresh_token="new_refresh",
        expires_in=7200,
    )

    assert updated.access_token == "new_token"
    assert updated.refresh_token == "new_refresh"


@pytest.mark.asyncio
async def test_get_credentials(db_manager: CredentialManager) -> None:
    """Test retrieving credentials."""
    # Store credentials
    await db_manager.store_credentials(
        user_id="user123",
        access_token="token",
        refresh_token="refresh",
        expires_in=3600,
    )

    # Retrieve credentials
    retrieved = await db_manager.get_credentials("user123")

    assert retrieved is not None
    assert retrieved.user_id == "user123"
    assert retrieved.access_token == "token"


@pytest.mark.asyncio
async def test_get_nonexistent_credentials(db_manager: CredentialManager) -> None:
    """Test retrieving credentials for non-existent user."""
    retrieved = await db_manager.get_credentials("nonexistent")
    assert retrieved is None


@pytest.mark.asyncio
async def test_delete_credentials(db_manager: CredentialManager) -> None:
    """Test deleting credentials."""
    # Store credentials
    await db_manager.store_credentials(
        user_id="user123",
        access_token="token",
        refresh_token="refresh",
        expires_in=3600,
    )

    # Delete credentials
    deleted = await db_manager.delete_credentials("user123")
    assert deleted is True

    # Verify deleted
    retrieved = await db_manager.get_credentials("user123")
    assert retrieved is None


@pytest.mark.asyncio
async def test_delete_nonexistent_credentials(db_manager: CredentialManager) -> None:
    """Test deleting non-existent credentials."""
    deleted = await db_manager.delete_credentials("nonexistent")
    assert deleted is False


@pytest.mark.asyncio
async def test_update_tokens(db_manager: CredentialManager) -> None:
    """Test updating tokens after refresh."""
    # Store initial credentials
    await db_manager.store_credentials(
        user_id="user123",
        access_token="old_token",
        refresh_token="old_refresh",
        expires_in=3600,
    )

    # Update tokens
    updated = await db_manager.update_tokens(
        user_id="user123",
        access_token="new_access_token",
        expires_in=7200,
        refresh_token="new_refresh_token",
    )

    assert updated is not None
    assert updated.access_token == "new_access_token"
    assert updated.refresh_token == "new_refresh_token"


@pytest.mark.asyncio
async def test_update_tokens_nonexistent_user(db_manager: CredentialManager) -> None:
    """Test updating tokens for non-existent user."""
    updated = await db_manager.update_tokens(
        user_id="nonexistent",
        access_token="token",
        expires_in=3600,
    )
    assert updated is None


@pytest.mark.asyncio
async def test_list_all_credentials(db_manager: CredentialManager) -> None:
    """Test listing all credentials."""
    # Store multiple credentials
    await db_manager.store_credentials(
        user_id="user1",
        access_token="token1",
        refresh_token="refresh1",
        expires_in=3600,
    )
    await db_manager.store_credentials(
        user_id="user2",
        access_token="token2",
        refresh_token="refresh2",
        expires_in=3600,
    )

    # List all
    all_creds = await db_manager.list_all_credentials()

    assert len(all_creds) == EXPECTED_CREDENTIAL_COUNT
    user_ids = {cred.user_id for cred in all_creds}
    assert user_ids == {"user1", "user2"}


@pytest.mark.asyncio
async def test_credential_is_expired(db_manager: CredentialManager) -> None:
    """Test checking if credential is expired."""
    # Store expired credential (expires in -1 seconds, i.e., already expired)
    credential = await db_manager.store_credentials(
        user_id="user123",
        access_token="token",
        refresh_token="refresh",
        expires_in=-1,
    )

    assert credential.is_expired() is True


@pytest.mark.asyncio
async def test_credential_not_expired(db_manager: CredentialManager) -> None:
    """Test checking if credential is not expired."""
    credential = await db_manager.store_credentials(
        user_id="user123",
        access_token="token",
        refresh_token="refresh",
        expires_in=3600,
    )

    assert credential.is_expired() is False


@pytest.mark.asyncio
async def test_credential_to_dict(db_manager: CredentialManager) -> None:
    """Test converting credential to dictionary."""
    credential = await db_manager.store_credentials(
        user_id="user123",
        access_token="token",
        refresh_token="refresh",
        expires_in=3600,
        scope="identify",
    )

    data = credential.to_dict()

    assert data["user_id"] == "user123"
    assert data["access_token"] == "token"
    assert data["refresh_token"] == "refresh"
    assert data["scope"] == "identify"
    assert "expires_at" in data
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_credential_timestamps(db_manager: CredentialManager) -> None:
    """Test that timestamps are properly set."""
    before = datetime.now(UTC)

    credential = await db_manager.store_credentials(
        user_id="user123",
        access_token="token",
        refresh_token="refresh",
        expires_in=3600,
    )

    after = datetime.now(UTC)

    # SQLite stores naive datetimes, so make them comparable
    created_at = (
        credential.created_at
        if credential.created_at.tzinfo
        else credential.created_at.replace(tzinfo=UTC)
    )
    updated_at = (
        credential.updated_at
        if credential.updated_at.tzinfo
        else credential.updated_at.replace(tzinfo=UTC)
    )
    expires_at = (
        credential.expires_at
        if credential.expires_at.tzinfo
        else credential.expires_at.replace(tzinfo=UTC)
    )

    # Check that timestamps are set and reasonable
    assert before <= created_at <= after
    assert before <= updated_at <= after
    assert expires_at > after  # Should expire in the future
