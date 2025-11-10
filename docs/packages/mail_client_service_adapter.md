# Mail Client Service Adapter

Adapter that implements the `mail_client_api.Client` interface by wrapping the auto-generated OpenAPI client for the mail service.

Key responsibilities:

- Convert generated client models to `mail_client_api.Message` objects
- Provide `ServiceAdapterClient` implementing the `Client` ABC
- Expose `register()` helper to bind the adapter as the runtime factory

See `src/mail_client_service_adapter/README.md` for more details and examples.
