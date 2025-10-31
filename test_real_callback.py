#!/usr/bin/env python3
"""Test the callback endpoint with a real OAuth code from Discord.

Usage:
    1. Run get_oauth_code.py to get the authorization URL
    2. Visit the URL in your browser and authorize
    3. Copy the code from the redirect URL
    4. Run this script:
       python test_real_callback.py <code> <user_id>

Example:
    python test_real_callback.py "AbCdEf123456..." "steven"
"""

import sys
import httpx


def test_real_callback(code: str, user_id: str):
    """Test callback with real Discord OAuth code."""

    # Load the saved state
    try:
        with open(".oauth_state") as f:
            state = f.read().strip()
    except FileNotFoundError:
        print("❌ No .oauth_state file found!")
        print("Run get_oauth_code.py first to generate the authorization URL.")
        sys.exit(1)

    print("=" * 70)
    print("Testing Discord OAuth Callback")
    print("=" * 70)
    print()
    print(f"📝 Code:    {code[:20]}... (truncated)")
    print(f"📝 State:   {state}")
    print(f"📝 User ID: {user_id}")
    print()

    # Make request to callback endpoint
    print("📡 Sending request to http://localhost:8000/auth/callback...")
    print()

    try:
        response = httpx.post(
            "http://localhost:8000/auth/callback",
            json={
                "code": code,
                "state": state,
                "user_id": user_id
            },
            timeout=10.0
        )

        print(f"📊 Status Code: {response.status_code}")
        print(f"📄 Response: {response.json()}")
        print()

        if response.status_code == 200:
            print("✅ SUCCESS! OAuth callback completed!")
            print()
            print("Your Discord credentials have been stored in the database.")
            print(f"You can now use user_id '{user_id}' to make Discord API calls.")
            print()
            print("=" * 70)
            print("Next Steps")
            print("=" * 70)
            print()
            print("Test getting channels:")
            print(f"  curl http://localhost:8000/{user_id}/channels")
            print()
            print("Test getting messages:")
            print(f"  curl http://localhost:8000/{user_id}/channels/CHANNEL_ID/messages")
            print()
            print("Check auth status:")
            print(f"  curl http://localhost:8000/auth/status/{user_id}")
            return True
        else:
            print(f"❌ FAILED with status {response.status_code}")
            print()
            print("Error details:")
            print(f"  {response.json().get('detail', 'Unknown error')}")
            return False

    except httpx.ConnectError:
        print("❌ ERROR: Could not connect to http://localhost:8000")
        print()
        print("Is the Discord service running?")
        print()
        print("Start it with:")
        print("  cd src/services/discord_client_service")
        print("  uv run uvicorn discord_client_service.service:app --reload --port 8000")
        sys.exit(1)
    except Exception as e:
        print(f"❌ ERROR: {e}")
        sys.exit(1)


def main():
    """Main entry point."""
    if len(sys.argv) < 3:
        print("Usage: python test_real_callback.py <code> <user_id>")
        print()
        print("Example:")
        print('  python test_real_callback.py "AbCdEf123456..." "steven"')
        print()
        print("Steps:")
        print("  1. Run: python get_oauth_code.py")
        print("  2. Visit the authorization URL in your browser")
        print("  3. Copy the 'code' parameter from the redirect URL")
        print("  4. Run this script with the code and a user_id")
        sys.exit(1)

    code = sys.argv[1]
    user_id = sys.argv[2]

    test_real_callback(code, user_id)


if __name__ == "__main__":
    main()
