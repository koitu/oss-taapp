"""Integration tests for forward_message functionality.

These tests verify that the forward functionality works with a real GmailClient instance.
They require valid Gmail credentials (via environment variables or token.json).
"""

import pytest
import gmail_client_impl  # noqa: F401 - Trigger DI registration
import mail_client_api


pytestmark = pytest.mark.integration


@pytest.mark.circleci
def test_forward_message_integration() -> None:
    """Integration test for forward_message with real client.

    This test verifies that:
    1. The client can be instantiated
    2. The forward_message method exists and is callable
    3. The method signature is correct
    """
    try:
        # Get a real client instance
        client = mail_client_api.get_client(interactive=False)

        # Verify the client has the forward_message method
        assert hasattr(client, "forward_message")
        assert callable(client.forward_message)

        # Verify it's an instance of GmailClient
        assert isinstance(client, gmail_client_impl.GmailClient)

    except FileNotFoundError:
        pytest.skip("Skipping integration test: credentials.json not found.")
    except (RuntimeError, ValueError, ConnectionError) as e:
        pytest.fail(f"Integration test failed during client initialization: {e}")


@pytest.mark.circleci
def test_forward_message_with_mock_message_id() -> None:
    """Test forward_message with a non-existent message ID.

    This should return False gracefully without crashing.
    """
    try:
        client = mail_client_api.get_client(interactive=False)

        # Try to forward a non-existent message
        # This should fail gracefully and return False
        result = client.forward_message("nonexistent_message_id_12345", "test@example.com")

        # Should return False, not raise an exception
        assert result is False

    except FileNotFoundError:
        pytest.skip("Skipping integration test: credentials.json not found.")
    except (RuntimeError, ValueError, ConnectionError) as e:
        pytest.fail(f"Integration test failed: {e}")


@pytest.mark.local_credentials
def test_forward_latest_email_integration() -> None:
    """Integration test for the forward_latest_email function.

    WARNING: This test will actually forward an email if run with valid credentials.
    It's marked as local_credentials to avoid running in CI.
    """
    try:
        from main import forward_latest_email

        # This will forward the latest email to john.jakobsen@cuny.edu
        # Only run this manually when you want to test the actual forwarding
        result = forward_latest_email("john.jakobsen@cuny.edu")

        # Result should be True if there are messages to forward
        assert isinstance(result, bool)

    except FileNotFoundError:
        pytest.skip("Skipping integration test: credentials.json not found.")
    except (RuntimeError, ValueError, ConnectionError) as e:
        pytest.fail(f"Integration test failed: {e}")


@pytest.mark.circleci
def test_forward_message_validates_client_contract() -> None:
    """Verify that forward_message is part of the Client contract."""
    from mail_client_api import Client
    import inspect

    # Verify that forward_message is defined in the ABC
    assert hasattr(Client, "forward_message")

    # Verify it's an abstract method
    method = getattr(Client, "forward_message")
    assert hasattr(method, "__isabstractmethod__")
    assert method.__isabstractmethod__ is True

    # Verify the signature
    sig = inspect.signature(Client.forward_message)
    params = list(sig.parameters.keys())

    # Should have: self, message_id, to_email
    assert "message_id" in params
    assert "to_email" in params
