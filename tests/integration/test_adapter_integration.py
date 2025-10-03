"""Integration Tests for the ServiceAdapterClient.

These tests verify that the ServiceAdapterClient can successfully communicate
with a running instance of the mail_client_service.

The test suite automatically manages the service subprocess.
"""

import os
import subprocess
import time

import pytest
from mail_client_api.message import Message
from mail_client_service_adapter.adapter_impl import ServiceAdapterClient

# Get the service URL from environment variables, with a default
SERVICE_URL = os.environ.get("SERVICE_URL", "http://127.0.0.1:8000")


@pytest.fixture(scope="session")
def managed_service():
    """Starts and stops the mail service as a subprocess for the test session."""
    command = ["python", "run_service.py"]
    print(f"\nStarting service with command: '{' '.join(command)}'")
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )

    # Allow time for the service to initialize.
    # A more robust implementation would poll a health check endpoint.
    time.sleep(5)

    # Verify the service started and is still running
    if process.poll() is not None:
        stdout, stderr = process.communicate()
        pytest.fail(
            f"Service terminated unexpectedly. Exit code: {process.returncode}\n"
            f"--- STDOUT ---\n{stdout}\n"
            f"--- STDERR ---\n{stderr}"
        )

    print(f"Service started successfully with PID: {process.pid}")

    yield SERVICE_URL  # Provide the URL to dependent fixtures

    # --- Teardown ---
    print(f"\nTerminating service (PID: {process.pid})...")
    process.terminate()
    try:
        process.wait(timeout=10)
        print("Service terminated gracefully.")
    except subprocess.TimeoutExpired:
        print("Service did not terminate in time, killing it.")
        process.kill()


@pytest.fixture(scope="module")
def client(managed_service: str) -> ServiceAdapterClient:
    """Provides a ServiceAdapterClient instance for the tests.

    This fixture depends on the `managed_service` to ensure the service
    is running before any client connections are attempted.
    """
    adapter_client = ServiceAdapterClient(service_url=managed_service)

    # Retry connecting to the service, as it might still be initializing
    max_retries = 10
    last_exception = None
    for i in range(max_retries):
        try:
            list(adapter_client.get_messages(max_results=1))
            print(f"Successfully connected to service at {managed_service}")
            return adapter_client
        except Exception as e:
            last_exception = e
            print(f"Attempt {i + 1}/{max_retries} failed to connect: {e}")
            time.sleep(2)

    pytest.fail(
        f"Could not connect to the managed service at {managed_service} "
        f"after {max_retries} attempts. Last error: {last_exception}"
    )


@pytest.mark.integration
def test_full_message_lifecycle(client: ServiceAdapterClient):
    """Tests a full lifecycle: list -> get -> mark_as_read -> delete -> verify."""
    # 1. List messages and get the ID of the first one
    messages = list(client.get_messages(max_results=10))
    assert messages, "Service did not return any messages. Cannot proceed with the test."
    
    target_message_summary = messages[0]
    assert isinstance(target_message_summary, Message)
    message_id = target_message_summary.id
    print(f"Selected message with ID: {message_id} for testing.")

    # 2. Get the full details of the message
    detailed_message = client.get_message(message_id)
    assert detailed_message is not None
    assert detailed_message.id == message_id
    assert detailed_message.subject == target_message_summary.subject
    assert detailed_message.from_ == target_message_summary.from_
    # The body should be populated in the detailed view
    assert detailed_message.body, "Message body should not be empty in detailed view."
    print(f"Successfully fetched details for message {message_id}.")

    # 3. Mark the message as read
    read_success = client.mark_as_read(message_id)
    assert read_success, f"Failed to mark message {message_id} as read."
    print(f"Successfully marked message {message_id} as read.")

    # 4. Delete the message
    delete_success = client.delete_message(message_id)
    assert delete_success, f"Failed to delete message {message_id}."
    print(f"Successfully deleted message {message_id}.")

    # 5. Verify the message is deleted by trying to get it again
    with pytest.raises(ValueError, match=f"Failed to retrieve message {message_id}"):
        client.get_message(message_id)
    print(f"Verified that message {message_id} is no longer accessible.")
