"""Test service module behavior when dotenv is unavailable and .env exists."""

import builtins
import importlib
from pathlib import Path

import pytest


def test_service_manual_dotenv(monkeypatch, tmp_path, caplog):
    # create a .env file in the project root so manual loader can find it
    env_path = Path(".env")
    env_content = "TEST_VAL=1\n"
    env_path.write_text(env_content)

    # cause ImportError when trying to import dotenv
    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "dotenv" or name.startswith("dotenv"):
            raise ImportError("no dotenv")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    try:
        # reload the service module to exercise the manual .env loading branch
        import discord_client_service.service as svc

        importlib.reload(svc)
        assert hasattr(svc, "app")
    finally:
        # cleanup .env we created
        try:
            env_path.unlink()
        except Exception:
            pass