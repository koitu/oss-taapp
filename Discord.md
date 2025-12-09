# Discord Service Implementation

## Overview

This document describes the Discord chat service implementation in this repository. It documents the architecture and usage for the current codebase, which uses session-based credential handling (no per-user database) and a service adapter + generated client to offer both local and remote access patterns.

## Architecture

### Design Philosophy

The implementation follows the Adapter pattern and service-oriented architecture, providing two distinct paths for accessing Discord functionality:

1. **Local Path**: Direct usage of the Discord client implementation
2. **Service Path**: Remote access through a FastAPI service with an adapter that presents a familiar local interface

This dual-path approach demonstrates architectural flexibility and separation of concerns. Note: recent code changes removed the per-user database and `user_id`-based routing in favor of session-based authentication.

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        User Code                            │
└──────────────────────┬──────────────────────────────────────┘
                       │
          ┌────────────┴────────────┐
          │                         │
    Local Path                Service Path
          │                         │
          ▼                         ▼
┌─────────────────┐    ┌──────────────────────────┐
│ DiscordClient   │    │ ServiceAdapterClient     │
│ (Implementation)│    │ (Adapter)                │
└────────┬────────┘    └──────────┬───────────────┘
         │                        │
         │                        ▼
         │             ┌──────────────────────────┐
         │             │ Generated HTTP Client    │
         │             │ (OpenAPI Client)         │
         │             └──────────┬───────────────┘
         │                        │
         │                        ▼
         │             ┌──────────────────────────┐
         │             │ FastAPI Service          │
         │             │ (REST API)               │
         │             └──────────┬───────────────┘
         │                        │
         │                        ▼
         │             ┌──────────────────────────┐
         │             │ DiscordClient + Session  │
         │             └──────────┬───────────────┘
         │                        │
         └────────────────────────┘
                      │
                      ▼
         ┌────────────────────────┐
         │   Discord REST API     │
         └────────────────────────┘
