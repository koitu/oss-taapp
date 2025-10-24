"""Database models for Discord OAuth2 credential storage."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all database models."""


class DiscordCredential(Base):
    """Store OAuth2 credentials for Discord users.

    This model stores per-user OAuth2 tokens allowing multi-user
    Discord authentication in the service.

    """

    __tablename__ = "discord_credentials"

    user_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    access_token: Mapped[str] = mapped_column(String(512), nullable=False)
    refresh_token: Mapped[str] = mapped_column(String(512), nullable=False)
    token_type: Mapped[str] = mapped_column(String(50), default="Bearer")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    scope: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    def __repr__(self) -> str:
        """Return string representation of credential."""
        return f"<DiscordCredential(user_id='{self.user_id}', expires_at='{self.expires_at}')>"

    def to_dict(self) -> dict[str, Any]:
        """Convert credential to dictionary format.

        Returns:
            Dictionary containing credential data.

        """
        return {
            "user_id": self.user_id,
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "token_type": self.token_type,
            "expires_at": self.expires_at.isoformat(),
            "scope": self.scope,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def is_expired(self) -> bool:
        """Check if the access token is expired.

        Returns:
            True if expired, False otherwise.

        """
        # Ensure expires_at has timezone info (SQLite stores naive datetimes)
        expires_at_aware = (
            self.expires_at if self.expires_at.tzinfo else self.expires_at.replace(tzinfo=UTC)
        )
        return datetime.now(UTC) >= expires_at_aware
