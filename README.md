# Python Application Template: A Component-Based Mail Client

[![CircleCI](https://dl.circleci.com/status-badge/img/gh/koitu/oss-taapp/tree/root.svg?style=svg)](https://dl.circleci.com/status-badge/redirect/gh/koitu/oss-taapp/tree/root)
[![Coverage](https://img.shields.io/badge/coverage-85%2B%25-brightgreen)](https://circleci.com/gh/ivanearisty/oss-taapp)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://python.org)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

This repository serves as a professional-grade template for a modern Python project. It demonstrates a robust, component-based architecture by building the core components for an AI-powered email assistant that interacts with the Gmail API.

The project emphasizes a strict separation of concerns, dependency injection, and a comprehensive, automated toolchain to enforce code quality and best practices.

## Architectural Philosophy

This project is built on the principle of "programming integrated over time." The architecture is designed to combat complexity and ensure the system is maintainable and evolvable.

-   **Component-Based Design:** The system is broken down into four distinct, self-contained components. Each component has a single responsibility and can be "forklifted" out of this project to be used in another with minimal effort.
-   **Interface-Implementation Separation:** Every piece of functionality is defined by an abstract **contract** implemented as an ABC (the "what") and fulfilled by a concrete **implementation** (the "how"). This decouples our business logic from specific technologies (like Gmail).
-   **Dependency Injection:** Implementations are "injected" into the abstract contracts at runtime. This means consumers of the API only ever depend on the stable interface, not the volatile implementation details.

## Core Components

The project is a `uv` workspace containing several related packages under `src/`. Each package has a focused responsibility and can be used independently:

- **`mail_client_api`**: Defines the abstract `Client` base class (ABC) and message abstractions. This package is the stable contract that implementations must satisfy.
- **`gmail_client_impl`**: A concrete implementation that implements the `mail_client_api` contract using the Gmail API (`GmailClient` and message implementations).
- **`mail_client_service_adapter`**: An adapter layer that translates between the mail client implementation and the service API (handler code used by the service).
- **`mail_client_service`** (located under `src/services/mail_client_service`): A small HTTP service that exposes the mail client functionality, orchestration and end-to-end glue.
- **`clients`** (under `src/clients`, e.g. `mail_client_service_client`): Generated OpenAPI client(s) used to call the service from other components or tests.

## Project Structure

```
ta-assignment/
├── src/                          # Source packages (workspace members)
│   ├── clients/                  # Generated API clients (e.g. mail_client_service_client)
│   ├── gmail_client_impl/        # Gmail-specific implementation of the mail client
│   ├── mail_client_api/          # Abstract mail client contract (Client, Message)
│   └── mail_client_service_adapter/ # Adapter that exposes implementations as the service API
│   └── services/
│       └── mail_client_service/  # Small HTTP service exposing the mail client API
├── tests/                        # Integration and E2E tests
│   ├── integration/              # Component integration tests
│   └── e2e/                      # End-to-end application tests
├── docs/                         # Documentation source files
├── .circleci/                    # CircleCI configuration
├── Dockerfile                     # Dockerfile to containerize FastAPI service
├── CONTRIBUTING.md                # Contributor guide
├── DESIGN.md                      # Design document for new components
├── main.py                        # Main application entry point / demo
├── pyproject.toml                 # Project configuration (dependencies, tools)
├── uv.lock                        # Locked dependency versions
└── credentials.json               # Google OAuth credentials (local only)
```

## Project Setup

### 1. Prerequisites

-   Python 3.11 or higher
-   `uv` – A fast, all-in-one Python package manager.

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

3.  **Set Up Google Credentials:**
    -   Follow the [Google Cloud instructions](https://developers.google.com/gmail/api/quickstart/python#authorize_credentials_for_a_desktop_application) to enable the Gmail API and download your OAuth 2.0 credentials.
    -   Rename the downloaded file to `credentials.json` and place it in the root of this project.
    -   **Alternative**: For CI/CD environments, you can use environment variables instead:
        ```bash
        export GMAIL_CLIENT_ID="your_client_id"
        export GMAIL_CLIENT_SECRET="your_client_secret"
        export GMAIL_REFRESH_TOKEN="your_refresh_token"
        ```
    -   **Important:** Credential files contain secrets and are ignored by `.gitignore`.

4.  **Create and Sync the Virtual Environment:**
    This single command creates a `.venv` folder and installs all packages (including workspace members and development tools) defined in `uv.lock`.
    ```bash
    uv sync --all-packages --extra dev
    ```

5.  **Activate the Virtual Environment:**
    ```bash
    # macOS / Linux
    source .venv/bin/activate
    # Windows (PowerShell)
    .venv\Scripts\Activate.ps1
    ```

6.  **Perform Initial Authentication:**
    Run the main application once to perform the interactive OAuth flow. This will open a browser window for you to grant permission.
    ```bash
    uv run python main.py
    ```
    After you approve, a `token.json` file will be created. This file is also ignored by `.gitignore` and will be used for authentication in subsequent runs.

## Development Workflow

All commands should be run from the project root with the virtual environment activated.

### Running the Application

To run the main demonstration script:
```bash
uv run python main.py
```

### Running the Toolchain

-   **Linting & Formatting (Ruff):**
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

-   **Static Type Checking (MyPy):**
    ```bash
    uv run mypy src tests
    ```

-   **Testing (Pytest):**

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
# Start the live-reloading documentation server
uv run mkdocs serve
```
Open your browser to `http://127.0.0.1:8000` to view the site.

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

The testing infrastructure handles different authentication scenarios:
- **Local Development**: Uses `credentials.json` and `token.json` files
- **CI/CD Environment**: Uses environment variables (`GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN`)
- **Missing Credentials**: Tests fail fast with clear error messages (no hanging)

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
6. **Run backend service**: `uv run python3 run_service.py`
7. **Demo of the frontend client**: `uv run python3 test_adapter.py`

### Best Practices
- Run unit tests (`uv run pytest src/`) during development for fast feedback
- Use integration tests (`uv run pytest -m integration`) to verify component interactions
- Run full test suite (`uv run pytest`) before pushing to ensure CI compatibility
- The CircleCI pipeline provides automated validation on every push

## Running with Docker

The application can be containerized using Docker for easy deployment and distribution.

### Building the Docker Image

```bash
docker build -t gmail-service .
```

This builds a Docker image named `gmail-service` using the provided Dockerfile. The build process:
- Uses Python 3.11 slim base image
- Installs `uv` for dependency management
- Copies project files and installs dependencies
- Exposes port 8000 for the FastAPI service

### Running the Container

**Basic run (FastAPI service):**
```bash
docker run -p 8000:8000 gmail-service
```

The service will be available at `http://localhost:8000`. You can access:
- API documentation: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`

**Note:** If you visit `http://localhost:8000/` (root path), you'll see a 404 error. This is normal - the service has specific endpoints like `/messages`, `/health`, etc. Use `/docs` to see all available endpoints.

**Running with Gmail credentials (environment variables):**
```bash
docker run -p 8000:8000 \
  -e GMAIL_CLIENT_ID="your_client_id" \
  -e GMAIL_CLIENT_SECRET="your_client_secret" \
  -e GMAIL_REFRESH_TOKEN="your_refresh_token" \
  gmail-service
```

**Running the main.py demo:**
```bash
docker run gmail-service uv run python main.py
```

**Running with credential files:**
```bash
docker run -p 8000:8000 \
  -v $(pwd)/credentials.json:/app/credentials.json \
  -v $(pwd)/token.json:/app/token.json \
  gmail-service
```

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
