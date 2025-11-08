"""Quick test to verify the /openapi.json endpoint works."""

import logging
import sys
from pathlib import Path

# Add service to path
service_path = Path(__file__).parent / "src" / "services" / "discord_client_service" / "src"
sys.path.insert(0, str(service_path))

from discord_client_service.service import app
from fastapi.testclient import TestClient


def test_openapi_endpoint() -> None:
    """Test that /openapi.json endpoint returns valid schema."""
    client = TestClient(app)

    # Make request to openapi endpoint
    response = client.get("/openapi.json")

    # Check response
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    # Verify it's JSON
    schema = response.json()

    # Verify basic OpenAPI structure
    assert "openapi" in schema, "Missing 'openapi' version field"
    assert "info" in schema, "Missing 'info' field"
    assert "paths" in schema, "Missing 'paths' field"

    # Verify version
    assert schema["openapi"] == "3.1.0", f"Expected OpenAPI 3.1.0, got {schema['openapi']}"

    # Verify info
    assert schema["info"]["title"] == "Discord Client Service"
    assert schema["info"]["version"] == "0.1.0"

    # Verify paths
    assert len(schema["paths"]) == 9, f"Expected 9 paths, got {len(schema['paths'])}"

    # Test assertions are sufficient; avoid printing in test files

if __name__ == "__main__":
    # Configure simple logging for when running this module as a script
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logger = logging.getLogger(__name__)
    try:
        test_openapi_endpoint()
        logger.info("OpenAPI endpoint test PASSED")
    except AssertionError:
        logger.exception("OpenAPI endpoint test FAILED")
        sys.exit(1)
    except Exception:
        logger.exception("OpenAPI endpoint test ERROR")
        sys.exit(1)
