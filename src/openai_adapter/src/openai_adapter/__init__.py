"""AI Service Adapter.

This package provides an adapter that exposes a small, stable API for
consumers and forwards calls to the OpenAI Client Service using explicit HTTP
calls.
"""

from openai_adapter._adapter import AdapterAPIError as AdapterAPIError
from openai_adapter._adapter import AIAdapter as AIAdapter
from openai_adapter._adapter import OpenAIServiceAdapter as OpenAIServiceAdapter
