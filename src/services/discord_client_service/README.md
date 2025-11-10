# Discord Client Service

RESTful API service for Discord chat operations with OAuth2 authentication.

## Features

- OAuth2 authorization code flow with Discord
- Per-user credential storage and management
- Discord message operations (get, send, delete)
- Discord channel operations (list, get)
- Automatic token refresh
- OpenAPI/Swagger documentation

## Installation

```bash
uv pip install -e .
```

## Usage

Start the service:

```bash
uvicorn discord_client_service.service:app --reload
```

The service will be available at `http://localhost:8000`.

API documentation is available at:
- Interactive docs: `http://localhost:8000/docs`
- OpenAPI schema: `http://localhost:8000/openapi.json`

## Environment Variables

Required environment variables (see `.env.example` in project root):

- `DISCORD_CLIENT_ID`: Discord application client ID
- `DISCORD_CLIENT_SECRET`: Discord application client secret
- `DISCORD_REDIRECT_URI`: OAuth2 redirect URI
- `DISCORD_DB_PATH`: Path to SQLite database file

### Important next steps:

1. Go to https://discord.com/developers/applications/${DISCORD_CLIENT_ID}/oauth2/general

2. Add this redirect URI: http://localhost:8000/auth/callback
3. Under OAuth2 → URL Generator, select scopes:

- identify
- guilds
- messages.read

## API Endpoints

### Authentication

- `GET /auth/login` - Initialize OAuth2 flow
- `POST /auth/callback` - Handle OAuth2 callback
- `DELETE /auth/logout/{user_id}` - Logout user
- `GET /auth/status/{user_id}` - Check authentication status

### Messages

- `GET /{user_id}/channels/{channel_id}/messages` - Get messages
- `POST /{user_id}/channels/{channel_id}/messages` - Send message
- `DELETE /{user_id}/channels/{channel_id}/messages/{message_id}` - Delete message

### Channels

- `GET /{user_id}/channels` - List channels
- `GET /{user_id}/channels/{channel_id}` - Get channel info

## Development

Run tests:

```bash
pytest
```

Type checking:

```bash
mypy src --explicit-package-bases
```

Linting:

```bash
ruff check .
```

### Regenerating OpenAPI Schema

After making changes to the API endpoints, regenerate the `openapi.json` file:

```bash
# From project root
uv run python generate_discord_openapi.py
```

The `openapi.json` file is committed to the repository to enable:
- Client code generation with `openapi-python-client`
- API documentation and schema validation
- Third-party integrations
