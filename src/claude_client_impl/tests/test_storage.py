"""Tests for the `claude_client_impl.storage` module."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from claude_client_impl.storage import (
    delete_conversation,
    get_claude_key,
    get_conversation_data,
    save_conversation,
    set_claude_key,
)


@pytest.fixture
def temp_db(tmp_path: Path) -> Path:
    """Create a temporary database for testing."""
    # Change working directory to temp path so relative paths work
    original_cwd = Path.cwd()
    os.chdir(tmp_path)

    try:
        # Reload module to initialize with new working directory
        import importlib

        import claude_client_impl.storage
        importlib.reload(claude_client_impl.storage)

        # Initialize the database
        from claude_client_impl.storage import init_db
        init_db()

        db_path = tmp_path / ".data" / "claude_credentials.db"
        yield db_path
    finally:
        # Restore original directory
        os.chdir(original_cwd)
        # Reload module to restore original state
        import importlib

        import claude_client_impl.storage
        importlib.reload(claude_client_impl.storage)


@pytest.fixture
def temp_fernet_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Set up a temporary Fernet key for testing."""
    from cryptography.fernet import Fernet

    test_key = Fernet.generate_key()
    key_file = tmp_path / ".fernet_key"
    key_file.write_text(test_key.decode(), encoding="utf-8")
    monkeypatch.setenv("FERNET_KEY", test_key.decode())

    # Reload the module to pick up the new key and recreate fernet object
    import importlib

    import claude_client_impl.storage
    importlib.reload(claude_client_impl.storage)


def test_init_db_creates_directory(temp_db: Path) -> None:
    """Test that init_db creates the .data directory if it doesn't exist."""
    # The fixture already calls init, so we just verify the database exists
    assert temp_db.exists()


def test_set_and_get_claude_key(temp_db: Path, temp_fernet_key: None) -> None:
    """Test setting and getting a Claude API key."""
    subject = "test_user"
    api_key = "sk-ant-test123456789"

    # Set the key
    set_claude_key(subject, api_key)

    # Get the key back
    retrieved_key = get_claude_key(subject)
    assert retrieved_key == api_key


def test_get_claude_key_nonexistent_user(temp_db: Path, temp_fernet_key: None) -> None:
    """Test getting a key for a user that doesn't exist."""
    retrieved_key = get_claude_key("nonexistent_user")
    assert retrieved_key is None


def test_get_claude_key_no_key_set(temp_db: Path, temp_fernet_key: None) -> None:
    """Test getting a key when no key is set returns None."""
    retrieved_key = get_claude_key("user_no_key")
    assert retrieved_key is None


def test_set_claude_key_updates_existing(temp_db: Path, temp_fernet_key: None) -> None:
    """Test that setting a key for an existing user updates it."""
    subject = "existing_user"
    first_key = "sk-ant-first"
    second_key = "sk-ant-second"

    set_claude_key(subject, first_key)
    assert get_claude_key(subject) == first_key

    # Update with new key
    set_claude_key(subject, second_key)
    assert get_claude_key(subject) == second_key


def test_save_conversation_new(temp_db: Path, temp_fernet_key: None) -> None:
    """Test saving a new conversation."""
    conv_id = "conv-new"
    subject = "user1"
    created_at = "2025-01-01T00:00:00Z"
    messages_json = '[{"role": "user", "content": "hello"}]'

    save_conversation(conv_id, subject, created_at, messages_json)

    # Verify it was saved
    result = get_conversation_data(conv_id)
    assert result is not None
    assert result[0] == subject
    assert result[1] == created_at
    assert result[2] == messages_json


def test_save_conversation_updates_existing(temp_db: Path, temp_fernet_key: None) -> None:
    """Test that saving a conversation with the same ID updates it."""
    conv_id = "conv-update"
    subject = "user1"
    created_at = "2025-01-01T00:00:00Z"
    first_messages = '[{"role": "user", "content": "hello"}]'
    second_messages = '[{"role": "user", "content": "hello"}, {"role": "assistant", "content": "hi"}]'

    save_conversation(conv_id, subject, created_at, first_messages)
    save_conversation(conv_id, subject, created_at, second_messages)

    result = get_conversation_data(conv_id)
    assert result is not None
    assert result[2] == second_messages


def test_get_conversation_data_existing(temp_db: Path, temp_fernet_key: None) -> None:
    """Test retrieving existing conversation data."""
    conv_id = "conv-123"
    subject = "user1"
    created_at = "2025-01-01T00:00:00Z"
    messages_json = '[{"role": "user", "content": "test"}]'

    save_conversation(conv_id, subject, created_at, messages_json)

    result = get_conversation_data(conv_id)
    assert result is not None
    assert len(result) == 3
    assert result[0] == subject
    assert result[1] == created_at
    assert result[2] == messages_json


def test_get_conversation_data_nonexistent(temp_db: Path, temp_fernet_key: None) -> None:
    """Test retrieving nonexistent conversation returns None."""
    result = get_conversation_data("nonexistent-conv")
    assert result is None


def test_delete_conversation_existing(temp_db: Path, temp_fernet_key: None) -> None:
    """Test deleting an existing conversation."""
    conv_id = "conv-delete"
    subject = "user1"
    created_at = "2025-01-01T00:00:00Z"
    messages_json = "[]"

    save_conversation(conv_id, subject, created_at, messages_json)

    # Verify it exists
    assert get_conversation_data(conv_id) is not None

    # Delete it
    rowcount = delete_conversation(conv_id)
    assert rowcount == 1

    # Verify it's gone
    assert get_conversation_data(conv_id) is None


def test_delete_conversation_nonexistent(temp_db: Path, temp_fernet_key: None) -> None:
    """Test deleting a nonexistent conversation returns 0."""
    rowcount = delete_conversation("nonexistent-conv")
    assert rowcount == 0


def test_fernet_key_generation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that a Fernet key is generated if not present."""
    key_file = tmp_path / ".fernet_key"
    data_dir = tmp_path / ".data"
    data_dir.mkdir()

    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Remove FERNET_KEY from environment to trigger key generation
        monkeypatch.delenv("FERNET_KEY", raising=False)

        # Patch the module-level FERNET_KEY
        import claude_client_impl.storage
        original_fernet_key = claude_client_impl.storage.FERNET_KEY
        claude_client_impl.storage.FERNET_KEY = None

        # Reload to trigger key generation
        import importlib
        importlib.reload(claude_client_impl.storage)

        # Verify key file was created
        assert key_file.exists()

        # Restore
        claude_client_impl.storage.FERNET_KEY = original_fernet_key
    finally:
        os.chdir(original_cwd)


def test_fernet_key_from_existing_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that an existing Fernet key file is used."""
    key_file = tmp_path / ".fernet_key"

    data_dir = tmp_path / ".data"
    data_dir.mkdir()

    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Remove FERNET_KEY from environment
        monkeypatch.delenv("FERNET_KEY", raising=False)

        # Patch the module-level FERNET_KEY
        import claude_client_impl.storage
        original_fernet_key = claude_client_impl.storage.FERNET_KEY
        claude_client_impl.storage.FERNET_KEY = None

        # Create a key file
        from cryptography.fernet import Fernet
        test_key = Fernet.generate_key().decode()
        key_file.write_text(test_key, encoding="utf-8")

        # Reload to load from file
        import importlib
        importlib.reload(claude_client_impl.storage)

        # Verify the key matches
        assert test_key == claude_client_impl.storage.FERNET_KEY

        # Restore
        claude_client_impl.storage.FERNET_KEY = original_fernet_key
    finally:
        os.chdir(original_cwd)
