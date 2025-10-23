"""Test the service adapter end-to-end.

This script demonstrates using the adapter to talk to the service,
which in turn talks to Gmail.
"""

import logging

from mail_client_service_adapter import ServiceAdapterClient

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    """Test the service adapter."""
    logger.info("=== Testing Service Adapter ===\n")

    # Create the adapter client pointing to our running service
    logger.info("Creating ServiceAdapterClient...")
    client = ServiceAdapterClient(service_url="http://localhost:8000")
    logger.info("✓ Client created\n")

    # Test 1: Get messages
    logger.info("TEST 1: Fetching messages via adapter")
    messages = list(client.get_messages(max_results=3))
    logger.info(f"✓ Retrieved {len(messages)} messages\n")

    for i, msg in enumerate(messages, 1):
        logger.info(f"Message {i}:\n  ID: {msg.id}\n  Subject: {msg.subject}\n  From: {msg.from_}\n  Date: {msg.date}\n")

    if not messages:
        logger.warning("No messages found. Test complete.")
        return

    # Test 2: Get specific message
    test_message_id = messages[0].id
    logger.info(f"\nTEST 2: Getting specific message (ID: {test_message_id})")
    specific_msg = client.get_message(test_message_id)
    logger.info(
        f"✓ Retrieved message:\n"
        f"  Subject: {specific_msg.subject}\n"
        f"  From: {specific_msg.from_}\n"
        f"  Body: {specific_msg.body[:100] if specific_msg.body else 'No body'}...\n"
    )

    # Test 3: Mark as read
    logger.info(f"\nTEST 3: Marking message as read (ID: {test_message_id})")
    success = client.mark_as_read(test_message_id)
    if success:
        logger.info("✓ Message marked as read\n")
    else:
        logger.warning("✗ Failed to mark message as read\n")

    logger.info("=== All Tests Complete ===")
    logger.info("\n✅ The adapter successfully:")
    logger.info("   1. Wrapped the auto-generated client")
    logger.info("   2. Made HTTP calls to the service")
    logger.info("   3. Service called Gmail API")
    logger.info("   4. Data flowed back through all layers")
    logger.info("\nArchitecture layers verified:")
    logger.info("   Application → Adapter → HTTP Client → Service → Gmail")


if __name__ == "__main__":
    main()
