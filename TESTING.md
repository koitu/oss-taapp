# Discord Service Testing Guide

This guide walks through testing all layers of the Discord implementation.

## Prerequisites

### 1. Create a Discord Application

1. Go to https://discord.com/developers/applications
2. Click "New Application"
3. Give it a name (e.g., "OSS-TAAPP Test")
4. Go to "OAuth2" → "General"
5. Copy your **Client ID** and **Client Secret**
6. Add a redirect URI: `http://localhost:8000/auth/callback`
7. Under "OAuth2" → "URL Generator":
   - Select scopes: `identify`, `guilds`, `messages.read`
   - Copy the generated URL for later

### 2. Set Environment Variables

Create or update your `.env` file in the project root:

```bash
# Discord OAuth2 Configuration
DISCORD_CLIENT_ID=your_client_id_here
DISCORD_CLIENT_SECRET=your_client_secret_here
DISCORD_REDIRECT_URI=http://localhost:8000/auth/callback
DISCORD_DB_PATH=discord_credentials.db

# Test Configuration
TEST_DISCORD_CHANNEL_ID=your_test_channel_id
TEST_DISCORD_USER_ID=your_discord_user_id
```

To get your Discord User ID:
- Enable Developer Mode in Discord (Settings → Advanced → Developer Mode)
- Right-click your username and select "Copy User ID"

To get a Channel ID:
- Right-click any channel and select "Copy Channel ID"

### 3. Install Dependencies

```bash
uv sync
```

## Testing Layers

### Layer 1: Chat Client API (Unit Tests)

Test the abstract interfaces:

```bash
PYTHONPATH=src/chat_client_api/src:$PYTHONPATH uv run pytest src/chat_client_api/tests/ -v
```

**Expected Output:**
```
test_chat_message_properties PASSED
test_channel_properties PASSED
test_client_methods PASSED
... (12 tests should pass)
```

### Layer 2: Discord Client Implementation (Unit Tests)

Test the Discord client with mocked HTTP responses:

```bash
PYTHONPATH=src/discord_client_impl/src:src/chat_client_api/src:$PYTHONPATH uv run pytest src/discord_client_impl/tests/test_discord_impl.py -v
```

**Expected Output:**
```
test_get_authorization_url PASSED
test_exchange_code_for_token PASSED
test_send_message PASSED
test_get_messages PASSED
... (13 tests should pass)
```

### Layer 3: Database Layer (Unit Tests)

Test credential storage and retrieval:

```bash
uv run pytest src/discord_client_impl/tests/test_database.py -v
```

**Expected Output:**
```
test_store_credentials PASSED
test_get_credentials PASSED
test_token_expiration PASSED
test_refresh_tokens PASSED
... (13 tests should pass)
```

### Layer 4: FastAPI Service (Manual Testing)

#### Step 1: Start the Service

In one terminal:

```bash
cd src/services/discord_client_service
uv run uvicorn discord_client_service.service:app --reload --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
INFO:     Initializing Discord service...
INFO:     Database initialized successfully
```

#### Step 2: Test Health Endpoint

In another terminal:

```bash
curl http://localhost:8000/health
```

**Expected Output:**
```json
{"status":"healthy","service":"discord-client-service"}
```

#### Step 3: Test OpenAPI Documentation

Open in your browser:
- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/redoc (ReDoc)

You should see all endpoints documented with schemas.

#### Step 4: Test OAuth Flow

**Initialize OAuth:**

```bash
curl http://localhost:8000/auth/login
```

**Expected Output:**
```json
{
  "authorization_url": "https://discord.com/api/oauth2/authorize?...",
  "state": "some-random-state"
}
```

**Authorize User:**
1. Open the `authorization_url` in your browser
2. Authorize the application
3. You'll be redirected to `http://localhost:8000/auth/callback?code=...`
4. Copy the `code` parameter from the URL

**Complete OAuth Callback:**

```bash
curl -X POST http://localhost:8000/auth/callback \
  -H "Content-Type: application/json" \
  -d '{
    "code": "YOUR_CODE_HERE",
    "user_id": "test_user_123"
  }'
```

**Expected Output:**
```json
{
  "status": "success",
  "user_id": "test_user_123"
}
```

**Check Auth Status:**

```bash
curl http://localhost:8000/auth/status/test_user_123
```

**Expected Output:**
```json
{
  "authenticated": true,
  "user_id": "test_user_123"
}
```

#### Step 5: Test Message Endpoints

**Get Messages:**

```bash
curl "http://localhost:8000/test_user_123/channels/YOUR_CHANNEL_ID/messages?limit=5"
```

**Send Message:**

```bash
curl -X POST "http://localhost:8000/test_user_123/channels/YOUR_CHANNEL_ID/messages" \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello from the API!"}'
```

