"""Storage layer for Claude API keys and conversations using SQLite."""

from __future__ import annotations

import os
from pathlib import Path

from cryptography.fernet import Fernet
from sqlalchemy import Column, String, Text, create_engine, delete, select
from sqlalchemy.orm import DeclarativeBase, Session

# Encryption key for API keys - same approach as OpenAI impl
FERNET_KEY = os.getenv("FERNET_KEY")
if FERNET_KEY is None:
    key_file = Path(".fernet_key")
    if key_file.exists():
        FERNET_KEY = key_file.read_text(encoding="utf-8").strip()
    else:
        FERNET_KEY = Fernet.generate_key().decode()
        key_file.write_text(FERNET_KEY, encoding="utf-8")

fernet = Fernet(FERNET_KEY)


class Base(DeclarativeBase):
    """Base class for all database models."""


class UserCred(Base):
    """Store encrypted Claude API keys per user."""

    __tablename__ = "user_creds"

    subject = Column(String, primary_key=True)
    encrypted_key = Column(String, nullable=False)


class ConversationData(Base):
    """Store conversation history."""

    __tablename__ = "conversations"

    conv_id = Column(String, primary_key=True)
    subject = Column(String, nullable=False)
    created_at = Column(String, nullable=False)
    messages_json = Column(Text, nullable=False)


data_dir = Path(".data")
db_path = data_dir / "claude_credentials.db"
engine = create_engine(f"sqlite:///{db_path}")


def init_db() -> None:
    """Initialize the database schema."""
    data_dir.mkdir(exist_ok=True)
    Base.metadata.create_all(engine)


init_db()


def set_claude_key(subject: str, key: str) -> None:
    """Store a Claude API key for a user."""
    encrypted = fernet.encrypt(key.encode()).decode()
    with Session(engine) as session:
        session.merge(UserCred(subject=subject, encrypted_key=encrypted))
        session.commit()


def get_claude_key(subject: str) -> str | None:
    """Retrieve a Claude API key for a user."""
    with Session(engine) as session:
        stmt = select(UserCred).where(UserCred.subject == subject)
        result = session.execute(stmt).scalar_one_or_none()
        if result is None:
            return None
        return fernet.decrypt(result.encrypted_key.encode()).decode()


def save_conversation(conv_id: str, subject: str, created_at: str, messages_json: str) -> None:
    """Save or update a conversation."""
    with Session(engine) as session:
        session.merge(
            ConversationData(
                conv_id=conv_id,
                subject=subject,
                created_at=created_at,
                messages_json=messages_json,
            )
        )
        session.commit()


def get_conversation_data(conv_id: str) -> tuple[str, str, str] | None:
    """Retrieve conversation data by ID."""
    with Session(engine) as session:
        stmt = select(ConversationData).where(ConversationData.conv_id == conv_id)
        result = session.execute(stmt).scalar_one_or_none()
        if result is None:
            return None
        return (result.subject, result.created_at, result.messages_json)


def delete_conversation(conv_id: str) -> int:
    """Delete a conversation by ID."""
    with Session(engine) as session:
        stmt = delete(ConversationData).where(ConversationData.conv_id == conv_id)
        result = session.execute(stmt)
        session.commit()
        return result.rowcount
