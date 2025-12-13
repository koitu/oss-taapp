"""Use the Discord client service to generate a URL for adding your bot to your server."""

import contextlib
import os

from dotenv import load_dotenv

from discord_client_impl import DiscordClient

with contextlib.suppress(FileNotFoundError):
    load_dotenv()

auth_client = DiscordClient(
    client_id=os.environ.get("DISCORD_CLIENT_ID"),
    client_secret=os.environ.get("DISCORD_CLIENT_SECRET"),
    access_token=os.environ.get("DISCORD_ACCESS_TOKEN"),
)
auth_client.redirect_uri = None

url, _ = auth_client._get_authorization_url()  # noqa: SLF001
print(url)  # noqa: T201