```

## Implementation Phases

### Changes from previous version

- Removed per-user database storage: the service no longer stores credentials per `user_id` in a repository database.
- Authentication and credential state are now managed using sessions (server-side or signed cookies), not a persistent per-user DB.
- API routes no longer include `user_id` in the path; endpoints operate on the current authenticated session.

### Phase 1: Abstract Chat Client API

**Purpose**: Define platform-agnostic interfaces for chat operations.

**Components**:
- `Message`: Abstract base class for messages with properties like id, content, author, timestamp
- `Channel`: Abstract base class for channels with properties like id, name, type
- `Client`: Abstract base class defining CRUD operations for messages and channels

**Key Design Decisions**:
- Used abstract base classes (ABC) to enforce interface contracts
- Designed for multi-session support: clients are obtained for the current session or created directly (no `user_id` path parameter required)
- Properties instead of methods for immutable attributes
- Iterator return types for memory-efficient batch operations

**Location**: `src/chat_client_api/`

### Phase 2: Discord Client Implementation

**Purpose**: Implement the abstract interfaces for Discord's REST API.

**Components**:
- `DiscordClient`: Main client class handling OAuth2 and Discord API calls
- `DiscordMessage`: Concrete implementation of Message
- `DiscordChannel`: Concrete implementation of Channel
- OAuth2 methods: authorization URL generation, token exchange, token refresh

**Key Design Decisions**:
- Used `httpx` for async-capable HTTP requests
- Implemented OAuth2 authorization code flow (not implicit flow)
- Client can operate with or without stored credentials
- Environment variables for configuration (client ID, secret, redirect URI)
- Comprehensive error handling with descriptive messages

**Location**: `src/discord_client_impl/`

**OAuth2 Flow**:
1. Generate authorization URL with state parameter for CSRF protection
2. User authorizes application in browser
3. Discord redirects with authorization code
4. Exchange code for access token and refresh token
5. Store tokens in the current session for future use

### Phase 3: Session-based Credential Management

**Purpose**: Maintain OAuth2 credential state tied to a user's session rather than persisting credentials in a per-user database.

**Components**:
- Session middleware (server-side session store or signed session cookie)
- Token management logic within the Discord client/service: tokens are kept in the active session and refreshed as needed
- `auth_helper`: convenience functions to obtain an authenticated client from the current session

**Key Design Decisions**:
- Credentials are stored in the active session (server-side store or secure signed cookie) instead of an application database.
- Session-based approach simplifies multi-tenant concerns and reduces persistent storage of sensitive tokens in this repository's default design.
- Automatic token refresh still occurs when the access token is expired; refreshed tokens are written back into the session.
- Sessions typically require a session secret and an appropriate session backend (in-memory, Redis, or signed cookie).

**Assumptions**: The repository currently expects session usage for authentication. For multi-instance production deployments, configure a shared session backend (Redis or similar) and a secure session secret.

**Location**: Session and auth-related code lives with the FastAPI service in `src/services/discord_client_service/` and the Discord client implementation in `src/discord_client_impl/`.

### Phase 4: FastAPI Service

**Purpose**: Expose Discord operations through a RESTful HTTP API.

**Components**:
- FastAPI application with OpenAPI documentation
- OAuth2 endpoints: login, callback, logout, status (session-based)
- Message endpoints: GET, POST, DELETE
- Channel endpoints: GET (list and individual)
- Health check endpoint
- Session lifespan and middleware (session init + cleanup)

**Key Design Decisions**:
- RESTful design using the authenticated session; `user_id` is not required in path parameters, Instead `guild_id` is required
- Pydantic models for request/response validation
- Proper HTTP status codes (200, 400, 401, 404, 500)
- Async endpoints for non-blocking I/O
- Lifespan context manager for session initialization if needed
- Comprehensive logging for debugging

**API Structure**:
```
GET     /health
GET     /openapi.json
GET     /auth/login
GET     /auth/status/{guild_id}
DELETE  /auth/logout/{guild_id}
GET     /guilds/{guild_id}/channels
GET     /{guild_id}/channels/{channel_id}
GET     /{guild_id}/channels/{channel_id}/messages
POST    /{guild_id}/channels/{channel_id}/messages
DELETE  /{guild_id}/channels/{channel_id}/messages/{message_id}
```

**Location**: `src/services/discord_client_service/`

### Phase 5: OpenAPI Client Generation

**Purpose**: Generate type-safe Python client from FastAPI's OpenAPI specification.

**Process**:
1. FastAPI automatically generates OpenAPI 3.0 specification
2. Use `openapi-python-client` to generate Python client code
3. Generated client provides sync and async methods for each endpoint
4. Type-safe models for all request/response bodies

**Generated Components**:
- `Client` and `AuthenticatedClient` classes
- API modules for each endpoint (organized by tags)
- Pydantic models for all request/response types
- Type-safe error handling

**Key Design Decisions**:
- Generated code is not manually edited (regenerate when API changes)
- Fixed type annotations to use modern Python 3.11+ syntax (Union -> |)
- Separate package for clean dependency management

**Location**: `src/clients/discord_client_service_client/`

### Phase 6: Service Adapter

**Purpose**: Wrap the generated HTTP client to implement the chat_client_api.Client interface.

**Components**:
- `ServiceAdapterClient`: Implements Client interface
- `ServiceMessage`: Implements Message interface
- `ServiceChannel`: Implements Channel interface

**Key Design Decisions**:
- Translates between HTTP responses and abstract interfaces
- Hides network complexity from user code
- Provides same interface as DiscordClient (local implementation)
- Handles HTTP errors gracefully
- Type narrowing with isinstance checks for union types
- User code unchanged whether using local or service path

**Location**: `src/discord_client_service_adapter/`

## Setup Instructions

### Prerequisites

1. **Python Environment**:
   - Python 3.11 or higher
   - `uv` package manager (used in this workspace) or use pip/venv as preferred

2. **Discord Application**:
   - Create an application at https://discord.com/developers/applications
   - Note the Application ID (Client ID)
   - Generate a Client Secret under OAuth2 → General
   - Add redirect URI: such as `http://localhost:8001/auth/callback`

