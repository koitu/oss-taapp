# Phase 1: Chat + AI + Tickets Integration

This document describes the Phase 1 integration that connects Discord (Chat) → AI (Claude/OpenAI) → Trello (Tickets).

## Architecture Overview

The integration implements a pipeline where:
1. User sends a natural language message in Discord
2. AI analyzes the intent and extracts structured data
3. System executes the appropriate ticket operation
4. Response is sent back to the user via Discord

## User Flow Example

```
User: "Create a ticket for fixing the login bug"
  ↓
Discord → AI Service (with tool schema)
  ↓
AI Response: {"action": "create_ticket", "parameters": {"title": "Fix login bug"}}
  ↓
Execute ticket operation on Trello
  ↓
Discord: "✅ Created ticket: **Fix login bug**"
```

## Components

### 1. Tool Schema ([ticket_tools.py](src/ospsd_service/src/ospsd_service/ticket_tools.py:6))

Defines the structured format for AI to understand and respond with ticket operations:

**Available Actions:**
- `create_ticket` - Create a new ticket
- `list_tickets` - List recent open tickets
- `get_ticket` - Get details of a specific ticket
- `close_ticket` - Close/archive a ticket
- `update_ticket` - Update a ticket's title or description
- `chat_response` - Respond conversationally (no ticket action)

**Key Functions:**
- `TICKET_TOOLS_SCHEMA` - JSON schema defining the action/parameters structure
- `get_system_prompt_with_tools()` - Generates system prompt explaining operations to AI
- `validate_tool_call()` - Validates AI responses have required parameters

### 2. Operation Handlers ([ticket_handlers.py](src/ospsd_service/src/ospsd_service/ticket_handlers.py:13))

Executes the actual Trello operations based on AI's structured responses:

**Handler Functions:**
- `handle_create_ticket()` - Creates a card in Trello
- `handle_list_tickets()` - Lists recent cards with preview
- `handle_get_ticket()` - Shows full ticket details
- `handle_close_ticket()` - Deletes/archives a card
- `handle_update_ticket()` - Updates card title/description
- `handle_chat_response()` - Returns conversational message
- `execute_tool_call()` - Routes to appropriate handler

All handlers include error handling for authentication, not found, and general API errors.

### 3. OSPSD Service Integration ([main.py](src/ospsd_service/src/ospsd_service/main.py:126))

The Discord bot service has been updated to:

1. **Initialize Trello Client** - Sets up connection with API token
2. **Get Default Board/List** - Finds or creates default board and list at startup
3. **Process Messages** - New message handling pipeline:
   - Receives Discord message
   - Generates system prompt with tool definitions
   - Calls AI with `response_schema=TICKET_TOOLS_SCHEMA`
   - Parses structured JSON response
   - Validates the tool call
   - Executes the operation via handlers
   - Sends result back to Discord

**Key Changes:**
- Added `get_trello_client()` function
- Added `initialize_trello_defaults()` async function
- Updated `handle_message()` to use tool calling pipeline
- Added error handling for JSON parsing and tool validation

## Configuration

### Environment Variables

Added to `.env`:
```bash
TRELLO_API_KEY=<your-api-key>
TRELLO_API_SECRET=<your-token>  # Actually the OAuth token, not secret
REDIRECT_URI=http://localhost:8000/trello/callback
```

### Dependencies

The following workspace members are now integrated:
- `kanban_client_api` - Abstract interface for ticketing systems
- `trello_client_impl` - Concrete Trello implementation

## Example Commands

Users can now type natural language commands in Discord:

**Creating Tickets:**
- "Create a ticket for fixing the login bug"
- "Make a ticket to update the docs with description: Add API examples"

**Listing Tickets:**
- "Show my recent tickets"
- "List 5 open tickets"

**Getting Details:**
- "Show me ticket ABC123"
- "Get details for ticket XYZ789"

**Closing Tickets:**
- "Close ticket ABC123"
- "Archive ticket XYZ789"

**Updating Tickets:**
- "Update ticket ABC123 with title 'New Title'"
- "Change the description of ticket ABC123 to 'Updated description'"

**General Chat:**
- "Hello!"
- "How are you?"
- "What can you do?"

## Error Handling

The integration includes comprehensive error handling:

1. **Authentication Errors** - Invalid API key/token
2. **Not Found Errors** - Ticket/board/list doesn't exist
3. **JSON Parsing Errors** - AI returns invalid JSON
4. **Validation Errors** - Missing required parameters
5. **General API Errors** - Network issues, rate limits, etc.

All errors return user-friendly messages prefixed with ❌.

## Testing

To test the integration:

1. **Start the OSPSD service:**
   ```bash
   uv run python -m ospsd_service.main
   ```

2. **Send a test message in Discord:**
   - "Create a ticket for testing"
   - Verify bot creates the ticket in Trello
   - Check bot responds with confirmation

3. **Test other operations:**
   - List tickets
   - Get ticket details
   - Update a ticket
   - Close a ticket

## Success Indicators

The integration is working correctly when:

✅ Bot initializes and connects to Trello on startup
✅ Natural language commands are correctly interpreted by AI
✅ Ticket operations execute successfully in Trello
✅ User receives clear confirmation/error messages
✅ Chat responses work for non-ticket queries

## Next Steps (Future Phases)

- **Phase 2:** Add telemetry/logging for ticket operations
- **Phase 3:** Support multiple boards/lists per user
- **Phase 4:** Add ticket assignment and labels
- **Phase 5:** Implement ticket search and filters

## Files Modified/Created

### New Files:
- [src/ospsd_service/src/ospsd_service/ticket_tools.py](src/ospsd_service/src/ospsd_service/ticket_tools.py) - Tool schema and prompts
- [src/ospsd_service/src/ospsd_service/ticket_handlers.py](src/ospsd_service/src/ospsd_service/ticket_handlers.py) - Operation handlers

### Modified Files:
- [src/ospsd_service/src/ospsd_service/main.py](src/ospsd_service/src/ospsd_service/main.py:126) - Updated message handling pipeline
- [.env](.env) - Added Trello credentials
- [pyproject.toml](pyproject.toml) - Added workspace members

## Troubleshooting

### "TRELLO_API_SECRET not set in environment"
- Ensure `.env` file contains `TRELLO_API_SECRET=<your-token>`
- Token is obtained from https://trello.com/app-key → Click "Token"

### "Authentication failed"
- Verify token is valid and not expired
- Check API key matches the token

### "No boards found, creating default board"
- Normal on first run - service creates "OSPSD Tickets" board automatically

### AI returns unparseable JSON
- Check AI model is set correctly (Claude or OpenAI)
- Verify system prompt is being passed correctly
- Check `response_schema` parameter is set
