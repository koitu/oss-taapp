#!/usr/bin/env python3
"""View the contents of the Discord credentials database."""

import asyncio
import sys
from datetime import datetime, UTC
from pathlib import Path


async def view_database():
    """View all credentials stored in the database."""
    from discord_client_impl.database import get_credential_manager

    print("=" * 80)
    print("Discord Credentials Database")
    print("=" * 80)
    print()

    # Check if database exists
    db_path = Path("discord_auth.db")
    if not db_path.exists():
        print("❌ Database file 'discord_auth.db' not found!")
        print()
        print("The database will be created when you:")
        print("  1. Start the Discord service")
        print("  2. Complete the OAuth flow for the first time")
        return

    print(f"📁 Database: {db_path.absolute()}")
    print(f"📊 Size: {db_path.stat().st_size} bytes")
    print()

    # Get credential manager
    manager = get_credential_manager()
    await manager.init_db()

    # List all credentials
    credentials = await manager.list_all_credentials()

    if not credentials:
        print("📭 No credentials stored in database yet")
        print()
        print("To add credentials:")
        print("  1. Run: python get_oauth_code.py")
        print("  2. Authorize in browser")
        print("  3. Run: python test_real_callback.py <code> <user_id>")
        await manager.close()
        return

    print(f"✅ Found {len(credentials)} credential(s)")
    print()

    # Display each credential
    for i, cred in enumerate(credentials, 1):
        print("─" * 80)
        print(f"Credential #{i}")
        print("─" * 80)
        print(f"👤 User ID:        {cred.user_id}")
        print(f"🔑 Access Token:   {cred.access_token[:20]}...{cred.access_token[-10:]}")
        print(f"🔄 Refresh Token:  {cred.refresh_token[:20]}...{cred.refresh_token[-10:]}")
        print(f"🏷️  Token Type:     {cred.token_type}")
        print(f"📅 Expires At:     {cred.expires_at}")

        # Check if expired
        expires_at_aware = (
            cred.expires_at if cred.expires_at.tzinfo
            else cred.expires_at.replace(tzinfo=UTC)
        )
        is_expired = datetime.now(UTC) >= expires_at_aware

        if is_expired:
            print(f"⚠️  Status:         EXPIRED")
        else:
            time_left = expires_at_aware - datetime.now(UTC)
            days = time_left.days
            hours = time_left.seconds // 3600
            print(f"✅ Status:         Valid (expires in {days}d {hours}h)")

        if cred.scope:
            print(f"🔐 Scopes:         {cred.scope}")
        print(f"📆 Created:        {cred.created_at}")
        print(f"🔄 Updated:        {cred.updated_at}")
        print()

    print("=" * 80)
    print("Database Management Commands")
    print("=" * 80)
    print()
    print("View specific user:")
    print("  python view_db.py <user_id>")
    print()
    print("Delete credentials:")
    print("  curl -X DELETE http://localhost:8000/auth/logout/<user_id>")
    print()
    print("Check auth status:")
    print("  curl http://localhost:8000/auth/status/<user_id>")
    print()

    await manager.close()


async def view_specific_user(user_id: str):
    """View credentials for a specific user."""
    from discord_client_impl.database import get_credential_manager

    print("=" * 80)
    print(f"Discord Credentials for User: {user_id}")
    print("=" * 80)
    print()

    manager = get_credential_manager()
    await manager.init_db()

    cred = await manager.get_credentials(user_id)

    if not cred:
        print(f"❌ No credentials found for user_id: {user_id}")
        print()
        print("Available users:")
        all_creds = await manager.list_all_credentials()
        if all_creds:
            for c in all_creds:
                print(f"  - {c.user_id}")
        else:
            print("  (none)")
        await manager.close()
        return

    print(f"👤 User ID:        {cred.user_id}")
    print()
    print(f"🔑 Access Token:   {cred.access_token}")
    print()
    print(f"🔄 Refresh Token:  {cred.refresh_token}")
    print()
    print(f"🏷️  Token Type:     {cred.token_type}")
    print(f"📅 Expires At:     {cred.expires_at}")

    # Check if expired
    expires_at_aware = (
        cred.expires_at if cred.expires_at.tzinfo
        else cred.expires_at.replace(tzinfo=UTC)
    )
    is_expired = datetime.now(UTC) >= expires_at_aware

    if is_expired:
        print(f"⚠️  Status:         EXPIRED")
        print()
        print("To refresh the token:")
        print(f"  1. Get new authorization code (python get_oauth_code.py)")
        print(f"  2. Exchange for new tokens (python test_real_callback.py <code> {user_id})")
    else:
        time_left = expires_at_aware - datetime.now(UTC)
        days = time_left.days
        hours = time_left.seconds // 3600
        minutes = (time_left.seconds % 3600) // 60
        print(f"✅ Status:         Valid (expires in {days}d {hours}h {minutes}m)")

    if cred.scope:
        print()
        print(f"🔐 Scopes:         {cred.scope}")

    print()
    print(f"📆 Created:        {cred.created_at}")
    print(f"🔄 Updated:        {cred.updated_at}")
    print()
    print("=" * 80)

    await manager.close()


async def view_database_schema():
    """View the database schema."""
    import sqlite3

    print("=" * 80)
    print("Database Schema")
    print("=" * 80)
    print()

    conn = sqlite3.connect("discord_auth.db")
    cursor = conn.cursor()

    # Get table info
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='discord_credentials';")
    schema = cursor.fetchone()

    if schema:
        print("Table: discord_credentials")
        print()
        print(schema[0])
        print()

        # Get column info
        cursor.execute("PRAGMA table_info(discord_credentials);")
        columns = cursor.fetchall()

        print()
        print("Columns:")
        for col in columns:
            cid, name, col_type, not_null, default_val, pk = col
            nullable = "NOT NULL" if not_null else "NULL"
            primary = "(PRIMARY KEY)" if pk else ""
            print(f"  {name:20} {col_type:15} {nullable:10} {primary}")

    conn.close()


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--schema":
            asyncio.run(view_database_schema())
        else:
            user_id = sys.argv[1]
            asyncio.run(view_specific_user(user_id))
    else:
        asyncio.run(view_database())


if __name__ == "__main__":
    main()
