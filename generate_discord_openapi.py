"""Generate OpenAPI schema for Discord Client Service.

Run this from the project root directory.
"""

import json
import sys
from pathlib import Path

# Add the discord service to the path
service_path = Path(__file__).parent / "src" / "services" / "discord_client_service" / "src"
sys.path.insert(0, str(service_path))

# Import FastAPI app without triggering lifespan
# We'll temporarily replace the lifespan
from discord_client_service import service
from discord_client_service.api import *  # Import all API routes
from fastapi import FastAPI

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
output_path = Path(__file__).parent / "src" / "services" / "discord_client_service" / "openapi.json"
with output_path.open("w") as f:
    json.dump(openapi_schema, f, indent=2)

print("✓ OpenAPI schema generated successfully!")
print(f"✓ Location: {output_path}")
print(f"✓ OpenAPI version: {openapi_schema.get('openapi')}")
print(f"✓ API title: {openapi_schema['info']['title']}")
print(f"✓ API version: {openapi_schema['info']['version']}")
print(f"✓ Total endpoints: {len(openapi_schema.get('paths', {}))}")
