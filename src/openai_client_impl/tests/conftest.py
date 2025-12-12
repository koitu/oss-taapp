"""Shared test fixtures for openai_client_impl tests."""

from __future__ import annotations

from pathlib import Path

import pytest

# ruff: noqa: PLC0415


@pytest.fixture
def temp_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a temporary database for testing."""
    db_path = tmp_path / "test.db"
    db_url = f"sqlite:///{db_path}"
    monkeypatch.setenv("DATABASE_URL", db_url)
    # Reimport to get the new database URL
    import importlib

    import openai_client_impl.storage

    importlib.reload(openai_client_impl.storage)
    from openai_client_impl.storage import init_db

    init_db()
    return db_path


@pytest.fixture
def temp_fernet_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Set up a temporary Fernet key for testing."""
    key_file = tmp_path / ".fernet_key"
    from cryptography.fernet import Fernet

    test_key = Fernet.generate_key()
    key_file.write_bytes(test_key)
    monkeypatch.setenv("FERNET_KEY", test_key.decode())
    # Reimport to get the new key
    import importlib

    import openai_client_impl.storage

    importlib.reload(openai_client_impl.storage)
