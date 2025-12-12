"""Shared test fixtures for claude_client_impl tests."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

# ruff: noqa: PLC0415


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
