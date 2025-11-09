# Mail Client Service

FastAPI service that exposes the mail client functionality over HTTP. The service translates between HTTP requests and the `mail_client_api` abstraction.

Endpoints include `/messages`, `/messages/{message_id}`, `/messages/{message_id}/mark-as-read`, and `/health`.

See `src/services/mail_client_service/README.md` for full details and examples for running and testing the service.
