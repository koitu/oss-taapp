# Discord Service Implementation

## Overview

This document describes the complete implementation of a Discord chat service following service-oriented architecture patterns. The implementation demonstrates how to build a scalable, maintainable chat client system with OAuth2 authentication, database-backed credential storage, and both local and remote access patterns.

## Architecture

### Design Philosophy

The implementation follows the Adapter pattern and service-oriented architecture, providing two distinct paths for accessing Discord functionality:

1. **Local Path**: Direct usage of the Discord client implementation
2. **Service Path**: Remote access through a FastAPI service with an adapter that presents a familiar local interface

This dual-path approach demonstrates architectural flexibility and separation of concerns.

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
         │             │ DiscordClient + Database │
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

### Phase 1: Abstract Chat Client API

**Purpose**: Define platform-agnostic interfaces for chat operations.

**Components**:
- `ChatMessage`: Abstract base class for messages with properties like id, content, author, timestamp
- `Channel`: Abstract base class for channels with properties like id, name, type
- `Client`: Abstract base class defining CRUD operations for messages and channels

**Key Design Decisions**:
- Used abstract base classes (ABC) to enforce interface contracts
- Designed for multi-user support with `get_client(user_id)` factory pattern
- Properties instead of methods for immutable attributes
- Iterator return types for memory-efficient batch operations

**Location**: `src/chat_client_api/`

### Phase 2: Discord Client Implementation

**Purpose**: Implement the abstract interfaces for Discord's REST API.

**Components**:
- `DiscordClient`: Main client class handling OAuth2 and Discord API calls
- `DiscordMessage`: Concrete implementation of ChatMessage
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
5. Store tokens for future use

### Phase 3: Database Layer

**Purpose**: Persist OAuth2 credentials per user with automatic token refresh.

**Components**:
- `DiscordCredential`: SQLAlchemy model for storing OAuth2 tokens
- `CredentialManager`: Async database operations (CRUD)
- `auth_helper`: Convenience functions for getting authenticated clients

**Key Design Decisions**:
- SQLAlchemy 2.0 with async support (asyncio + aiosqlite)
- Per-user credential storage (not global singleton)
- Token expiration tracking with timezone awareness
- Automatic token refresh when expired
- Separate database per deployment (configurable path)

**Database Schema**:
```
discord_credentials
├── user_id (Primary Key)
├── access_token
├── refresh_token
├── token_type
├── expires_at
├── scope
├── created_at
└── updated_at
```

**Location**: `src/discord_client_impl/database/`

### Phase 4: FastAPI Service

**Purpose**: Expose Discord operations through a RESTful HTTP API.

**Components**:
- FastAPI application with OpenAPI documentation
- OAuth2 endpoints: login, callback, logout, status
- Message endpoints: GET, POST, DELETE
- Channel endpoints: GET (list and individual)
- Health check endpoint
- Database lifespan management

**Key Design Decisions**:
- RESTful design with user_id in URL path for multi-tenancy
- Pydantic models for request/response validation
- Proper HTTP status codes (200, 400, 401, 404, 500)
- Async endpoints for non-blocking I/O
- Lifespan context manager for database initialization
- Comprehensive logging for debugging

**API Structure**:
```
GET  /health
GET  /auth/login
POST /auth/callback
DELETE /auth/logout/{user_id}
GET  /auth/status/{user_id}
GET  /{user_id}/channels
GET  /{user_id}/channels/{channel_id}
GET  /{user_id}/channels/{channel_id}/messages
POST /{user_id}/channels/{channel_id}/messages
DELETE /{user_id}/channels/{channel_id}/messages/{message_id}
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
- `ServiceMessage`: Implements ChatMessage interface
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
   - `uv` package manager installed

2. **Discord Application**:
   - Create application at https://discord.com/developers/applications
   - Note the Application ID (Client ID)
   - Generate a Client Secret under OAuth2 → General
   - Add redirect URI: `http://localhost:8000/auth/callback`

### Installation

```bash
# Clone the repository
cd oss-taapp

# Sync dependencies
uv sync

# Set up environment variables
./setup_discord_env.sh
# Or manually create .env with:
# DISCORD_CLIENT_ID=your_client_id
# DISCORD_CLIENT_SECRET=your_client_secret
# DISCORD_REDIRECT_URI=http://localhost:8000/auth/callback
# DISCORD_DB_PATH=discord_credentials.db
```

