# Python Application Template: A Component-Based Mail Client

[![CircleCI](https://dl.circleci.com/status-badge/img/gh/koitu/oss-taapp/tree/root.svg?style=svg)](https://dl.circleci.com/status-badge/redirect/gh/koitu/oss-taapp/tree/root)
[![Coverage](https://img.shields.io/badge/coverage-85%2B%25-brightgreen)](https://circleci.com/gh/ivanearisty/oss-taapp)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://python.org)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

This repository serves as a professional-grade template for a modern Python project. It demonstrates a robust, component-based architecture by building the core components for an AI-powered email assistant that interacts with the Gmail API.

The project emphasizes a strict separation of concerns, dependency injection, and a comprehensive, automated toolchain to enforce code quality and best practices.

## Architectural Philosophy

This project is built on the principle of "programming integrated over time." The architecture is designed to combat complexity and ensure the system is maintainable and evolvable.

- **Component-Based Design:** The system is broken down into four distinct, self-contained components. Each component has a single responsibility and can be "forklifted" out of this project to be used in another with minimal effort.
- **Interface-Implementation Separation:** Every piece of functionality is defined by an abstract **contract** implemented as an ABC (the "what") and fulfilled by a concrete **implementation** (the "how"). This decouples our business logic from specific technologies (like Gmail).
- **Dependency Injection:** Implementations are "injected" into the abstract contracts at runtime. This means consumers of the API only ever depend on the stable interface, not the volatile implementation details.

## Core Components

This repository is a `uv` workspace containing multiple related packages under `src/` plus a small `services/` folder. The codebase is component-oriented: each package focuses on a single responsibility and can be used independently or swapped via dependency injection.

- **`mail_client_api`**: The abstract contract (ABCs) for mail clients and message/value objects. Consumers depend on this stable API.
- **`gmail_client_impl`**: A concrete implementation of the mail client API that uses the Gmail APIs and OAuth credentials.
- **`mail_client_service_adapter`**: Adapter code that exposes an implementation behind the service API (handlers/translation logic).
- **`discord_client_impl`** and **`discord_client_service_adapter`**: Companion packages for Discord integration (implementation + adapter layer) — this repo contains Discord-related tools and OpenAPI generation helpers.
- **`chat_client_api`**: An API package present in `src/` that follows the same contract/implementation pattern for chat clients.
- **`ai_api`** and **`openai_client_impl`**: AI service abstractions and OpenAI implementation for AI-powered features.
- **`shared_telemetry`**: Reusable Prometheus-based telemetry for all services, tracking request latency, success/failure rates, and error metrics.
- **`clients`**: Generated OpenAPI client packages (for example `discord_client_service_client`)
- **`services/`**: Local HTTP services that expose component functionality (for example `services/discord_client_service`). These are small FastAPI apps used for integration and end-to-end testing.
- **`src/services/`**: Local HTTP services that expose component functionality (for example `src/services/discord_client_service`). These are small FastAPI apps used for integration and end-to-end testing.

Note: The exact packages in `src/` may evolve; see the `src/` directory for the current, authoritative list of workspace members.

## Project Structure

```
oss-taapp/                           # repository root
├── src/                             # Source packages (workspace members)
│   ├── chat_client_api/             # Chat client API package
│   ├── clients/                     # Generated API clients (e.g. discord_client_service_client and mail_client_service_client)
│   ├── discord_client_impl/         # Discord implementation package
│   ├── discord_client_service_adapter/  # Discord adapter layer
│   ├── gmail_client_impl/           # Gmail implementation of mail client API
│   ├── mail_client_api/             # Abstract mail client contract (Client, Message)
│   ├── mail_client_service_adapter/ # Adapter that exposes implementations as the service API
│   ├── services/                    # Small FastAPI services (e.g. discord_client_service and mail_client_service)
├── tests/                           # Integration and E2E tests
│   ├── integration/
│   └── e2e/
├── docs/                            # Documentation source files and generated site (site/)
├── .circleci/                       # CI configuration (CircleCI)
├── Dockerfile                        # Dockerfile to containerize services
├── generate_discord_openapi.py       # helper to generate OpenAPI clients for Discord
├── run_service.py                    # run a local service (FastAPI) for testing  --> Gmail
├── run_discord_service.py            # run the Discord-oriented service  --> Discord
├── main.py                           # Main demo / entrypoint script
├── pyproject.toml                    # Project configuration (dependencies, tools)
├── uv.lock                           # Locked dependency versions (workspace)
├── credentials.json                  # Local Google OAuth credentials (optional)
├── token.json                        # OAuth token created after initial auth
├── .env.example                      # Sample .env file
├── .md files                         # Top-level project markdown documents
├── CONTRIBUTING.md                   # Contribution guidelines
├── DESIGN.md                         # Design notes
├── Discord.md                        # Discord integration notes
└── README.md                         # This file
```

## Project Setup

### 1. Prerequisites

- Python 3.11 or higher
- `uv` – A fast, all-in-one Python package manager.

### 2. Initial Setup

1.  **Install `uv`:**

    ```bash
    # macOS / Linux
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Windows (PowerShell)
    irm https://astral.sh/uv/install.ps1 | iex
    ```

2.  **Clone the Repository:**

    ```bash
    git clone <your-repository-url>
    cd ta-assignment
    ```

3.  **Set Up Gmail Credentials:**

    - Follow the [Google Cloud instructions](https://developers.google.com/gmail/api/quickstart/python#authorize_credentials_for_a_desktop_application) to enable the Gmail API and download your OAuth 2.0 credentials.
    - Rename the downloaded file to `credentials.json` and place it in the root of this project. Running the demo or the service for the first time will initiate the OAuth flow and create a `token.json` file with the user tokens.
    - **Alternative (CI/CD / non-interactive):** Instead of using a local `credentials.json` and interactive flow, you can provide credentials via environment variables:
      ```powershell
      $env:GMAIL_CLIENT_ID = "your_client_id"
      $env:GMAIL_CLIENT_SECRET = "your_client_secret"
      $env:GMAIL_REFRESH_TOKEN = "your_refresh_token"
      ```
    - **Security note:** Credential files and tokens contain sensitive data and are ignored by `.gitignore`. Keep them out of source control and use secret management in CI/CD.

4.  **Set Up Discord Credentials (optional - for Discord integration):**

    - Create a Discord application at https://discord.com/developers/applications and register a new application for your bot or OAuth client.
    - Under the application settings, create a bot and/or configure OAuth2 Redirect URIs for any web-based flows.
    - Record the following values from the Discord developer dashboard and provide them to the application as environment variables:
      - `DISCORD_CLIENT_ID` — the application's client ID
      - `DISCORD_CLIENT_SECRET` — the application's client secret
      - `DISCORD_REDIRECT_URI` — the OAuth redirect URI used for OAuth flows
      - `DISCORD_PUBLIC_KEY` — public key used to verify interactions (if using interactions/webhooks)
      - `DISCORD_BOT_TOKEN` — bot token
    - Example (PowerShell):
      ```powershell
      $env:DISCORD_CLIENT_ID = "your_discord_client_id"
      $env:DISCORD_CLIENT_SECRET = "your_discord_client_secret"
      $env:DISCORD_REDIRECT_URI = "https://your-app/callback"
      $env:DISCORD_PUBLIC_KEY = "your_public_key"
      $env:DISCORD_BOT_TOKEN = "your_bot_token"
      ```
    - **Notes:** Discord credentials are not required for the Gmail-focused parts of this template. Use Discord credentials only if you plan to run the Discord-related services or adapters included in `src/` and `services/`.

5.  **Create and Sync the Virtual Environment:**
    This single command creates a `.venv` folder and installs all packages (including workspace members and development tools) defined in `uv.lock`.

    ```bash
    uv sync --all-packages --extra dev
    ```

6.  **Activate the Virtual Environment:**

    ```bash
    # macOS / Linux
    source .venv/bin/activate
    # Windows (PowerShell)
    .venv\Scripts\Activate.ps1
    ```

7.  **Perform Initial Authentication (Gmail):**
    Run the main application once (or the Gmail service) to perform the interactive OAuth flow. This will open a browser window for you to grant permission and will create a `token.json` file containing the user tokens.
    ```powershell
    uv run python main.py
    ```
    If you're using CI/CD with pre-provisioned refresh tokens, this step is not required.

## Development Workflow

All commands should be run from the project root with the virtual environment activated.

### Running the Application

To run the main demonstration script:

```bash
uv run python main.py
```

To run the Discord service (local FastAPI service):

```powershell
uv run python run_discord_service.py
```

Then open http://localhost:8001/docs in your browser to view the Discord service API docs.

### Running the Toolchain

- **Linting & Formatting (Ruff):**
  The project uses Ruff with comprehensive rules configured in `pyproject.toml`.

  ```bash
  # Check for issues
  uv run ruff check .
  # Automatically fix issues
  uv run ruff check . --fix
  # Check formatting
  uv run ruff format --check .
  # Apply formatting
  uv run ruff format .
  ```

- **Static Type Checking (MyPy):**

  ```bash
  uv run mypy src tests
  ```

- **Testing (Pytest):**

  I'd recommend only running: `uv run pytest src/ tests/ -m "not local_credentials" -v` for simplicity.

  The project uses a comprehensive testing strategy with different test categories.

  ```bash
  # Run all tests (includes unit, integration, and e2e tests)
  uv run pytest

  # Run only unit tests (fast, no external dependencies - from src/ directories)
  uv run pytest src/

  # Run all tests except those requiring local credential files
  uv run pytest src/ tests/ -m "not local_credentials"

  # Run only integration tests (requires environment variables or credentials)
  uv run pytest -m integration

  # Run only end-to-end tests (requires credentials)
  uv run pytest -m e2e

  # Run only CircleCI-compatible tests (CI/CD environment)
  uv run pytest -m circleci

  # Run tests with coverage reporting
  uv run pytest --cov=src --cov-report=term-missing
  ```

- **(Optional) Pre-commit Checks**

  To automatically running ruff linting/format, mypy, and unit tests before committing.

  ```bash
  uv tool install pre-commit --with pre-commit-uv
  uv run pre-commit install

  # Run against all files (optional)
  uv run pre-commit run --all-files
  ```

### Viewing Documentation

This project uses MkDocs for documentation.

```bash
uv run mkdocs build
# Start the live-reloading documentation server
uv run mkdocs serve
```

Open your browser to `http://127.0.0.1:8000` to view the site.

## Telemetry & Observability

All services are instrumented with **Prometheus metrics** to track performance and health:

### Metrics Collected

- **Request Latency**: HTTP request duration in seconds (histogram with p50, p95, p99)
- **Success Rate**: Percentage of successful requests (2xx status codes)
- **Failure Rate**: Percentage of failed requests (4xx/5xx status codes)
- **Request Volume**: Total number of requests per endpoint

### Accessing Metrics

Each service exposes a `/metrics` endpoint:

```bash
# Discord Service (port 8001)
curl http://localhost:8001/metrics

# OpenAI Service (port 8002)
curl http://localhost:8002/metrics

# Mail Service (port 8000)
curl http://localhost:8000/metrics
```

### Testing Telemetry

Run the telemetry verification script:

```bash
# Start all services first
uv run python run_discord_service.py &  # Port 8001
uv run uvicorn openai_client_service.main:app --port 8002 &
uv run python run_service.py &  # Port 8000

# Verify metrics are being collected
uv run python test_telemetry.py
```

### Monitoring Dashboard

For production deployments on Google Cloud Run, use **Google Cloud Operations** (formerly Stackdriver) to visualize metrics. For local development, you can use Prometheus + Grafana.

See [docs/telemetry.md](docs/telemetry.md) for detailed documentation on:

- Metric definitions and labels
- Integration with monitoring systems
- Adding telemetry to new services
- Best practices and troubleshooting

## Testing Infrastructure

The project implements a sophisticated testing strategy designed for both local development and CI/CD environments:

### Test Categories

- **Unit Tests** (`src/*/tests/`): Fast, isolated tests with mocked dependencies
- **Integration Tests** (`tests/integration/`): Tests that verify component interactions
- **End-to-End Tests** (`tests/e2e/`): Full application workflow tests
- **CircleCI Tests**: CI/CD-compatible tests that handle missing credentials gracefully
- **Local Credentials Tests**: Tests that require `credentials.json` or `token.json` files

### Test Markers

The project uses pytest markers to categorize tests:

```bash
@pytest.mark.unit              # Fast unit tests
@pytest.mark.integration       # Integration tests
@pytest.mark.e2e              # End-to-end tests
@pytest.mark.circleci         # CI/CD compatible
@pytest.mark.local_credentials # Requires local auth files
```

### Authentication in Tests

The testing infrastructure handles different authentication scenarios for each external service. Below are the details for Gmail and Discord.

#### Gmail

- **Local Development**: Uses `credentials.json` and `token.json` files
- **CI/CD Environment**: Uses environment variables (`GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN`)
- **Missing Credentials**: Tests fail fast with clear error messages (no hanging)

#### Discord

- **Local Development**: Provide the Discord credentials as environment variables in your shell or in a `.env` file before running tests. The repository expects the following variables when running Discord-related tests locally:

  - `DISCORD_CLIENT_ID`
  - `DISCORD_CLIENT_SECRET`
  - `DISCORD_REDIRECT_URI`
  - `DISCORD_PUBLIC_KEY`
  - `DISCORD_BOT_TOKEN`

- **CI/CD Environment**: In CI or other non-interactive environments, supply the same Discord values via your CI secret management (for example, repository secrets or a secret manager). Tests that require Discord credentials will read these environment variables and behave accordingly.

- **Missing Credentials**: Tests that require Discord credentials will fail fast with a clear error message indicating which environment variables are missing. They will not wait for interactive input.

## Continuous Integration

The project includes a comprehensive CircleCI configuration (`.circleci/config.yml`) with:

- **All Branches**: Unit tests, linting, and CI-compatible tests
- **Main/Develop**: Additional integration tests with real Gmail API calls
- **Artifacts**: Coverage reports, test results, and build summaries

See `docs/circleci-setup.md` for detailed CI/CD setup instructions.

## Development Workflow

### Quick Start

1. **Install dependencies**: `uv sync --all-packages --extra dev`
2. **Run tests**: `uv run pytest tests/ -v` or `uv run pytest src/ tests/ -m "not local_credentials" -v`
3. **Check code quality**: `uv run ruff check . && uv run ruff format --check .`
4. **Fix formatting**: `uv run ruff format .`
5. **View documentation**: `uv run mkdocs serve`
6. **Run backend services**:

   - **Gmail backend (local FastAPI service)** — runs the Gmail-focused service (default port 8000):

     ```powershell
     uv run python run_service.py
     ```

     Then open `http://localhost:8000/docs` to view the Gmail service API docs.

   - **Discord backend (local FastAPI service)** — runs the Discord-focused service (default port 8001):

     ```powershell
     uv run python run_discord_service.py
     ```

     Then open `http://localhost:8001/docs` to view the Discord service API docs.

### Best Practices

- Run unit tests (`uv run pytest src/`) during development for fast feedback
- Use integration tests (`uv run pytest -m integration`) to verify component interactions
- Run full test suite (`uv run pytest`) before pushing to ensure CI compatibility
- The CircleCI pipeline provides automated validation on every push

## Running with Docker

The application can be containerized using Docker for easy local testing and distribution. The examples below show how to build and run the Discord-focused service packaged as `discord-service`.

### Building the Docker Image

```bash
docker build -t discord-service .
```

This builds a Docker image named `discord-service` using the provided Dockerfile. The build process:

- Uses Python 3.11 slim base image
- Installs `uv` for dependency management
- Copies project files and installs dependencies
- Exposes port 8001 for the Discord FastAPI service (local default)

### Running the Container

**Basic run (Discord FastAPI service):**

```bash
docker run -p 8001:8001 discord-service
```

The service will be available at `http://localhost:8001`. You can access:

- API documentation: `http://localhost:8001/docs`

**Note:** If you visit `http://localhost:8001/` (root path), you may see a 404 error. This is normal — the service exposes specific endpoints (for example the Discord adapter endpoints). Use `/docs` to view available routes.

**Running with Discord credentials (environment variables):**

```bash
docker run -p 8001:8001 \
    -e DISCORD_CLIENT_ID="your_client_id" \
    -e DISCORD_CLIENT_SECRET="your_client_secret" \
    -e DISCORD_REDIRECT_URI="https://your-app/callback" \
    -e DISCORD_PUBLIC_KEY="your_public_key" \
    -e DISCORD_BOT_TOKEN="your_bot_token" \
    discord-service
```

**Running the Discord service demo:**

```bash
docker run discord-service uv run python run_discord_service.py
```

**Running with credential files (local .env):**
If you prefer to supply credentials via a file, you can mount a local `.env` (or another file) into the container. Example (host current directory):

```bash
docker run -p 8001:8001 \
    -v $(pwd)/.env:/app/.env \
    discord-service
```

The container will read environment variables from the mounted file if your entrypoint or startup logic loads `.env` values.

## Deployment

The Discord service is deployed on **Google Cloud Run** with the following URL:

[http://discord-service-755226003273.us-central1.run.app/docs](http://discord-service-755226003273.us-central1.run.app/docs)

### Platform

- **Cloud Run** (fully managed)
- **Region:** `us-central1`
- **Port:** `8000`
- **Authentication:** Allow unauthenticated access for public API

### Environment Variables

Secrets are securely stored in **Google Secret Manager**.

- `DISCORD_CLIENT_ID`
- `DISCORD_CLIENT_SECRET`
- `DISCORD_REDIRECT_URI`
- `DISCORD_PUBLIC_KEY`
- `DISCORD_BOT_TOKEN`

### CI/CD Pipeline

The deployment pipeline is automated using **CircleCI** with the following steps:

1. **Checkout Code**  
   Pulls the latest code from the repository.

2. **Setup Remote Docker**  
   Enables Docker builds within the CI environment.

3. **Configure GCP Authentication**

   - The service account key is stored in the `GOOGLE_SERVICE_KEY` environment variable.
   - Authenticate using the service account and set the project and region:
     ```bash
     gcloud auth activate-service-account --key-file=$HOME/gcloud-key.json
     gcloud config set project $GOOGLE_PROJECT_ID
     gcloud config set run/region us-central1
     gcloud auth configure-docker us-central1-docker.pkg.dev -q
     ```

4. **Build and Push Docker Image**

   - Docker image is built and pushed to Google Artifact Registry:
     ```bash
     IMAGE="us-central1-docker.pkg.dev/$GOOGLE_PROJECT_ID/discord-service-repo/discord-service:latest"
     docker build -t "$IMAGE" .
     docker push "$IMAGE"
     ```

5. **Deploy to Cloud Run**
   - Deploys the service using the pushed Docker image:
     ```bash
     gcloud run deploy discord-service \
       --image "$IMAGE" \
       --platform managed \
       --region us-central1 \
       --allow-unauthenticated \
       --port 8000
     ```

This setup ensured secure and automated deployment of our Discord service while keeping secrets protected and applying principle of least privilege access for each service.
