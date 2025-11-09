#!/usr/bin/env python3
"""Generate OpenAPI schema for Discord client service."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src" / "services" / "discord_client_service" / "src"))

from discord_client_service.service import app

schema = app.openapi()
output_file = Path(__file__).parent / "src" / "services" / "discord_client_service" / "openapi.json"
with output_file.open("w") as f:
    json.dump(schema, f, indent=2)

print(f"✓ Generated {output_file}")  # noqa: T201
print(f"✓ Endpoints: {len(schema.get('paths', {}))}")  # noqa: T201
