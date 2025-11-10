"""Generate OpenAPI schema for Discord Client Service.

Run this from the project root directory.
"""

import importlib
import json
import logging
import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_openapi(output_path: Path | str | None = None) -> dict[str, Any]:
    """Generate OpenAPI schema for the discord client service.

    This function dynamically adds the service source directory to sys.path,
    imports the service module, creates a temporary FastAPI app (without
    lifespan), copies routes and writes the generated OpenAPI JSON to
    `output_path` (defaults to the service's openapi.json file).
    """
    # Add the discord service to the path so imports resolve
    service_path = (
        Path(__file__).parent / "src" / "services" / "discord_client_service" / "src"
    )
    sys.path.insert(0, str(service_path))

    # Import the service module dynamically (avoid module-level import after code)
    service = importlib.import_module("discord_client_service.service")

    # Create a new app without lifespan for schema generation
    temp_app = FastAPI(
        title="Discord Client Service",
        description="RESTful API for Discord chat operations with OAuth2 authentication",
        version="0.1.0",
    )

    # Copy routes from the original app
    temp_app.router.routes = service.app.router.routes

    # Generate schema
    openapi_schema = temp_app.openapi()

    # Save to file
    if output_path is None:
        output_path = (
            Path(__file__).parent / "src" / "services" / "discord_client_service" / "openapi.json"
        )
    else:
        output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2)

    logger.info("✓ OpenAPI schema generated successfully!")
    logger.info("✓ Location: %s", output_path)
    logger.info("✓ OpenAPI version: %s", openapi_schema.get("openapi"))
    logger.info("✓ API title: %s", openapi_schema["info"]["title"])
    logger.info("✓ API version: %s", openapi_schema["info"]["version"])
    logger.info("✓ Total endpoints: %d", len(openapi_schema.get("paths", {})))

    return openapi_schema


if __name__ == "__main__":
    generate_openapi()
