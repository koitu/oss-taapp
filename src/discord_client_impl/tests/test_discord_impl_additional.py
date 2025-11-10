from unittest.mock import MagicMock

import pytest
import respx
from httpx import Response

from discord_client_impl.discord_impl import DiscordClient


def test_get_authorization_url_without_client_id(monkeypatch):
    # Ensure no env var
    monkeypatch.delenv("DISCORD_CLIENT_ID", raising=False)
    client = DiscordClient(client_id=None, client_secret=None)

    with pytest.raises(ValueError, match="DISCORD_CLIENT_ID not configured"):
        client._get_authorization_url()


def test_update_http_client_sets_headers():
    client = DiscordClient(client_id="cid", client_secret="cs", access_token=None, token_type="Bot")
    # assign access token and call update
    client.access_token = "newtoken"
    client._update_http_client()

    assert client._http_client.headers.get("Authorization") == f"{client.token_type} newtoken"


@respx.mock
def test_leave_guild_success():
    client = DiscordClient(client_id="cid", client_secret="cs", access_token="t")
    respx.delete("https://discord.com/api/v10/users/@me/guilds/g1").mock(return_value=Response(204))

    assert client.leave_guild("g1") is True


@respx.mock
def test_leave_guild_failure():
    client = DiscordClient(client_id="cid", client_secret="cs", access_token="t")
    respx.delete("https://discord.com/api/v10/users/@me/guilds/g1").mock(return_value=Response(500))

    with pytest.raises(ValueError, match="Failed to leave guild"):
        client.leave_guild("g1")


@respx.mock
def test_get_guild_channels_success():
    client = DiscordClient(client_id="cid", client_secret="cs", access_token="t")
    mock_channels = [{"id": "c1", "name": "A", "type": 0}, {"id": "c2", "name": "B", "type": 0}]
    respx.get("https://discord.com/api/v10/guilds/g1/channels").mock(return_value=Response(200, json=mock_channels))

    channels = list(client.get_guild_channels("g1"))
    assert len(channels) == 2
    assert channels[0].id == "c1"


@respx.mock
def test_get_guild_channels_failure():
    client = DiscordClient(client_id="cid", client_secret="cs", access_token="t")
    respx.get("https://discord.com/api/v10/guilds/g1/channels").mock(return_value=Response(500))

    with pytest.raises(ValueError, match="Failed to retrieve guild channels"):
        list(client.get_guild_channels("g1"))


def test_context_manager_closes_http_client():
    client = DiscordClient(client_id="cid", client_secret="cs", access_token="t")
    # patch the underlying client's close
    client._http_client.close = MagicMock()

    with client:
        pass

    assert client._http_client.close.called
