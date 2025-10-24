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

API documentation is available at `http://localhost:8000/docs`.

## Environment Variables

Required environment variables (see `.env.example` in project root):

- `DISCORD_CLIENT_ID`: Discord application client ID
- `DISCORD_CLIENT_SECRET`: Discord application client secret
- `DISCORD_REDIRECT_URI`: OAuth2 redirect URI
- `DISCORD_DB_PATH`: Path to SQLite database file

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
