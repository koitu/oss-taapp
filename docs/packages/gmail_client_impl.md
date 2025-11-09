# Gmail Client Implementation

This package provides a concrete `mail_client_api.Client` implementation that talks to the Gmail API. It handles OAuth2 auth, token refresh, and returns `GmailMessage` objects compatible with the API.

Highlights:

- Interactive and non-interactive authentication modes
- OAuth2 token storage (`token.json`) and environment-variable overrides
- Implements all `Client` methods with Gmail-specific behaviour

Refer to `src/gmail_client_impl/README.md` for usage examples and setup instructions.
