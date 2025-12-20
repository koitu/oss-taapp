"""Discord message and channel implementations."""

from typing import Any

from chat_api import Message


class DiscordMessage(Message):
    """Discord implementation of Message."""

    def __init__(self, raw_data: dict[str, Any]) -> None:
        """Initialize a Discord message from raw API data.

        Args:
            raw_data: Raw message data from Discord API.

        """
        self._raw_data = raw_data

    @property
    def id(self) -> str:
        """Return the unique identifier of the message."""
        return str(self._raw_data.get("id", ""))

    @property
    def channel_id(self) -> str:
        """Return the ID of the channel where the message was sent."""
        return str(self._raw_data.get("channel_id", ""))

    @property
    def sender_id(self) -> str:
        """Return the ID of the message author."""
        author = self._raw_data.get("author", {})
        return str(author.get("id", "")) if isinstance(author, dict) else ""

    @property
    def sender_name(self) -> str:
        """Return the display name of the message author."""
        author = self._raw_data.get("author", {})
        if isinstance(author, dict):
            # Prefer global_name, fallback to username
            return str(author.get("global_name") or author.get("username", "Unknown"))
        return "Unknown"

    @property
    def content(self) -> str:
        """Return the text content of the message."""
        return str(self._raw_data.get("content", ""))

    @property
    def timestamp(self) -> str:
        """Return the timestamp when the message was created (ISO 8601 format)."""
        return str(self._raw_data.get("timestamp", ""))

    @property
    def edited_timestamp(self) -> str | None:
        """Return the timestamp when the message was last edited, or None if never edited."""
        edited = self._raw_data.get("edited_timestamp")
        return str(edited) if edited else None
