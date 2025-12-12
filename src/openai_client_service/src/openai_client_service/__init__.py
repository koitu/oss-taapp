"""OpenAI Client Service package."""

import ai_api
from openai_client_service import routes as routes
from openai_client_service.ai_interface_impl import EnvAIImplementation
from openai_client_service.main import app as app


def register() -> None:
    """Register the OpenAI client interface."""
    ai_api.AIInterface = EnvAIImplementation

register()
