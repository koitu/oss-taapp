"""Fake Discord client implementations for testing the Discord service API.

These mimic the minimal behavior the API expects from the real clients so
the HTTP routes can be tested deterministically.
"""

from __future__ import annotations

from typing import Iterable

from chat_client_api.exceptions import MessageDeleteError, MessageNotFoundError


class FakeChannel:
    def __init__(self, id_: str, name: str, channel_type: str = "text") -> None:
        self.id = id_
        self.name = name
        self.channel_type = channel_type


class FakeMessage:
    def __init__(
        self,
        id_: str,
        channel_id: str,
        author_id: str = "user1",
        author_name: str = "Alice",
        content: str = "hello",
        timestamp: str = "2025-10-01T12:00:00Z",
        edited_timestamp: str | None = None,
    ) -> None:
        self.id = id_
        self.channel_id = channel_id
        self.author_id = author_id
        self.author_name = author_name
        self.content = content
        self.timestamp = timestamp
        self.edited_timestamp = edited_timestamp


class FakeBotClient:
    """A minimal bot client used for guild-level operations."""

    def __init__(self, channels: Iterable[FakeChannel] | None = None) -> None:
        self._channels = list(channels or [])

    def get_guild_channels(self, guild_id: str) -> Iterable[FakeChannel]:
        return self._channels

    def leave_guild(self, guild_id: str) -> None:
        # no-op for tests
        return None


class FakeUserClient:
    """Fake per-user client which supports channel/message operations."""

    def __init__(self) -> None:
        self._channels = {"c1": FakeChannel("c1", "general")}
        self._messages = {
            "c1": [
                FakeMessage("m1", channel_id="c1", content="first"),
                FakeMessage("m2", channel_id="c1", content="second"),
            ]
        }

    def get_channel(self, channel_id: str) -> FakeChannel:
        try:
            return self._channels[channel_id]
        except KeyError as e:
            raise ValueError(f"Channel {channel_id} not found") from e

    def get_messages(self, channel_id: str, max_results: int = 10) -> list[FakeMessage]:
        return self._messages.get(channel_id, [])[:max_results]

    def send_message(self, channel_id: str, content: str) -> FakeMessage:
        if not content:
            raise ValueError("message content empty")
        msg = FakeMessage("m3", channel_id=channel_id, content=content)
        self._messages.setdefault(channel_id, []).append(msg)
        return msg

    def delete_message(self, channel_id: str, message_id: str) -> None:
        msgs = self._messages.get(channel_id, [])
        for i, m in enumerate(msgs):
            if m.id == message_id:
                del msgs[i]
                return
        # Simulate not found
        raise MessageNotFoundError(f"Message {message_id} not found")