**Expected Output:**
```json
{
  "id": "message_id",
  "channel_id": "YOUR_CHANNEL_ID",
  "content": "Hello from the API!",
  "author_id": "...",
  "author_name": "...",
  "timestamp": "2025-10-24T...",
  "edited_timestamp": null
}
```

#### Step 6: Test Channel Endpoints

**Get All Channels:**

```bash
curl http://localhost:8000/test_user_123/channels
```

**Get Specific Channel:**

```bash
curl http://localhost:8000/test_user_123/channels/YOUR_CHANNEL_ID
```

### Layer 5: Service Adapter (Integration Test)

Create a test script to verify the adapter works:

```bash
cat > test_adapter.py << 'PYEOF'
"""Test the Discord service adapter."""
import asyncio
from discord_client_service_adapter import ServiceAdapterClient

async def main():
    # Initialize adapter (assumes service is running on localhost:8000)
    client = ServiceAdapterClient(
        service_url="http://localhost:8000",
        user_id="test_user_123"  # Use your authenticated user_id
    )
    
    print("Testing Discord Service Adapter")
    print("=" * 50)
    
    # Test 1: Get channels
    print("\n1. Getting channels...")
    try:
        channels = list(client.get_channels())
        print(f"   ✓ Found {len(channels)} channels")
        for ch in channels[:3]:  # Show first 3
            print(f"     - {ch.name} ({ch.id})")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 2: Get messages (use your channel ID)
    channel_id = input("\nEnter a channel ID to test: ")
    print(f"\n2. Getting messages from channel {channel_id}...")
    try:
        messages = list(client.get_messages(channel_id=channel_id, max_results=5))
        print(f"   ✓ Found {len(messages)} messages")
        for msg in messages:
            print(f"     - {msg.author_name}: {msg.content[:50]}...")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 3: Send message
    print(f"\n3. Sending test message to channel {channel_id}...")
    try:
        sent = client.send_message(
            channel_id=channel_id,
            content="🤖 Test message from service adapter!"
        )
        print(f"   ✓ Message sent: {sent.id}")
        print(f"     Content: {sent.content}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n" + "=" * 50)
    print("Adapter testing complete!")

if __name__ == "__main__":
    asyncio.run(main())
PYEOF

# Run the test
uv run python test_adapter.py
```

**Expected Output:**
```
Testing Discord Service Adapter
==================================================

1. Getting channels...
   ✓ Found 5 channels
     - general (123456789)
     - announcements (987654321)
     - testing (456789123)

2. Getting messages from channel 123456789...
   ✓ Found 5 messages
     - User1: Hey everyone!...
     - User2: How's it going?...

3. Sending test message to channel 123456789...
   ✓ Message sent: 789123456
     Content: 🤖 Test message from service adapter!

==================================================
Adapter testing complete!
```

## Type Checking and Linting

Verify code quality:

```bash
# Run all mypy checks
uv run mypy src/chat_client_api/src --explicit-package-bases
uv run mypy src/discord_client_impl/src --explicit-package-bases
uv run mypy src/services/discord_client_service/src --explicit-package-bases
uv run mypy src/discord_client_service_adapter/src --explicit-package-bases

# Run all ruff checks
uv run ruff check src/chat_client_api
uv run ruff check src/discord_client_impl
uv run ruff check src/services/discord_client_service
uv run ruff check src/discord_client_service_adapter
```

All should pass with no errors ✅

## Troubleshooting

### OAuth Issues

**Problem:** "Invalid OAuth redirect URI"
- **Solution:** Make sure redirect URI in Discord app settings exactly matches `http://localhost:8000/auth/callback`

**Problem:** "User not authenticated"
- **Solution:** Complete the OAuth flow first using `/auth/login` and `/auth/callback`

### Database Issues

**Problem:** "No credentials found"
- **Solution:** Ensure OAuth callback was successful and credentials were stored

**Problem:** "Token expired"
- **Solution:** The system should auto-refresh. Check logs for refresh errors.

### Service Issues

**Problem:** "Connection refused"
- **Solution:** Make sure the FastAPI service is running on port 8000

**Problem:** "404 Not Found"
- **Solution:** Check that the endpoint path is correct (include user_id in path)

## Clean Up

After testing:

```bash
# Stop the FastAPI service (Ctrl+C)

# Remove test database
rm discord_credentials.db

# Remove test script
rm test_adapter.py
```

## Summary

You've now tested:
- ✅ Unit tests for all layers
- ✅ FastAPI service with OAuth2
- ✅ Database credential storage
- ✅ Service adapter wrapping HTTP client
- ✅ Type checking and linting

All layers working together demonstrate the complete service-oriented architecture!
