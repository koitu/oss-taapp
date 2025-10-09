# Contributing Guide

Welcome! This guide will help you understand how this project is organized, how the components work together, and how to develop and test code.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Repository Structure](#repository-structure)
- [Testing Strategy](#testing-strategy)
- [Development Tools](#development-tools)

## Architecture Overview

### Components

The project uses a `uv` workspace with four main components:

1. **`mail_client_api`** - Defines abstract interfaces (`Client` and `Message` ABCs). This has no external dependencies.

2. **`gmail_client_impl`** - The concrete Gmail implementation. This provides `GmailClient` and `GmailMessage` classes with OAuth2 authentication.

3. **`mail_client_service_adapter`** - Adapter layer that connects the mail client to the HTTP service.

4. **`mail_client_service`** - A FastAPI HTTP service that exposes mail client functionality through REST endpoints.

**How Components Interact:**

```
main.py → imports gmail_client_impl (triggers DI)
       → calls mail_client_api.get_client()
       → returns GmailClient instance

mail_client_api (interfaces) ← gmail_client_impl (implementation)
       ↑
       └── mail_client_service_adapter ← mail_client_service (HTTP API)
```

When you import `gmail_client_impl`, it automatically registers itself. Then when you call `mail_client_api.get_client()`, you get back a working `GmailClient` instead of an error.

### Interface Design

The project uses **Abstract Base Classes (ABCs)** to define contracts between components.

**Design Principles:**

- **Deep Modules** - The interface has only 4 methods, but they're powerful enough to handle complex email workflows
- **Information Hiding** - Users of `Client` don't need to know about OAuth2 flows, Gmail API calls, or error handling. That's all hidden inside `GmailClient`.
- **Stable Interfaces** - The `mail_client_api` package has zero dependencies and rarely needs to change. Implementations can evolve without breaking things.

**Example Interface:**

```python
class Client(ABC):
    @abstractmethod
    def get_message(self, message_id: str) -> Message:
        raise NotImplementedError

    @abstractmethod
    def delete_message(self, message_id: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def mark_as_read(self, message_id: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get_messages(self, max_results: int = 10) -> Iterator[Message]:
        raise NotImplementedError
```

**Why Use ABCs Instead of Protocols?**

- **Runtime Checks** - ABCs will throw an error if you forget to implement a method. Protocols only work with static type checkers.
- **Clear Intent** - You have to explicitly inherit: `class GmailClient(Client)`. This makes relationships obvious.
- **Easy Discovery** - You can search for all implementations by looking for classes that inherit from the ABC.

**ABC vs Protocol Comparison:**

| Aspect | ABC | Protocol |
|--------|-----|----------|
| Type Checking | Nominal (explicit inheritance) | Structural (duck typing) |
| Runtime Check | Yes | No |
| Inheritance | Required | Optional |
| Use Case | Framework contracts (this project) | Flexible type hints |

### Implementation Details

**Python Features Used:**

1. **`abc.ABC`** - Base class that marks something as abstract
2. **`@abstractmethod`** - Decorator that forces subclasses to implement a method
3. **`@property + @abstractmethod`** - Makes abstract properties (like `Message.id`)
4. **Factory Functions** - Functions like `get_client()` that create instances

**How It Works:**

- **Contract** ([client.py:11](src/mail_client_api/src/mail_client_api/client.py#L11)): Says "all clients must have a `get_messages()` method that returns `Iterator[Message]`"
- **Implementation** ([gmail_impl.py:298](src/gmail_client_impl/src/gmail_client_impl/gmail_impl.py#L298)): The actual code that calls Gmail API and returns `GmailMessage` objects
- **Usage**: You just call `mail_client_api.get_client().get_messages()` - you don't need to know anything about Gmail

This means we could swap in `OutlookClient` or `MockClient` without changing any code that uses the interface.

### Dependency Injection

This project uses a **factory function override** pattern for dependency injection.

**How It Works:**

1. The API defines a `get_client()` function that raises `NotImplementedError`:

```python
# mail_client_api/client.py
def get_client(*, interactive: bool = False) -> Client:
    raise NotImplementedError  # Placeholder
```

2. The implementation provides a real factory and registers it:

```python
# gmail_impl.py
def get_client_impl(*, interactive: bool = False) -> mail_client_api.Client:
    return GmailClient(interactive=interactive)

def register() -> None:
    mail_client_api.get_client = get_client_impl  # Replace the placeholder!
```

3. Registration happens automatically when you import:

```python
# gmail_client_impl/__init__.py
register()  # Runs when module is imported
```

4. Your application imports the implementation, then uses the API:

```python
import gmail_client_impl  # Triggers registration
import mail_client_api

client = mail_client_api.get_client()  # Now returns GmailClient
```

**Where the injection happens:** [gmail_impl.py:346](src/gmail_client_impl/src/gmail_client_impl/gmail_impl.py#L346)

**Why this is useful:**
- You can swap implementations just by changing what you import
- Tests can inject mocks by overriding the factory
- No circular dependencies
- Acts like a plugin system

## Repository Structure

### Project Organization

```
oss-taapp/
├── src/                          # All source packages
│   ├── mail_client_api/          # Abstract interfaces
│   ├── gmail_client_impl/        # Gmail implementation
│   ├── mail_client_service_adapter/
│   ├── services/mail_client_service/
│   └── clients/                  # Generated API clients
├── tests/                        # Integration & E2E tests
│   ├── integration/
│   └── e2e/
├── docs/                         # MkDocs documentation
├── .circleci/config.yml          # CI pipeline
├── main.py                       # Main application entry point
├── pyproject.toml                # Root workspace config
└── uv.lock                       # Locked dependency versions
```

**Important directories:**

- **`src/`** - Each subdirectory is a separate package with its own `pyproject.toml`
- **`src/*/src/`** - The actual source code (this is called "src layout")
- **`src/*/tests/`** - Unit tests for each package
- **`tests/`** - Integration and E2E tests that span multiple components

### Configuration Files

**Root `pyproject.toml`:**
- Lists all workspace members
- Defines shared dependencies (like fastapi)
- Configures tools (ruff, mypy, pytest, coverage) for the whole project

**Component `pyproject.toml`:**
- Package name and version
- Package-specific dependencies
- References to workspace dependencies via `[tool.uv.sources]`
- Can extend or override root config

**Main differences:**

| Aspect | Root | Component |
|--------|------|-----------|
| Purpose | Manages the whole workspace | Defines one package |
| Dependencies | Shared across all packages | Just for this package |
| Workspace | Lists members | Declares dependencies |

### Package Structure

**`__init__.py` Files:**

Every package under `src/` has an `__init__.py` file that:
- Marks the directory as a Python package
- Defines what's public via `__all__`
- Runs initialization code (like calling `register()`)

**Keep `__init__.py` files simple:**

✅ **Do:**
- Import and re-export your public API
- Define `__all__`
- Call simple setup functions

❌ **Don't:**
- Put business logic here
- Do complex initialization
- Create heavy side effects

**Example:**

```python
# mail_client_api/__init__.py
from mail_client_api.client import Client, get_client
from mail_client_api.message import Message, get_message

__all__ = ["Client", "Message", "get_client", "get_message"]
```

### Import Guidelines

**Follow these rules:**

1. **Use absolute imports:**

```python
# ✅ Good
from mail_client_api import Client

# ❌ Avoid
from .client import Client
```

2. **Only use relative imports when:**
   - You're inside a package's internal modules
   - You need to avoid circular imports

3. **Import from `__init__.py`, not internal modules:**

```python
# ✅ Good
from mail_client_api import Client

# ❌ Bad
from mail_client_api.client import Client
```

4. **Organize imports in this order:**
   - Standard library
   - Third-party packages
   - Your local packages

## Testing Strategy

### Testing Philosophy

**Things to keep in mind when writing tests:**

1. **Test what code does, not how it does it** - This makes tests survive refactoring
2. **Arrange-Act-Assert (AAA)** - Set up, run the code, check results
3. **Isolate unit tests** - Use mocks so tests don't depend on external services
4. **Keep tests fast** - Unit tests should run in milliseconds
5. **Use descriptive names** - Like `test_get_message_with_invalid_id_raises_error`
6. **Keep tests simple** - No loops or complex logic in tests

### Test Organization

**Three types of tests:**

1. **Unit Tests** (`src/*/tests/`) - Fast, isolated, everything mocked
2. **Integration Tests** (`tests/integration/`) - Test how components work together, may call real APIs
3. **E2E Tests** (`tests/e2e/`) - Test complete workflows, slowest

**Don't put `__init__.py` in test directories:**

Test directories should NOT be packages. This prevents:
- Tests importing from each other
- Weird namespace issues
- Circular dependencies

### Test Abstraction Levels

**1. Unit Tests (80% of your tests)** - Test individual functions/classes with mocks:

```python
def test_client_get_messages() -> None:
    mock_client = Mock(spec=Client)
    mock_client.get_messages.return_value = iter([mock_message])
    # ...
```

**2. Integration Tests (15%)** - Test components working together:

```python
def test_get_client_and_authenticate() -> None:
    client = mail_client_api.get_client(interactive=False)
    assert isinstance(client, gmail_client_impl.GmailClient)
```

**3. E2E Tests (5%)** - Test the whole system end-to-end

### Code Coverage

**Tool:** `pytest-cov` (a pytest plugin for coverage.py)

**Required coverage:** 85% minimum

**How to run tests with coverage:**

```bash
# All tests with coverage
uv run pytest --cov=src --cov-report=term-missing

# Just unit tests
uv run pytest src/ --cov=src --cov-fail-under=85

# Skip tests that need local credentials (good for CI)
uv run pytest src/ tests/ -m "not local_credentials" --cov=src

# Generate HTML report (then open htmlcov/index.html)
uv run pytest --cov=src --cov-report=html

# Generate XML (for CI tools)
uv run pytest --cov=src --cov-report=xml
```

**What's excluded from coverage:**
- Test files themselves
- Generated code
- Lines with `raise NotImplementedError`
- Type checking blocks (`if TYPE_CHECKING:`)

## Development Tools

### Workspace Management

**uv** is a Python package manager that replaces pip, virtualenv, and pip-tools.

**Common commands:**

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Set up your environment
uv sync --all-packages --extra dev

# Run stuff
uv run python main.py
uv run pytest
uv run ruff check .

# Add a dependency
uv add <package-name>                                  # To root
cd src/gmail_client_impl && uv add <package-name>      # To a component

# Update dependencies
uv sync    # From pyproject.toml
uv lock    # Regenerate uv.lock
```

**Typical workflow:**

```bash
uv sync --all-packages --extra dev
# Make your changes...
uv run pytest src/ tests/ -m "not local_credentials" -v
uv run ruff check . --fix
uv run ruff format .
uv run mypy src/
```

#### pyproject.toml Roles

**Root `pyproject.toml`**

- Serves as the global configuration for the entire repository.
- Specifies the **build system** used by all components.
- Defines **global tool configurations** (e.g., `black`, `ruff`, `mypy`) to ensure consistency across all packages.
- Can manage **shared dependencies** if the repository uses a workspace or monorepo setup.

**Component-level `pyproject.toml`**

- Defines **package-specific metadata** (name, version, description, authors) for each component.
- Manages **component-specific dependencies** required only by that subpackage.
- Can override or extend **tool configurations** for the specific component.
- Needed if the component is independently buildable or installable.

**Interaction**

- Root `pyproject.toml` provides global defaults.
- Component-level `pyproject.toml` overrides or extends root settings as needed.
- Dependency installation, tool execution, and builds consult both root and component configurations depending on context.


### Static Analysis and Code Formatting

**Tools we use:**

- **Ruff** - Super fast linter and formatter (replaces flake8, isort, black)
- **MyPy** - Type checker

**Commands:**

```bash
# Ruff
uv run ruff check .              # Find issues
uv run ruff check . --fix        # Auto-fix what it can
uv run ruff format --check .     # Check if formatted correctly
uv run ruff format .             # Format the code

# MyPy
uv run mypy src/                 # Check types
```

**Why use these:**
- Everyone's code looks the same
- Catches bugs before you run the code
- Makes code review easier
- Makes refactoring safer

Both tools get installed when you run `uv sync --extra dev` and are configured in `pyproject.toml`.

### Documentation Generation

**Tool:** MkDocs with Material theme and mkdocstrings

**Commands:**

```bash
# Run docs locally with live reload
uv run mkdocs serve
# Then visit http://127.0.0.1:8000

# Build static site
uv run mkdocs build
# Output goes in site/
```

**To add a new doc page:**
1. Create `docs/your-page.md`
2. Add it to `mkdocs.yml`:

```yaml
nav:
  - Overview: index.md
  - Your Page: your-page.md
```

**Docstring format:**

```python
def example(param1: str, param2: int) -> bool:
    """One-line summary.

    Args:
        param1: What this is.
        param2: What this is.

    Returns:
        What gets returned.

    Raises:
        ValueError: When this happens.
    """
```

### CI

**Platform:** CircleCI (config in [.circleci/config.yml](.circleci/config.yml))

**The pipeline has 6 jobs:**

1. **build** - Install uv, install dependencies, save workspace
2. **lint** - Check code style with ruff
3. **unit_test** - Run unit tests + check coverage (85%) + type check with mypy
4. **circleci_test** - Run all tests except ones that need local credentials
5. **integration_test** - Run full integration tests with real Gmail API (only on main/develop)
6. **report_summary** - Show test results

**Two workflows:**

- **build_and_test** (feature branches) - Runs jobs 1-4 and 6
- **full_integration** (main/develop) - Runs all jobs including real API tests

**When jobs run:**

| Job | Trigger | Branches |
|-----|---------|----------|
| build | Every push | All |
| lint | After build | All |
| unit_test | After build | All |
| circleci_test | After unit_test | All |
| integration_test | After circleci_test | main, develop only |
| report_summary | After tests | All |

**Environment variables needed (stored in CircleCI):**
- `GMAIL_CLIENT_ID`
- `GMAIL_CLIENT_SECRET`
- `GMAIL_REFRESH_TOKEN`

### Docker Deployment

The project includes Docker support for containerized deployment.

**Dockerfile Overview:**

The [Dockerfile](Dockerfile) uses a multi-stage approach:
- Base image: Python 3.11 slim (lightweight)
- Installs `uv` via pip
- Copies all project files (respecting `.dockerignore`)
- Installs dependencies with `uv sync --all-packages --no-dev`
- Exposes port 8000
- Default command runs the FastAPI service

**Build the image:**
```bash
docker build -t gmail-service .
```

**Run the service:**
```bash
# Basic run
docker run -p 8000:8000 gmail-service

# With environment variables (for Gmail API)
docker run -p 8000:8000 \
  -e GMAIL_CLIENT_ID="your_id" \
  -e GMAIL_CLIENT_SECRET="your_secret" \
  -e GMAIL_REFRESH_TOKEN="your_token" \
  gmail-service

# Run main.py demo instead
docker run gmail-service uv run python main.py
```

**Access the API:**
- Docs: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`
- Root path (`/`) returns 404 - this is normal

**What's excluded (.dockerignore):**
- Virtual environments and caches
- Git and CI files
- Documentation and tests
- Secrets (credentials.json, token.json)
- IDE and OS files

---

## Quick Reference

**Setup:**
```bash
uv sync --all-packages --extra dev
```

**Development loop:**
```bash
uv run pytest src/                    # Quick unit tests
uv run ruff check . --fix             # Fix linting
uv run ruff format .                  # Format code
uv run mypy src/                      # Type check
uv run pytest src/ tests/ -m "not local_credentials"  # All tests
```

**Docker:**
```bash
docker build -t gmail-service .       # Build image
docker run -p 8000:8000 gmail-service # Run service
```

**Docs:**
```bash
uv run mkdocs serve
```

**Coverage:**
```bash
uv run pytest --cov=src --cov-report=html
```

---

## Getting Help

- [README.md](README.md) - Setup instructions
- Look at existing code and tests for examples
- Report issues at https://github.com/koitu/oss-taapp/issues

## Summary

- **Architecture**: Uses ABCs for interfaces, dependency injection with factory functions
- **Structure**: uv workspace with src layout
- **Testing**: Unit/integration/E2E tests, 85% coverage required
- **Tools**: uv, ruff, mypy, mkdocs, CircleCI
