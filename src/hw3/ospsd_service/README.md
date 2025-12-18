# OSPSD Service
The OSPSD is a chat service that integrates Discord, a choice of AI backend, and a ticketing system to enable AI-powered conversational interactions and ticket management.

## Overview
OSPSD is a systems integration project that combines three core components:
- Chat Interface (Discord)
  - Discord Gateway Client: handles real-time Discord message events via WebSocket connection
  - Chat Interface: standardized abstraction for chat operations
- AI Service (OpenAI, Claude)
  - AI Interface: standardized abstraction for AI model interactions
- Ticket Management

## Usage

### Environment Variables
The following environment variables must be set in the environment or `.env` (see `.env.example` for an example)
```bash
NO_OAUTH=True

# Discord Configuration
DISCORD_CLIENT_ID=your-discord-client-id
DISCORD_CLIENT_SECRET=your-discord-client-secret
DISCORD_PUBLIC_KEY=your-discord-public-key
DISCORD_BOT_TOKEN=your-bot-token

# OpenAI API Key
OPENAI_API_KEY=
```

### Running the Program
Adding the bot to your server can be done by running then visiting the url generated.
```bash
uv run python generate_discord_auth_url.py
```

After adding the bot to your server you can control the bot using the `DISCORD_BOT_TOKEN` so we can start the service with:
```bash
uv run python -m ospsd_service.main
```
Now just go visit the server you added the bot to and talk to it!
