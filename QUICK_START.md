# Quick Start Guide - Testing Your Discord Implementation

## ✅ Prerequisites Complete
- [x] Discord application created
- [x] Credentials added to .env file

## Step-by-Step Testing

### Step 1: Verify Discord App Settings

Go to your Discord Developer Portal and ensure:

1. **OAuth2 Redirect URI is set:**
   - Visit: https://discord.com/developers/applications
   - Select your application
   - Go to OAuth2 → General
   - Under "Redirects", add: `http://localhost:8000/auth/callback`
   - Click "Save Changes"

2. **Required OAuth2 Scopes:**
   - Go to OAuth2 → URL Generator
   - Select scopes: `identify`, `guilds`, `messages.read`
   - Copy the generated URL (you'll use this later)

### Step 2: Run Automated Tests

Verify everything is working correctly:

```bash
# Run the test suite
./run_tests.sh
```

**Expected:** 
- ✅ 38 unit tests pass
- ✅ All mypy checks pass
- ✅ All ruff checks pass

### Step 3: Start the FastAPI Service

In your terminal:

```bash
cd src/services/discord_client_service
uv run uvicorn discord_client_service.service:app --reload --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
INFO:     Initializing Discord service...
INFO:     Database initialized successfully
```

**Keep this terminal open!** The service needs to stay running.

### Step 4: Test the Health Endpoint

Open a **new terminal** and run:

```bash
curl http://localhost:8000/health
```

**Expected output:**
```json
{"status":"healthy","service":"discord-client-service"}
```

✅ If you see this, your service is running correctly!

### Step 5: Open Swagger UI

Open your browser and go to:
```
http://localhost:8000/docs
```

You should see the interactive API documentation with all endpoints:
- OAuth2 endpoints (login, callback, logout, status)
- Message endpoints (GET, POST, DELETE)
- Channel endpoints (GET)

### Step 6: Test OAuth2 Flow

#### 6.1 Initialize OAuth

In your terminal:

```bash
curl http://localhost:8000/auth/login
```

**Output will look like:**
```json
{
  "authorization_url": "https://discord.com/api/oauth2/authorize?response_type=code&client_id=...&scope=identify+guilds+messages.read&state=...",
  "state": "some-random-string"
}
```

#### 6.2 Authorize the Application

1. **Copy the `authorization_url`** from the response above
2. **Open it in your browser**
3. **Log in to Discord** (if not already logged in)
4. **Click "Authorize"** to grant permissions

#### 6.3 Get the Authorization Code

After authorizing, you'll be redirected to:
```
http://localhost:8000/auth/callback?code=XXXXXXXXXXXXX
```

The page might show an error (that's OK - we haven't implemented a callback page UI). 

**Copy the `code` parameter** from the URL (the XXXXXXXXXXXXX part).

#### 6.4 Complete the OAuth Callback

In your terminal, run this (replace YOUR_CODE_HERE with the code from step 6.3):

```bash
curl -X POST http://localhost:8000/auth/callback \
  -H "Content-Type: application/json" \
  -d '{
    "code": "YOUR_CODE_HERE",
    "user_id": "test_user_123"
  }'
```

**Expected output:**
```json
{
  "status": "success",
  "user_id": "test_user_123"
}
```

✅ Your OAuth2 credentials are now stored in the database!

#### 6.5 Verify Authentication

```bash
curl http://localhost:8000/auth/status/test_user_123
```

**Expected output:**
```json
{
  "authenticated": true,
  "user_id": "test_user_123"
}
```

### Step 7: Test Discord Operations

Now you can test actual Discord operations!

#### Get Your Channels

```bash
curl http://localhost:8000/test_user_123/channels
```

**Expected:** List of Discord servers/channels you have access to.

#### Get Messages from a Channel

First, get a channel ID from Discord:
- Open Discord
- Enable Developer Mode: Settings → Advanced → Developer Mode
- Right-click any text channel → Copy Channel ID

Then:

```bash
curl "http://localhost:8000/test_user_123/channels/YOUR_CHANNEL_ID/messages?limit=5"
```

**Expected:** List of recent messages from that channel.

#### Send a Test Message

```bash
curl -X POST "http://localhost:8000/test_user_123/channels/YOUR_CHANNEL_ID/messages" \
  -H "Content-Type: application/json" \
  -d '{"content": "🤖 Hello from my Discord API implementation!"}'
```

**Expected:** The message appears in your Discord channel!

### Step 8: Test the Service Adapter (Integration Test)

Create and run an integration test:

```bash
cat > test_integration.py << 'PYEOF'
"""Integration test for Discord service adapter."""
from discord_client_service_adapter import ServiceAdapterClient

# Initialize adapter (make sure service is running on localhost:8000)
client = ServiceAdapterClient(
    service_url="http://localhost:8000",
    user_id="test_user_123"  # Use the user_id from OAuth flow
)

print("🧪 Testing Discord Service Adapter Integration")
print("=" * 60)

# Test 1: Get channels
print("\n1️⃣  Getting your Discord channels...")
try:
    channels = list(client.get_channels())
    print(f"   ✅ Found {len(channels)} channels")
    for i, ch in enumerate(channels[:5], 1):  # Show first 5
        print(f"      {i}. {ch.name} (ID: {ch.id}, Type: {ch.channel_type})")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Get messages
if channels:
    test_channel = channels[0]
    print(f"\n2️⃣  Getting messages from '{test_channel.name}'...")
    try:
        messages = list(client.get_messages(channel_id=test_channel.id, max_results=3))
        print(f"   ✅ Found {len(messages)} recent messages")
        for msg in messages:
            preview = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
            print(f"      • {msg.author_name}: {preview}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Send a message
    print(f"\n3️⃣  Sending test message to '{test_channel.name}'...")
    try:
        sent = client.send_message(
            channel_id=test_channel.id,
            content="🤖 Integration test successful! This message was sent via the service adapter."
        )
        print(f"   ✅ Message sent successfully!")
        print(f"      Message ID: {sent.id}")
        print(f"      Content: {sent.content}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

print("\n" + "=" * 60)
print("✅ Integration test complete!")
PYEOF

# Run the integration test
uv run python test_integration.py
```

**Expected:** 
- ✅ Channels listed
- ✅ Messages retrieved
- ✅ New message sent and appears in Discord

### Step 9: Verify Everything Works

You should now have:
- ✅ FastAPI service running on port 8000
- ✅ OAuth2 authentication working
- ✅ Credentials stored in database
- ✅ Able to list channels
- ✅ Able to read messages
- ✅ Able to send messages
- ✅ Service adapter working end-to-end

## 🎉 Success!

Your Discord implementation is fully working! You've successfully:

1. ✅ Implemented the abstract chat client API
2. ✅ Created Discord client with OAuth2
3. ✅ Built database layer for credential storage
4. ✅ Deployed FastAPI service
5. ✅ Generated OpenAPI client
6. ✅ Created service adapter
7. ✅ Tested the complete architecture

## Troubleshooting

### "Invalid redirect URI"
- Make sure `http://localhost:8000/auth/callback` is added in Discord Developer Portal
- Check that port 8000 matches in both .env and Discord settings

### "401 Unauthorized" when accessing channels/messages
- Complete the OAuth flow first (steps 6.1-6.4)
- Verify authentication with `/auth/status/{user_id}`

### "Connection refused"
- Make sure the FastAPI service is running (Step 3)
- Check that you're using port 8000

### Service won't start
- Run `uv sync` to ensure all dependencies are installed
- Check .env file has all required variables

## Next Steps

Now you're ready to:
1. Create the pull request to merge hw2 → root
2. Demo the complete architecture
3. Show the service-oriented design patterns

The implementation is complete and tested! 🚀