### Configuration

The system uses environment variables for configuration:

- `DISCORD_CLIENT_ID`: OAuth2 client identifier from Discord Developer Portal
- `DISCORD_CLIENT_SECRET`: OAuth2 client secret (keep secure)
- `DISCORD_REDIRECT_URI`: OAuth2 callback URL (must match Discord settings)
- `DISCORD_DB_PATH`: Path to SQLite database file for credentials

## Running the System

### Option 1: Automated Test Suite

```bash
./run_tests.sh
```

This runs:
- Unit tests for all components (38 tests)
- Type checking with mypy strict mode
- Linting with ruff

### Option 2: Manual Service Testing

**Step 1: Start the FastAPI service**

```bash
cd src/services/discord_client_service
uv run uvicorn discord_client_service.service:app --reload --port 8000
```

**Step 2: Test health endpoint**

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status":"healthy","service":"discord-client-service"}
```

**Step 3: Access API documentation**

Open http://localhost:8000/docs in a browser to see interactive Swagger UI.

**Step 4: Complete OAuth flow**

Initialize authentication:
```bash
curl http://localhost:8000/auth/login
```

This returns an authorization URL. Open it in a browser, authorize the application, and copy the code parameter from the callback URL.

Complete the callback:
```bash
curl -X POST http://localhost:8000/auth/callback \
  -H "Content-Type: application/json" \
  -d '{"code": "YOUR_CODE_HERE", "user_id": "test_user_123"}'
```

**Step 5: Test Discord operations**

List channels:
```bash
curl http://localhost:8000/test_user_123/channels
```

Get messages:
```bash
curl "http://localhost:8000/test_user_123/channels/CHANNEL_ID/messages?limit=5"
```

Send message:
```bash
curl -X POST "http://localhost:8000/test_user_123/channels/CHANNEL_ID/messages" \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello from the API!"}'
```

### Option 3: Service Adapter Testing

The service adapter provides the same interface as the local client but routes through the HTTP service:

```python
from discord_client_service_adapter import ServiceAdapterClient

# Initialize adapter (service must be running)
client = ServiceAdapterClient(
    service_url="http://localhost:8000",
    user_id="test_user_123"
)

