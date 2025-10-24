"""Initialize Discord credentials database.

This script creates the database tables for storing Discord OAuth2 credentials.

Usage:
    python -m discord_client_impl.scripts.init_db

Or with uv:
    uv run python -m discord_client_impl.scripts.init_db

"""

import asyncio
import logging
import sys

from discord_client_impl.database import get_credential_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Initialize database tables."""
    try:
        manager = get_credential_manager()
        logger.info("Initializing database...")
        await manager.init_db()
        logger.info("Database initialized successfully!")
        await manager.close()
    except Exception:
        logger.exception("Failed to initialize database")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
