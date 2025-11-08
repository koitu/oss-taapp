"""Generate OpenAPI schema for the Discord Client Service - Simple version."""

import json
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Prevent lifespan from running during import
import os

os.environ["SKIP_DB_INIT"] = "1"

from discord_client_service.service import app


def generate_openapi_schema() -> None:
    """Generate and save the OpenAPI schema to openapi.json."""
    # Get the OpenAPI schema from FastAPI
    openapi_schema = app.openapi()

    # Save to file in the service directory
    output_path = Path(__file__).parent / "openapi.json"
    with output_path.open("w") as f:
        json.dump(openapi_schema, f, indent=2)

    print(f"✓ OpenAPI schema generated at: {output_path}")
    print(f"✓ Schema version: {openapi_schema.get('openapi', 'unknown')}")
    print(f"✓ API title: {openapi_schema.get('info', {}).get('title', 'unknown')}")
    print(f"✓ Number of paths: {len(openapi_schema.get('paths', {}))}")


if __name__ == "__main__":
    generate_openapi_schema()