### Installation

```powershell
# From the repository root
cd .\oss-taapp

# Sync dependencies (if using uv as the project manager)
uv sync
```

### Configuration

The system uses environment variables for configuration. In the current session-driven design, you'll need:

- `DISCORD_CLIENT_ID`: OAuth2 client identifier from Discord Developer Portal
- `DISCORD_CLIENT_SECRET`: OAuth2 client secret (keep secure)
- `DISCORD_REDIRECT_URI`: OAuth2 callback URL (must match Discord settings)
- `DISCORD_PUBLIC_KEY`: public key for the app
- `DISCORD_BOT_TOKEN`: bot token for discord

Note: The per-user database variable (previously `DISCORD_DB_PATH`) is no longer required by the default code in this repo.

## Running the System

### Option 1: Automated Test Suite

```
uv run ruff check .
uv run mypy src tests
uv run pytest
```

This runs:
- Unit tests for all components
- Type checking with mypy strict mode
- Linting with ruff

### Option 2: Service Adapter Testing

The service adapter provides the same interface as the local client but routes through the HTTP service. Note: adapters no longer accept a `user_id`; they operate with the current authenticated session or an authenticated HTTP client instance.

```python
from discord_client_service_adapter import ServiceAdapterClient

# Initialize adapter (service must be running)
client = ServiceAdapterClient(service_url="http://localhost:8000")

# If the adapter supports attaching session cookies or an auth token, do that before calling methods.
channels = list(client.get_channels())
messages = list(client.get_messages(channel_id="123", max_results=10))
sent = client.send_message(channel_id="123", content="Test message")
```

## Implementation Logic and Design Rationale

### Multi-User / Multi-Session Support

**Problem**: Traditional single-user credential storage doesn't fit multi-session applications.

**Solution**: The current code uses session-bound credential state. The service maintains OAuth2 tokens inside the user's session, and client operations act on the authenticated session.

**Benefits**:
- Multiple concurrent sessions are supported without a per-user DB schema in this repository
- Credentials are scoped to sessions, reducing risk of long-lived database storage in this codebase
- Scales to multi-tenant scenarios when combined with a shared session backend (Redis) in production

### OAuth2 with Session Persistence

**Problem**: Persisting tokens in a database may be unnecessary for some deployments and increases responsibility for secure storage.

**Solution**: Store OAuth2 tokens in the user's session for the lifetime of the session. Tokens are refreshed transparently and updated back into the session.

**Implementation Details**:
- Tokens are placed into the session object after the OAuth callback completes.
- Before making API calls, the client checks token expiry and refreshes using the refresh token when needed, updating the session state.
- Sessions should be secured with HTTPS and appropriate cookie flags (Secure, HttpOnly, SameSite) when used in production.

## Project Structure

```
src/
├── chat_client_api/              # Abstract interfaces
├── discord_client_impl/          # Discord implementation (client, token handling)
├── services/discord_client_service/  # FastAPI service (session middleware + routes)
├── clients/discord_client_service_client/  # Generated OpenAPI client
└── discord_client_service_adapter/  # Service adapter (adapts HTTP client to chat_client_api)
```

## Key Takeaways

1. **Abstract Interfaces**: Define clear contracts before implementation
2. **OAuth2 Best Practices**: Use authorization code flow with refresh tokens
3. **Session-Backed Credentials**: The current repository favors session-bound credential storage.
4. **Service-Oriented Design**: Separation of concerns, independent deployment
5. **Code Generation**: Let tools generate boilerplate (OpenAPI client)
6. **Adapter Pattern**: Hide implementation details, present familiar interface
7. **Type Safety**: Catch errors early with static type checking
8. **Comprehensive Testing**: Unit tests, integration tests, type checking

## References

- Discord API Documentation: https://discord.com/developers/docs
- FastAPI Documentation: https://fastapi.tiangolo.com
- OAuth2 RFC: https://tools.ietf.org/html/rfc6749
- OpenAPI Specification: https://swagger.io/specification/
- Python Type Hints: https://docs.python.org/3/library/typing.html
