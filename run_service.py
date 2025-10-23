"""Run the mail client service locally.

This script starts the FastAPI service using uvicorn.
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "mail_client_service:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info",
    )
