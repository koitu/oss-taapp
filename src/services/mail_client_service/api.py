"""module for fastAPI endpoints."""

# TODO: error handling, delete safety (trash instead?), logging, pagination for /messages # ruff: noqa: FIX002, TD002, TD003

import contextlib

from fastapi import FastAPI, HTTPException

import gmail_client_impl  # noqa: F401
import mail_client_api

client = mail_client_api.get_client(interactive=False)

app = FastAPI()


@app.get("/messages")
def get_emails() -> dict:
    """Get the summary of the 10 most recent emails."""
    messages = list(client.get_messages(max_results=10))

    result = {}
    for msg in messages:
        result[msg.id] = {
            "Subject": msg.subject,
            "From": msg.from_,
            "Date": msg.date,
        }

    return result


@app.get("/messages/{message_id}")
def get_email_contents(message_id: str) -> dict:
    """Get the contents of a single specified email."""
    with contextlib.suppress(Exception):
        msg = client.get_message(message_id)
        return {
            "ID": message_id,
            "Subject": msg.subject,
            "From": msg.from_,
            "Date": msg.date,
            "Body": msg.body,
        }

    raise HTTPException(status_code=404, detail="Error")


@app.post("/messages/{message_id}/mark-as-read")
def mark_email_read(message_id: str) -> dict:
    """Mark a specified email as read."""
    with contextlib.suppress(Exception):
        success = client.mark_as_read(message_id)
        if success:
            return {"Status": "Success"}

    raise HTTPException(status_code=404, detail="Error")


@app.delete("/messages/{message_id}")
def delete_email(message_id: str) -> dict:
    """Delete a specified email."""
    with contextlib.suppress(Exception):
        success = client.delete_message(message_id)
        if success:
            return {"Status": "Success"}

    raise HTTPException(status_code=404, detail="Error")
