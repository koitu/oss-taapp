"""Generate OpenAPI schema for the Discord Client Service."""

import json
from pathlib import Path

# Import after setting up the path
from discord_client_service.service import app


def generate_openapi_schema() -> None:
    """Generate and save the OpenAPI schema to openapi.json."""
    # Get the OpenAPI schema from FastAPI
    openapi_schema = app.openapi()

    # Save to file
    output_path = Path(__file__).parent / "openapi.json"
    with output_path.open("w") as f:
        json.dump(openapi_schema, f, indent=2)

    print(f"OpenAPI schema generated successfully at: {output_path}")
    print(f"Schema contains {len(openapi_schema.get('paths', {}))} paths")


if __name__ == "__main__":
    generate_openapi_schema()
