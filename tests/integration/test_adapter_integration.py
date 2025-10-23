"""Integration tests for the ServiceAdapterClient.

Verify that the ServiceAdapterClient can successfully communicate
with a running instance of the mail_client_service.

The test suite automatically manages the service subprocess.
"""

import logging
import os
import subprocess
import time
from collections.abc import Generator

import pytest
from mail_client_api.message import Message
from mail_client_service_adapter.adapter_impl import ServiceAdapterClient

# Configure logging for test runs
logger = logging.getLogger(__name__)

# Get the service URL from environment variables, with a default
SERVICE_URL = os.environ.get("SERVICE_URL", "http://127.0.0.1:8000")


@pytest.fixture(scope="session")
def managed_service() -> Generator[str, None, None]:
    """Start and stop the mail service as a subprocess for the test session."""
    command = ["python", "run_service.py"]
    logger.info("Starting service with command: '%s'", " ".join(command))
    process = subprocess.Popen(  # noqa: S603
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )

    time.sleep(5)  # allow time for the service to initialize

    if process.poll() is not None:
        stdout, stderr = process.communicate()
        pytest.fail(
            f"Service terminated unexpectedly. Exit code: {process.returncode}\n"
            f"--- STDOUT ---\n{stdout}\n"
            f"--- STDERR ---\n{stderr}"
        )

    logger.info("Service started successfully with PID: %s", process.pid)

    yield SERVICE_URL

    # --- Teardown ---
    logger.info("Terminating service (PID: %s)...", process.pid)
    process.terminate()
    try:
        process.wait(timeout=10)
        logger.info("Service terminated gracefully.")
    except subprocess.TimeoutExpired:
        logger.warning("Service did not terminate in time, killing it.")
        process.kill()


@pytest.fixture(scope="module")
def client(managed_service: str) -> ServiceAdapterClient:
    """Provide a ServiceAdapterClient instance for the tests.

    This fixture depends on the `managed_service` to ensure the service
    is running before any client connections are attempted.
    """
    adapter_client = ServiceAdapterClient(service_url=managed_service)

    max_retries = 10
    last_exception = None
    for i in range(max_retries):
        try:
            list(adapter_client.get_messages(max_results=1))
            logger.info("Successfully connected to service at %s", managed_service)
            return adapter_client
        except Exception as e:
            last_exception = e
            logger.warning("Attempt %d/%d failed to connect: %s", i + 1, max_retries, e)
            time.sleep(2)

    pytest.fail(
        f"Could not connect to the managed service at {managed_service} "
        f"after {max_retries} attempts. Last error: {last_exception}"
    )


@pytest.mark.integration
def test_full_message_lifecycle(client: ServiceAdapterClient) -> None:
    """Test a full lifecycle: list -> get -> mark_as_read -> delete -> verify."""
    messages = list(client.get_messages(max_results=10))
    assert messages, "Service did not return any messages. Cannot proceed with the test."

    target_message_summary = messages[0]
    assert isinstance(target_message_summary, Message)
    message_id = target_message_summary.id
    logger.info("Selected message with ID: %s for testing.", message_id)

    detailed_message = client.get_message(message_id)
    assert detailed_message is not None
    assert detailed_message.id == message_id
    assert detailed_message.subject == target_message_summary.subject
    assert detailed_message.from_ == target_message_summary.from_
    assert detailed_message.body, "Message body should not be empty in detailed view."
    logger.info("Successfully fetched details for message %s.", message_id)

    read_success = client.mark_as_read(message_id)
    assert read_success, f"Failed to mark message {message_id} as read."
    logger.info("Successfully marked message %s as read.", message_id)

    delete_success = client.delete_message(message_id)
    assert delete_success, f"Failed to delete message {message_id}."
    logger.info("Successfully deleted message %s.", message_id)

    with pytest.raises(ValueError, match=f"Failed to retrieve message {message_id}"):
        client.get_message(message_id)
    logger.info("Verified that message %s is no longer accessible.", message_id)
