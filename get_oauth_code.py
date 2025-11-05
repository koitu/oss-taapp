#!/usr/bin/env python3
"""Helper script to get OAuth code from Discord for testing the callback endpoint.

This script will:
1. Generate the authorization URL
2. Print instructions for you to authorize in browser
3. Show you how to extract the code from the redirect
4. Demonstrate how to call the callback endpoint with real credentials
"""

import os
import sys

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def main():
    """Generate OAuth URL and show instructions."""
    from discord_client_impl.discord_impl import DiscordClient

    print("=" * 70)
    print("Discord OAuth Code Retrieval Guide")
    print("=" * 70)
    print()

    # Get credentials from environment
    client_id = os.environ.get("DISCORD_CLIENT_ID")
    client_secret = os.environ.get("DISCORD_CLIENT_SECRET")
    redirect_uri = os.environ.get("DISCORD_REDIRECT_URI", "http://localhost:8000/auth/callback")

    if not client_id or not client_secret:
        print("❌ ERROR: DISCORD_CLIENT_ID or DISCORD_CLIENT_SECRET not found in environment!")
        print("Please ensure your .env file is configured correctly.")
        sys.exit(1)

    print("✅ Discord Credentials Found:")
    print(f"   Client ID: {client_id}")
    print(f"   Redirect URI: {redirect_uri}")
    print()

    # Create client and generate auth URL
    client = DiscordClient()
    auth_url, state = client.get_authorization_url()

    print("=" * 70)
    print("STEP 1: Authorize Your Application")
    print("=" * 70)
    print()
    print("📋 Copy this URL and paste it in your browser:")
    print()
    print(f"   {auth_url}")
    print()
    print("=" * 70)
    print("STEP 2: Authorize in Browser")
    print("=" * 70)
    print()
    print("1. The browser will take you to Discord's authorization page")
    print("2. Click 'Authorize' to grant permissions to your application")
    print("3. Discord will redirect you to: http://localhost:8000/auth/callback")
    print("   (This will likely fail with 'connection refused' - that's OK!)")
    print()
    print("=" * 70)
    print("STEP 3: Extract the Code from URL")
    print("=" * 70)
    print()
    print("After clicking Authorize, your browser will show a URL like:")
    print()
    print("   http://localhost:8000/auth/callback?code=XXXXX&state=YYYYY")
    print()
    print("Copy the ENTIRE URL from your browser's address bar!")
    print()
    print("=" * 70)
    print("STEP 4: Parse the Code")
    print("=" * 70)
    print()
    print("The URL will contain two important parameters:")
    print()
    print(f"   state: {state}")
    print("   code:  (will be a long string like 'AbCdEf123456...')")
    print()
    print("=" * 70)
    print("STEP 5: Test the Callback Endpoint")
    print("=" * 70)
    print()
    print("Once you have the code, you can test the callback with curl:")
    print()
    print("   curl -X POST http://localhost:8000/auth/callback \\")
    print('     -H "Content-Type: application/json" \\')
    print("     -d '{")
    print('       "code": "YOUR_CODE_HERE",')
    print(f'       "state": "{state}",')
    print('       "user_id": "your_discord_user_id"')
    print("     }'")
    print()
    print("Or in Python:")
    print()
    print("   import httpx")
    print()
    print("   response = httpx.post(")
    print('       "http://localhost:8000/auth/callback",')
    print("       json={")
    print('           "code": "YOUR_CODE_HERE",')
    print(f'           "state": "{state}",')
    print('           "user_id": "your_discord_user_id"')
    print("       }")
    print("   )")
    print("   print(response.json())")
    print()
    print("=" * 70)
    print("Understanding the Parameters")
    print("=" * 70)
    print()
    print("📝 code:    The authorization code from Discord (one-time use)")
    print(f"📝 state:   CSRF protection token (must match: {state})")
    print("📝 user_id: Your choice of identifier (e.g., 'steven123')")
    print()
    print("The user_id is NOT your Discord user ID - it's any string you")
    print("want to use to identify this set of credentials in your database.")
    print("For example: 'steven', 'user123', 'test_account', etc.")
    print()
    print("=" * 70)
    print()

    # Save state to file for reference
    with open(".oauth_state", "w") as f:
        f.write(state)

    print("💾 State saved to .oauth_state file")
    print()
    print("⚠️  IMPORTANT: The authorization code can only be used ONCE!")
    print("    After you exchange it for tokens, you'll need to authorize")
    print("    again to get a new code.")
    print()


if __name__ == "__main__":
    main()
