"""Main module for demonstrating the mail client."""

# ta-assignment/main.py

import contextlib
import logging

import gmail_client_impl  # noqa: F401
import mail_client_api

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    """Initialize the client and demonstrate all mail client methods."""
    # Now, get_client() returns a GmailClient instance...
    # use interactive=True to use credentials.json to get token.json, then use interative=False
    client = mail_client_api.get_client(interactive=False)
    logger.info("\n")
    logger.info("Successfully authenticated and connected to the Gmail API.")

    # Test 1: Get messages (existing functionality)
    logger.info("\n")
    logger.info("=== TEST 1: Fetching Messages ===")
    messages = list(client.get_messages(max_results=3))

    if not messages:
        logger.info("No messages found in inbox.")
        return

    for i, msg in enumerate(messages, 1):
        # fmt: off
        logger.info(
            f"Message {i}:\n"
            f"  ID: {msg.id}\n"
            f"  Subject: {msg.subject}\n"
            f"  From: {msg.from_}\n"
            f"  Date: {msg.date}\n"
        )
        # fmt: on

    # Test 2: Get a specific message by ID
    if messages:
        test_message_id = messages[0].id
        logger.info("\n")
        logger.info(f"=== TEST 2: Getting Specific Message (ID: {test_message_id}) ===")

        with contextlib.suppress(Exception):
            specific_msg = client.get_message(test_message_id)
            logger.info(
                f"Successfully retrieved message:\n"
                f"  Subject: {specific_msg.subject}\n"
                f"  From: {specific_msg.from_}\n"
                f"  Date: {specific_msg.date}\n"
            )

    # Test 3: Mark a message as read
    if messages:
        test_message_id = messages[0].id
        logger.info("\n")
        logger.info(f"=== TEST 3: Marking Message as Read (ID: {test_message_id}) ===")
        with contextlib.suppress(Exception):
            success = client.mark_as_read(test_message_id)
            if success:
                logger.info("✓ Message marked as read successfully\n")
            else:
                logger.info("✗ Failed to mark message as read\n")

    # Test 4: Delete a message (WARNING: This is destructive and DOES NOT send to trash!)
    # Only test if we have more than one message to avoid deleting all messages
    if len(messages) > 1:
        logger.info("\n")
        logger.info("=== TEST 4: Delete Message ===")
        # Ask for confirmation before deleting
        delete_message_id = messages[-1].id  # Delete the last message
        logger.info(f"About to delete message ID: {delete_message_id}")
        logger.info(f"Subject: {messages[-1].subject}")

        try:
            confirmation = input("Type 'DELETE' to confirm deletion: ")
            if confirmation == "DELETE":
                success = client.delete_message(delete_message_id)
                if success:
                    logger.info("Message with ID %s deleted.", delete_message_id)
                else:
                    logger.info("Failed to delete message with ID %s.", delete_message_id)
        except EOFError:
            # This means that CircleCI or another non-interactive environment is not going to actually delete anything
            pass
    else:
        pass

    logger.info("Demo complete.")


if __name__ == "__main__":
    main()
