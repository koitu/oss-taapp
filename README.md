# OSPSD: AI-Based Discord Bot for Ticket Management

[![CircleCI](https://dl.circleci.com/status-badge/img/gh/koitu/oss-taapp/tree/root.svg?style=svg)](https://dl.circleci.com/status-badge/redirect/gh/koitu/oss-taapp/tree/root)
[![Coverage](https://img.shields.io/badge/coverage-85%2B%25-brightgreen)](https://circleci.com/gh/koitu/oss-taapp)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://python.org)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

## Table of Contents
- [Project Structure](#project-structure)
- [Project Setup](#project-setup)
- [Service Credentials Setup](#service-credentials-setup)
- [Running Locally](#development-workflow)
- [Infrastructure Deployment (Terraform)](#infrastructure-deployment-terraform)

## Project Structure
```
├── .circleci                               # circleci config
├── Dockerfile                              # docker file
├── .env.example                            # example for the .env file
├── src/                                    # workspace members
│   ├── hw1/                                # hw1 files
│   │   ├── gmail_client_impl/              # gmail impl
│   │   ├── mail_client_api/                # mail client API
│   │   ├── mail_client_service/            # mail service
│   │   ├── mail_client_service_adapter/    # mail client adapater
│   │   └── mail_client_service_client/     # mail generated client
│   ├── hw2/                                # hw2 files
│   │   ├── chat_client_api/                # chat client API
│   │   ├── discord_client_impl/            # discord client impl
│   │   ├── discord_client_service/         # discord service
│   │   ├── discord_client_service_adapter/ # discord client adapater
│   │   └── discord_client_service_client/  # discord generated client
│   ├── hw3/                                # hw3 files
│   │   ├── claude_client_service/          # claude ai client impl
│   │   ├── discord_chat_impl/              # discord chat client impl (and gateway)
│   │   ├── openai_client_service/          # openai ai client impl
│   │   ├── ospsd_service/                  # ospsd service (connector)
│   │   └── trello_ticket_impl/             # trell ticket client impl
│   └── oss-api/                            # standarized APIs
│       ├── ai_api/                         # api for ai client
│       ├── chat_api/                       # api for chat client
│       └── tickets_api/                    # api for ticket client
├── terraform/                              # terraform config
└── tests/                                  # tests
    ├── e2e/                                # end-to-end test
    └── integration/                        # integration tests
```

## Project Setup

### Prerequisites
- Python 3.11 or higher
- `uv` – A fast, all-in-one Python package manager.
- Docker (optional) - For containerized deployment
- Terraform (optional) - For infrastructure as code deployment
- gcloud CLI (optional) - For Google Cloud Platform deployment

### Quick Start
1.  **Install `uv`:**
    ```bash
    # macOS / Linux
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Windows (PowerShell)
    irm https://astral.sh/uv/install.ps1 | iex
    ```

2.  **Clone the Repository:**
    ```bash
    git clone https://github.com/koitu/oss-taapp.git
    cd oss-taapp
    ```

3.  **Install Dependencies:**
    ```bash
    uv sync --all-packages --extra dev
    ```

4.  **Configure Environment Variables:**
    ```bash
    cp .env.example .env
    # Edit .env with your credentials (see next section)
    ```

5.  **Add the bot to your Discord server:**
    ```bash
    uv run python generate_discord_auth_url.py
    # Follow the url then close the window
    ```
    Or add our bot (already deployed to cloud) with [this link](https://discord.com/oauth2/authorize?client_id=1433637952713654333&permissions=67584&response_type=code&redirect_uri=https%3A%2F%2Fdiscord-service-755226003273.us-central1.run.app%2Fauth%2Fcallback&integration_type=0&scope=identify+bot+guilds+messages.read)

6.  **Run the Service:**
    ```bash
    # Run the OSPSD service then chat with it
    # - /bot to talk to the bot
    # - /model to change the model
    uv run python -m ospsd_service.main
    ```


## Service Credentials Setup

The OSPSD service integrates with multiple external services.
Copy `.env.example` then configure credentials in your `.env` file:


### Discord API

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. `General Information`: take the `Application ID` and `Public Key`
4. `Installation`: set `User Install` and `Guild Install`
   - `Guild Install`: add `bot` to scopes along with `Send Messages` and `View Channels` in permissions
5. `OAuth2`: take the `Client ID` and `Client Secret`
6. `Bot`: make sure that `Message Content Intent` is checked

Add to `.env`:
```bash
DISCORD_CLIENT_ID=your-discord-client-id
DISCORD_CLIENT_SECRET=your-discord-client-secret
DISCORD_PUBLIC_KEY=your-discord-public-key
DISCORD_BOT_TOKEN=your-discord-bot-token
```

### OpenAI API

1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Create an API key

Add to `.env`:
```bash
OPENAI_API_KEY=your-openai-api-key
```

### Claude API

1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Create an API key

Add to `.env`:
```bash
CLAUDE_API_KEY=your-claude-api-key
```

### Trello API

1. Go to [Trello Power-Ups Admin](https://trello.com/power-ups/admin)
2. Create a new Power-Up to get API Key
3. Generate a token
4. Create a new board and get its id from the url

Add to `.env`:
```bash
TRELLO_API_KEY=your-trello-api-key
TRELLO_API_SECRET=your-trello-api-secret
TRELLO_BOARD_ID=your-board-id
```


## Development Workflow

### Running the Application
```bash
uv run python -m ospsd_service.main
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
uv run mkdocs build
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


## Infrastructure Deployment (Terraform)

Deploy the OSPSD service to Google Cloud Platform with Prometheus and Grafana using Terraform.

### Setup

1. **GCP Project**
   ```bash
   # Create new project or use existing
   export GCP_PROJECT_ID="your-project-id"
   gcloud projects create $GCP_PROJECT_ID --name="OSPSD Service"

   # Set as active project
   gcloud config set project $GCP_PROJECT_ID
   ```

2. **Enable Billing**
    - Link billing account in [GCP Console](https://console.cloud.google.com/billing)

3. **Authenticate gcloud**
   ```bash
   gcloud auth login
   gcloud auth application-default login
   ```
   
4. **Add secrets**
    - Visit the [secrets manager](https://console.cloud.google.com/security/secret-manager) and add the `.env` variables


### Deploy Infrastructure

**1. Navigate to Terraform Directory**
```bash
cd terraform
```

**2. Configure Variables**

Create `terraform.tfvars`:
```hcl
project         = "your-gcp-project-id"
region          = "us-central1"
service_name    = "ospsd-service"
artifact_repo   = "oss-repo"
no_auth         = "true"
trello_board_id = "your-trello-board"
```

**3. Initialize Backend (First Time Only)**
```bash
# Create bucket
gsutil mb -p your-project-id -l us-central1 gs://ospsd-terraform-state

# Initialize Terraform
terraform init
```

**4. Build and Push Docker Image**

```bash
# Authenticate Docker with Artifact Registry
gcloud auth configure-docker us-central1-docker.pkg.dev

# Build image
docker build -t us-central1-docker.pkg.dev/${GCP_PROJECT_ID}/oss-repo/ospsd-service:latest ..

# Push image
docker push us-central1-docker.pkg.dev/${GCP_PROJECT_ID}/oss-repo/ospsd-service:latest
```
Add the docker image name to the `terraform.tfvars`.

**5. Deploy with Terraform**

```bash
# Preview changes
terraform plan

# Apply changes
terraform apply
```
