# Mail Client Service

A FastAPI-based REST service that provides a network interface to the mail client components.

## Overview

This service acts as a thin wrapper around the `mail_client_api` and `gmail_client_impl` components, exposing their functionality via HTTP endpoints. It demonstrates the **Service** pattern - a unit of deployment that runs as an independent process and communicates over a network protocol.

## Architecture

- **Service Layer**: FastAPI application with RESTful endpoints
- **Component Integration**: Uses dependency injection to obtain mail client instances
- **Type Safety**: Pydantic models for request/response validation
- **Error Handling**: Proper HTTP status codes and error responses

## API Endpoints

- `GET /messages` - Fetch list of message summaries
- `GET /messages/{message_id}` - Get full message details
- `POST /messages/{message_id}/mark-as-read` - Mark message as read
- `DELETE /messages/{message_id}` - Delete a message
- `GET /health` - Health check endpoint

## Running the Service

```bash
# From project root with activated virtual environment
uv run uvicorn mail_client_service.api:app --reload

# Or specify host and port
uv run uvicorn mail_client_service.api:app --host 0.0.0.0 --port 8000
```

## Testing

Unit tests use a fake client to avoid requiring Gmail API credentials:

```bash
# Run service tests
uv run pytest src/services/mail_client_service/tests/ -v
```

## OpenAPI Documentation

When the service is running, interactive API documentation is available at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
