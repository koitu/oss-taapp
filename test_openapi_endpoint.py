"""Quick test to verify the /openapi.json endpoint works."""

import sys
from pathlib import Path

# Add service to path
service_path = Path(__file__).parent / "src" / "services" / "discord_client_service" / "src"
sys.path.insert(0, str(service_path))

from fastapi.testclient import TestClient
from discord_client_service.service import app

def test_openapi_endpoint():
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

    print("✓ All checks passed!")
    print(f"✓ OpenAPI version: {schema['openapi']}")
    print(f"✓ Service: {schema['info']['title']} v{schema['info']['version']}")
    print(f"✓ Endpoints: {len(schema['paths'])}")

    return True

if __name__ == "__main__":
    try:
        test_openapi_endpoint()
        print("\n✅ OpenAPI endpoint test PASSED")
    except AssertionError as e:
        print(f"\n❌ OpenAPI endpoint test FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ OpenAPI endpoint test ERROR: {e}")
        sys.exit(1)
