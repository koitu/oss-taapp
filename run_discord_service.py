"""Run the Discord client service with uvicorn.

This script starts the FastAPI Discord service on port 8001.

Usage:
    python run_discord_service.py

Or with uv:
    uv run python run_discord_service.py

"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "discord_client_service:app",
        host="127.0.0.1",
        port=8001,
        reload=True,
        log_level="info",
    )
