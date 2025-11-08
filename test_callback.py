#!/usr/bin/env python3
"""Test script for Discord OAuth callback endpoint."""

import asyncio
import sys
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient


async def setup_database():
    """Initialize the test database."""
    from discord_client_impl.database import get_credential_manager
    manager = get_credential_manager()
    await manager.init_db()
    return manager


def test_callback_endpoint():
    """Test the OAuth callback endpoint with mocked Discord token exchange."""
    print("🧪 Testing /auth/callback endpoint...")

    # Import here so .env gets loaded first
    from discord_client_service.service import app

    # Initialize database
    asyncio.run(setup_database())

    client = TestClient(app)

    # Mock the token exchange
    with patch("discord_client_service.api.DiscordClient") as MockDiscordClient:
        # Setup mock
        mock_client_instance = MagicMock()
        mock_client_instance.exchange_code_for_token.return_value = {
            "access_token": "mock_access_token",
            "refresh_token": "mock_refresh_token",
            "token_type": "Bearer",
            "expires_in": 604800,
            "scope": "identify guilds",
        }
        MockDiscordClient.return_value = mock_client_instance

        # Make request
        response = client.post(
            "/auth/callback",
            json={
                "code": "test_authorization_code",
                "user_id": "test_user_123",
                "state": "test_state"
            }
        )

        print(f"📊 Status Code: {response.status_code}")
        print(f"📄 Response: {response.json()}")

        if response.status_code == 200:
            print("✅ Callback endpoint works correctly!")
            data = response.json()
            assert data["status"] == "success"
            assert data["user_id"] == "test_user_123"
            print(f"✅ User ID: {data['user_id']}")
            print(f"✅ Status: {data['status']}")
            return True
        print(f"❌ Callback failed with status {response.status_code}")
        print(f"❌ Error: {response.json().get('detail', 'Unknown error')}")
        return False


def test_callback_with_invalid_code():
    """Test callback with invalid authorization code."""
    print("\n🧪 Testing /auth/callback with invalid code...")

    from discord_client_service.service import app

    client = TestClient(app)

    # Mock the token exchange to fail
    with patch("discord_client_service.api.DiscordClient") as MockDiscordClient:
        mock_client_instance = MagicMock()
        mock_client_instance.exchange_code_for_token.side_effect = ValueError("Invalid authorization code")
        MockDiscordClient.return_value = mock_client_instance

        response = client.post(
            "/auth/callback",
            json={
                "code": "invalid_code",
                "user_id": "test_user_123"
            }
        )

        print(f"📊 Status Code: {response.status_code}")
        print(f"📄 Response: {response.json()}")

        if response.status_code == 400:
            print("✅ Correctly rejected invalid authorization code!")
            return True
        print(f"❌ Expected 400, got {response.status_code}")
        return False


def test_callback_validation():
    """Test callback input validation."""
    print("\n🧪 Testing /auth/callback input validation...")

    from discord_client_service.service import app

    client = TestClient(app)

    # Test missing required fields
    response = client.post(
        "/auth/callback",
        json={
            "code": "test_code"
            # Missing user_id
        }
    )

    print(f"📊 Status Code: {response.status_code}")
    print(f"📄 Response: {response.json()}")

    if response.status_code == 422:
        print("✅ Correctly validates required fields!")
        return True
    print(f"❌ Expected 422 validation error, got {response.status_code}")
    return False


if __name__ == "__main__":
    print("=" * 60)
    print("Discord OAuth Callback Endpoint Tests")
    print("=" * 60)

    results = []

    # Run tests
    results.append(("Valid callback", test_callback_endpoint()))
    results.append(("Invalid code", test_callback_with_invalid_code()))
    results.append(("Input validation", test_callback_validation()))

    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")

    print(f"\n{passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed")
        sys.exit(1)
