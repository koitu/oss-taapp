# Mail Client Service - Usage Examples

## Starting the Service

### Option 1: Using the run script
```bash
uv run python run_service.py
```

### Option 2: Using uvicorn directly
```bash
uv run uvicorn mail_client_service.api:app --reload --port 8000
```

The service will start on `http://localhost:8000`

## API Examples

### 1. Health Check

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy"
}
```

---

### 2. Get List of Messages

**Basic request (10 messages):**
```bash
curl http://localhost:8000/messages
```

**With custom limit:**
```bash
curl "http://localhost:8000/messages?max_results=5"
```

**Response:**
```json
{
  "messages": {
    "abc123": {
      "subject": "Meeting Tomorrow",
      "from": "alice@example.com",
      "date": "2025-10-02"
    },
    "def456": {
      "subject": "Project Update",
      "from": "bob@example.com",
      "date": "2025-10-01"
    }
  },
  "count": 2
}
```

---

### 3. Get Specific Message Details

```bash
curl http://localhost:8000/messages/abc123
```

**Response:**
```json
{
  "id": "abc123",
  "subject": "Meeting Tomorrow",
  "from": "alice@example.com",
  "date": "2025-10-02",
  "body": "Hi team,\n\nLet's meet tomorrow at 10 AM...\n\nBest,\nAlice"
}
```

**Error (404):**
```json
{
  "detail": "Message not found: xyz999"
}
```

---

### 4. Mark Message as Read

```bash
curl -X POST http://localhost:8000/messages/abc123/mark-as-read
```

**Response:**
```json
{
  "status": "success",
  "message": "Message abc123 marked as read"
}
```

---

### 5. Delete Message

**Warning:** This permanently deletes the message from Gmail!

```bash
curl -X DELETE http://localhost:8000/messages/abc123
```

**Response:**
```json
{
  "status": "success",
  "message": "Message abc123 deleted successfully"
}
```

---

## Using Python Requests Library

```python
import requests

BASE_URL = "http://localhost:8000"

# Get messages
response = requests.get(f"{BASE_URL}/messages", params={"max_results": 5})
data = response.json()
print(f"Found {data['count']} messages")

# Get specific message
message_id = list(data['messages'].keys())[0]
response = requests.get(f"{BASE_URL}/messages/{message_id}")
message = response.json()
print(f"Subject: {message['subject']}")
print(f"Body: {message['body'][:100]}...")

# Mark as read
response = requests.post(f"{BASE_URL}/messages/{message_id}/mark-as-read")
print(response.json()['message'])

# Delete message (uncomment to actually delete)
# response = requests.delete(f"{BASE_URL}/messages/{message_id}")
# print(response.json()['message'])
```

---

## Interactive API Documentation

### Swagger UI (Recommended)
Open in browser: **http://localhost:8000/docs**

Features:
- Interactive endpoint testing
- Request/response examples
- Schema documentation
- Try out API calls directly

### ReDoc
Open in browser: **http://localhost:8000/redoc**

Features:
- Clean, readable documentation
- Code samples in multiple languages
- Schema definitions

### OpenAPI Specification
Download the spec: **http://localhost:8000/openapi.json**

Use this to:
- Generate client libraries
- Import into Postman
- Create mock servers

---

## Error Handling

### 404 Not Found
```bash
curl http://localhost:8000/messages/invalid_id
```
```json
{
  "detail": "Message not found: invalid_id"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Failed to retrieve messages: [error details]"
}
```

### 422 Validation Error (invalid parameters)
```bash
curl "http://localhost:8000/messages?max_results=200"  # Max is 100
```
```json
{
  "detail": [
    {
      "type": "less_than_equal",
      "loc": ["query", "max_results"],
      "msg": "Input should be less than or equal to 100"
    }
  ]
}
```

---

## Testing the Service

### Unit Tests (No Gmail API needed)
```bash
uv run pytest src/services/mail_client_service/tests/ -v
```

### Integration Test (Requires Gmail credentials)
```bash
# Start the service
uv run python run_service.py &

# In another terminal, test with real API
curl http://localhost:8000/messages

# Stop the service
pkill -f uvicorn
```

---

## Development Workflow

1. **Start service in development mode:**
   ```bash
   uv run python run_service.py
   ```
   - Auto-reloads on code changes
   - Detailed logging

2. **Make API calls** using curl, browser, or Swagger UI

3. **View logs** in the terminal running the service

4. **Run tests** after changes:
   ```bash
   uv run pytest src/services/mail_client_service/tests/ -v
   uv run ruff check src/services/mail_client_service/
   ```

---

## Next Steps

- Create a Python client adapter (auto-generated from OpenAPI spec)
- Add authentication to protect endpoints
- Implement pagination for large message lists
- Add filtering options (by sender, date, unread status)
- Create async endpoints for better performance
- Deploy to a cloud service (AWS, GCP, etc.)
