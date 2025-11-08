"""Generate OpenAPI schema for the Discord Client Service."""

import json
import logging
from pathlib import Path

# Import after setting up the path
from discord_client_service.service import app

# module logger
logger = logging.getLogger(__name__)


def generate_openapi_schema() -> None:
    """Generate and save the OpenAPI schema to openapi.json."""
    # Get the OpenAPI schema from FastAPI
    openapi_schema = app.openapi()

    # Save to file
    output_path = Path(__file__).parent / "openapi.json"
    with output_path.open("w") as f:
        json.dump(openapi_schema, f, indent=2)

    logger.info("OpenAPI schema generated successfully at: %s", output_path)
    logger.info("Schema contains %d paths", len(openapi_schema.get("paths", {})))


if __name__ == "__main__":
    # Configure simple logging for script usage
    logging.basicConfig(level=logging.INFO)
    generate_openapi_schema()
