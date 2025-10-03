"""E2E test: exercise the service adapter against a running mail_client_service.

This test is intended to run against real infrastructure (a running service
and a Gmail account with valid credentials). It will be skipped when no
credentials or service are available so it doesn't fail CI unintentionally.
"""

import logging
import os
from pathlib import Path

import httpx
import pytest

import mail_client_api
from mail_client_service_adapter import adapter_impl

pytestmark = pytest.mark.e2e

logger = logging.getLogger(__name__)

# Unsure which one should be used
# @pytest.mark.local_credentials
@pytest.mark.circleci
def test_service_adapter_can_reach_service_and_gmail() -> None:
    """Use the service adapter to list messages and fetch one message detail.

    Steps:
    - ensure credentials or env vars exist (otherwise skip)
    - ensure the mail service is reachable (health endpoint)
    - register the adapter to talk to the service
    - call get_messages and then get_message for one message
    """
    # Workspace root detection (same convention used in other E2E tests)
    workspace_root = Path(__file__).parent.parent.parent

    credentials_file = workspace_root / "credentials.json"
    token_file = workspace_root / "token.json"

    required_env_vars = [
        "GMAIL_CLIENT_ID",
        "GMAIL_CLIENT_SECRET",
        "GMAIL_REFRESH_TOKEN",
    ]

    # If no credential files and no env vars, skip the test
    if not credentials_file.exists() and not token_file.exists():
        missing = [v for v in required_env_vars if not os.environ.get(v)]
        if missing:
            pytest.skip(f"No credentials found and missing env vars: {missing}")

    # Determine service URL (allow override via env var)
    service_url = os.environ.get("MAIL_CLIENT_SERVICE_URL", "http://localhost:8000")

    # Check service health before proceeding
    health_url = service_url.rstrip("/") + "/health"
    try:
        resp = httpx.get(health_url, timeout=5.0)
        if resp.status_code != httpx.codes.OK:
            pytest.skip(f"Mail service unhealthy at {health_url}: status={resp.status_code}")
    except httpx.RequestError as exc:
        pytest.skip(f"Mail service not reachable at {health_url}: {exc}")

    # Register adapter to point at the running service
    adapter_impl.register(service_url=service_url)

    # Create client (non-interactive) and exercise it
    client = mail_client_api.get_client(interactive=False)

    # Try fetching messages
    messages = list(client.get_messages(max_results=5))

    if not messages:
        pytest.skip("No messages returned from Gmail account - cannot validate E2E flow")

    # Validate first message and fetch its details
    first = messages[0]
    assert getattr(first, "id", None), "Message must have an id"
    assert isinstance(first.subject, (str, type(None)))
    assert isinstance(first.from_, (str, type(None)))

    # Fetch full message detail via the service-backed client
    detail = client.get_message(first.id)
    # Basic sanity checks
    assert detail.id == first.id
    assert isinstance(detail.body, (str, type(None)))

    # Optionally mark as read if supported -- don't fail the test if operation fails
    try:
        _ = client.mark_as_read(first.id)
    except Exception as e:
        logger.warning("Failed to mark message as read (ignored): %s", e)