# Use same interface as local client
channels = list(client.get_channels())
messages = list(client.get_messages(channel_id="123", max_results=10))
sent = client.send_message(channel_id="123", content="Test message")
```

## Implementation Logic and Design Rationale

### Multi-User Support

**Problem**: Traditional implementations use global singletons or single-user patterns.

**Solution**: Every component accepts `user_id` parameter. The database stores per-user credentials. The factory pattern `get_client(user_id)` retrieves the appropriate client.

**Benefits**:
- Multiple users can use the same service instance
- Credentials are isolated per user
- Scales to multi-tenant scenarios

### OAuth2 with Database Persistence

**Problem**: Simple file-based token storage is not production-ready.

**Solution**: SQLAlchemy database with proper credential management, token expiration tracking, and automatic refresh.

**Implementation Details**:
- Tokens stored encrypted in database (application-level)
- Expiration checked before each request
- Automatic refresh using refresh token when expired
- Timezone-aware timestamps (UTC)

### Service-Oriented Architecture

**Problem**: Monolithic applications are hard to scale and maintain.

**Solution**: Separate FastAPI service exposing HTTP API, with generated client and adapter.

**Benefits**:
- Service can be deployed independently
- Multiple clients can connect (web, mobile, CLI)
- Easy to add rate limiting, caching, monitoring
- Clear separation of concerns

### Adapter Pattern

**Problem**: User code should not need to change when switching between local and service implementations.

**Solution**: ServiceAdapterClient implements the same Chat Client API interface as DiscordClient, but delegates to HTTP client.

**Benefits**:
- User code unchanged: `client.get_messages()` works for both
- Easy to switch implementations (config change)
- Hides network complexity (retries, timeouts, serialization)

### Type Safety Throughout

**Problem**: Dynamic typing leads to runtime errors.

**Solution**: Full type annotations, mypy strict mode, Pydantic models.

**Implementation**:
- All functions have type annotations
- Abstract base classes enforce contracts
- Pydantic validates request/response at runtime
- OpenAPI client is fully typed
- mypy strict mode catches type errors at development time

### Testing Strategy

**Unit Tests**: Test individual components in isolation
- Abstract interfaces (12 tests)
- Message and channel implementations (9 tests)
- Database operations (13 tests)
- Registration and factory (4 tests)

**Type Checking**: Enforce type safety
- mypy strict mode on all modules
- No type: ignore comments
- Explicit type annotations

**Linting**: Maintain code quality
- ruff with comprehensive rule set
- Consistent formatting
- Documented exceptions

**Integration Tests**: Verify end-to-end functionality
- Manual testing with real Discord API
- Service adapter integration tests
- OAuth flow verification

## Project Structure

```
src/
├── chat_client_api/              # Abstract interfaces
│   ├── src/chat_client_api/
│   │   ├── __init__.py
│   │   ├── client.py            # Client ABC
│   │   └── message.py           # ChatMessage, Channel ABCs
│   └── tests/
│
├── discord_client_impl/          # Discord implementation
│   ├── src/discord_client_impl/
│   │   ├── __init__.py
│   │   ├── discord_impl.py      # DiscordClient
│   │   ├── message_impl.py      # DiscordMessage, DiscordChannel
│   │   ├── auth_helper.py       # Auth convenience functions
│   │   └── database/
│   │       ├── models.py        # SQLAlchemy models
│   │       └── manager.py       # CredentialManager
│   └── tests/
│
├── services/discord_client_service/  # FastAPI service
│   └── src/discord_client_service/
│       ├── __init__.py
│       ├── service.py           # FastAPI app
│       └── api.py               # Endpoint definitions
│
├── clients/discord_client_service_client/  # Generated client
│   ├── __init__.py
│   ├── client.py                # HTTP client
│   ├── api/                     # Generated API modules
│   ├── models/                  # Generated Pydantic models
│   └── types.py                 # Type utilities
│
└── discord_client_service_adapter/  # Service adapter
    └── src/discord_client_service_adapter/
        ├── __init__.py
        └── adapter_impl.py      # ServiceAdapterClient
```

## Code Quality Metrics

- **Type Coverage**: 100% (all functions typed)
- **Mypy Compliance**: Strict mode, no errors
- **Ruff Compliance**: All checks pass
- **Test Coverage**: 38 unit tests
  - chat_client_api: 100% coverage
  - discord_client_impl: Core functionality covered
- **Lines of Code**: ~5000 (including generated)
- **Packages Created**: 6

## Key Takeaways

1. **Abstract Interfaces**: Define clear contracts before implementation
2. **OAuth2 Best Practices**: Use authorization code flow with refresh tokens
3. **Database-Backed Credentials**: Production-ready multi-user support
4. **Service-Oriented Design**: Separation of concerns, independent deployment
5. **Code Generation**: Let tools generate boilerplate (OpenAPI client)
6. **Adapter Pattern**: Hide implementation details, present familiar interface
7. **Type Safety**: Catch errors early with static type checking
8. **Comprehensive Testing**: Unit tests, integration tests, type checking

## Future Enhancements

Potential improvements for production use:

1. **Authentication Service**: Separate OAuth service for credential management
2. **Rate Limiting**: Implement rate limiting in FastAPI service
3. **Caching**: Cache channel lists and metadata
4. **WebSocket Support**: Add real-time message streaming
5. **Retry Logic**: Implement exponential backoff for failed requests
6. **Metrics**: Add Prometheus metrics for monitoring
7. **Logging**: Structured logging with correlation IDs
8. **Error Recovery**: More sophisticated error handling and recovery

## References

- Discord API Documentation: https://discord.com/developers/docs
- FastAPI Documentation: https://fastapi.tiangolo.com
- OAuth2 RFC: https://tools.ietf.org/html/rfc6749
- OpenAPI Specification: https://swagger.io/specification/
- Python Type Hints: https://docs.python.org/3/library/typing.html

## Conclusion

This implementation demonstrates a complete, production-quality chat service architecture. The design emphasizes type safety, maintainability, and architectural flexibility. The dual-path approach (local and service) shows how to build systems that can grow from simple library usage to distributed microservices while maintaining a consistent interface for client code.
