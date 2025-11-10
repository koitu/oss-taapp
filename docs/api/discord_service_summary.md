## Discord Service — Summary

This page summarizes the Discord service implementation in the repository. It gives a compact overview for readers of the docs site and links to implementation details in the codebase.

### What this component is

- A service-oriented implementation of a Discord chat client.
- Provides two access paths:
  - Local path: direct usage of the `DiscordClient` implementation.
  - Service path: an HTTP FastAPI service with a generated OpenAPI client and a `ServiceAdapterClient` that implements the same chat API.

### Key features

- OAuth2 Authorization Code flow with refresh tokens and session-backed credential storage (credentials are kept in the user's session, not a per-user DB by default).
- Async-capable HTTP client (`httpx`) and an async-friendly FastAPI service.
- FastAPI service exposing endpoints for authentication, channels, and messages.
- An auto-generated OpenAPI Python client and a service adapter that implements the project's abstract chat client API.

### Architecture (short)

1. User code calls a `Client` interface defined by `chat_client_api`.
2. Either `DiscordClient` (local) or `ServiceAdapterClient` (remote) is used.
3. The remote path uses a generated HTTP client to talk to the FastAPI service.
4. The FastAPI service uses `DiscordClient` internally and manages OAuth2 tokens in the active session (session-store or signed cookies); a persistent per-user DB is not required by the default setup.

### Important files & locations

- Abstract API: `src/chat_client_api/` (interfaces for Client, Message, Channel)
- Discord implementation: `src/discord_client_impl/` (client, messages, auth)
- FastAPI service: `src/services/discord_client_service/` (service endpoints and app)
- Generated client: `src/clients/discord_client_service_client/` (openapi client)
- Service adapter: `src/discord_client_service_adapter/` (adapter that implements the chat API)

### Quick start (developer)

1. Ensure environment variables: `DISCORD_CLIENT_ID`, `DISCORD_CLIENT_SECRET`, `DISCORD_REDIRECT_URI`, `DISCORD_PUBLIC_KEY`, `DISCORD_BOT_TOKEN`.
  - Note: `DISCORD_DB_PATH` is not required by the repository's default session-based design.
2. Start the service (from the repository root or service folder):

  uv run uvicorn discord_client_service.service:app --reload --port 8000

3. Use the service adapter in your code to interact with the running service, or call the API endpoints directly. The adapter and generated client operate on the authenticated session (no `user_id` path parameter required).

Example (adapter):

```python
from discord_client_service_adapter import ServiceAdapterClient
client = ServiceAdapterClient(service_url="http://localhost:8000")
channels = list(client.get_channels(guild_id="123"))
``` 

### Public API endpoints (high level)

- GET /health — health check
- GET /openapi.json — OpenAPI spec
- GET /auth/login — start OAuth flow (redirects or returns authorization URL)
- GET /auth/status/{guild_id} — check auth status for the given guild in the current session
- DELETE /auth/logout/{guild_id} — logout / revoke credentials for the guild in the current session
- GET /guilds/{guild_id}/channels — list channels for a guild
- GET /{guild_id}/channels/{channel_id} — get channel metadata
- GET /{guild_id}/channels/{channel_id}/messages — list messages
- POST /{guild_id}/channels/{channel_id}/messages — send message
- DELETE /{guild_id}/channels/{channel_id}/messages/{message_id} — delete message

### Design notes / rationale (condensed)

- Session-backed credentials: tokens are stored in the active session (server-side store or signed cookie) and refreshed as needed. This simplifies the default deployment and avoids persisting sensitive tokens in a per-user DB.
- Adapter pattern ensures user code doesn't change when switching local vs service path.
- OpenAPI generation provides a typed HTTP client which keeps the adapter thin and easier to maintain.

### Where to read more

- Full implementation and rationale: repository root `Discord.md`.
- Service implementation: `src/services/discord_client_service/`.
- Discord client implementation: `src/discord_client_impl/`.

### Future improvements

- Add rate limiting, caching, and Prometheus metrics.
- Add a WebSocket or server-sent events path for real-time messages.
- For large deployments, configure a shared session backend (Redis) and tighten cookie/session security settings.
