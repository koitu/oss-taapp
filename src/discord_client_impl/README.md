# Discord Client Implementation

Discord implementation of the `chat_client_api` contract with OAuth2 authentication.

## Features

- **OAuth2 Authentication**: Full OAuth2 flow with authorization code exchange
- **Token Management**: Access token and refresh token support
- **Discord REST API**: Complete integration with Discord API v10
- **Message Operations**: Send, retrieve, and delete messages
- **Channel Operations**: List and retrieve channel information
- **Multi-user Support**: Designed for per-user credential storage (via database in Phase 4)

## OAuth2 Flow

1. **Get Authorization URL**: Generate URL to redirect user to Discord
2. **User Authorizes**: User logs in and grants permissions
3. **Exchange Code**: Backend exchanges authorization code for access token
4. **Store Credentials**: Access token and refresh token stored in database (Phase 4)
5. **Make API Calls**: Use access token for Discord API requests

## Environment Variables

```bash
DISCORD_CLIENT_ID=your-client-id
DISCORD_CLIENT_SECRET=your-client-secret
DISCORD_REDIRECT_URI=http://localhost:8001/auth/callback
```

## Usage

### Direct Usage with Token

```python
from discord_client_impl import DiscordClient

# With existing access token
client = DiscordClient(access_token="your_access_token")

# Send a message
message = client.send_message(channel_id="123456", content="Hello!")

# Get recent messages
messages = list(client.get_messages(channel_id="123456", max_results=10))
```

### OAuth2 Flow

```python
from discord_client_impl import DiscordClient

# Initialize client
client = DiscordClient(
    client_id="your_client_id",
    client_secret="your_client_secret",
    redirect_uri="http://localhost:8001/auth/callback"
)

# Step 1: Get authorization URL
auth_url, state = client.get_authorization_url()
# Redirect user to auth_url

# Step 2: After user authorizes, exchange code for token
token_data = client.exchange_code_for_token(code="code_from_callback")
# token_data contains: access_token, refresh_token, expires_in, etc.

# Step 3: Client is now authenticated and ready to use
messages = list(client.get_messages(channel_id="123456"))
```

### Via Abstract API (after registration)

```python
import discord_client_impl  # Registers Discord as implementation
import chat_client_api

# Get client (will use Discord implementation)
client = chat_client_api.get_client(user_id="user123")

# Use abstract API
message = client.send_message(channel_id="123456", content="Hello!")
```

## Discord API Scopes

The client requests these OAuth2 scopes:
- `identify`: Read user information
- `guilds`: Read guild information
- `messages.read`: Read message history

Additional scopes can be added as needed.

## Type Safety

Fully typed with strict mypy checking and `py.typed` marker.
