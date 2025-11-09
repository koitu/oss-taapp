## Discord Service — Summary

This page summarizes the Discord service implementation in the repository. It gives a compact overview for readers of the docs site and links to implementation details in the codebase.

### What this component is

- A service-oriented implementation of a Discord chat client.
- Provides two access paths:
  - Local path: direct usage of the `DiscordClient` implementation.
  - Service path: an HTTP FastAPI service with a generated OpenAPI client and a `ServiceAdapterClient` that implements the same chat API.

### Key features

- OAuth2 Authorization Code flow with refresh tokens and per-user credential storage.
- Async-compatible HTTP client (`httpx`) with SQLAlchemy async-backed credential storage.
- FastAPI service exposing endpoints for authentication, channels, and messages.
- An auto-generated OpenAPI Python client and a service adapter that implements the project's abstract chat client API.

### Architecture (short)

1. User code calls a `Client` interface defined by `chat_client_api`.
2. Either `DiscordClient` (local) or `ServiceAdapterClient` (remote) is used.
3. The remote path uses a generated HTTP client to talk to the FastAPI service.
4. The FastAPI service uses `DiscordClient` internally and persists OAuth2 tokens in a SQLite DB.

### Important files & locations

- Abstract API: `src/chat_client_api/src` (interfaces for Client, Message, Channel)
- Discord implementation: `src/discord_client_impl/src` (client, messages, auth, database)
- FastAPI service: `src/services/discord_client_service/src` (service endpoints and app)
- Generated client: `src/clients/discord_client_service_client` (openapi client)
- Service adapter: `src/discord_client_service_adapter/src` (adapter that implements the chat API)

### Quick start (developer)

1. Ensure environment variables: `DISCORD_CLIENT_ID`, `DISCORD_CLIENT_SECRET`, `DISCORD_REDIRECT_URI`, `DISCORD_DB_PATH`.
2. Start the service (from the service folder):

   uv run uvicorn discord_client_service.service:app --reload --port 8000

3. Use the service adapter in your code to interact with the running service, or call the API endpoints directly.

### Public API endpoints (high level)

- GET /health — health check
- GET /auth/login — start OAuth flow (returns authorization URL)
- POST /auth/callback — complete OAuth callback with code + user_id
- DELETE /auth/logout/{user_id} — revoke stored credentials
- GET /{user_id}/channels — list channels
- GET /{user_id}/channels/{channel_id}/messages — list messages
- POST /{user_id}/channels/{channel_id}/messages — send message
- DELETE /{user_id}/channels/{channel_id}/messages/{message_id} — delete message

### Design notes / rationale (condensed)

- Multi-user support via per-user credentials in the database.
- Adapter pattern ensures user code doesn't change when switching local vs service path.
- OpenAPI generation provides a typed HTTP client to keep the adapter thin.

### Where to read more

- Full implementation and rationale: repository root `Discord.md`.
- Service implementation: `src/services/discord_client_service/src`.
- Database models and credential manager: `src/discord_client_impl/src/database`.

### Future improvements

- Add rate limiting, caching, and Prometheus metrics.
- Add a WebSocket or server-sent events path for real-time messages.
- Move credential management to a dedicated auth service for large deployments.

----

This summary is intentionally concise; follow the links above for in-depth documentation and code references.
