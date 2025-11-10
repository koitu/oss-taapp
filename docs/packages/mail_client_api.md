# Mail Client API

`mail_client_api` defines the abstract `Client` contract and the `Message` abstractions for the project. It contains no concrete logic and intentionally has minimal dependencies.

Key points:

- Provides `Client` ABC with methods: `get_message`, `delete_message`, `mark_as_read`, `get_messages`
- Exposes a factory function `get_client` which implementations override at import time
- Designed for dependency injection and clear separation of interface vs implementation

See `src/mail_client_api/README.md` for examples and deeper documentation.
