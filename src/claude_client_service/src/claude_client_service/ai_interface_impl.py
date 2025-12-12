"""Implementation of AIInterface that reads Claude API key from environment variables."""

import json
import os
from typing import Any

from anthropic import Anthropic

from ai_api import AIInterface  # type: ignore[attr-defined]

DEFAULT_MODEL = "claude-3-5-sonnet-20241022"


class EnvAIImplementation(AIInterface):
    """Implementation of AIInterface that uses Claude API key from environment variables."""

    def __init__(self) -> None:
        """Initialize the AI implementation with API key from environment."""
        api_key = os.getenv("CLAUDE_API_KEY")
        if not api_key:
            error_msg = "CLAUDE_API_KEY environment variable is not set. Please set it in your .env file."
            raise ValueError(error_msg)
        self._client = Anthropic(api_key=api_key)

    def _prepare_schema(self, response_schema: dict[str, Any]) -> dict[str, Any]:
        """Prepare schema for Claude structured output.

        Args:
            response_schema: The user-provided JSON schema

        Returns:
            Schema with additionalProperties and required fields added

        """
        schema_with_additional_props = dict(response_schema)
        if "additionalProperties" not in schema_with_additional_props:
            schema_with_additional_props["additionalProperties"] = False

        # All properties in the response schema are assumed to be required
        if "properties" in schema_with_additional_props:
            all_properties = list(schema_with_additional_props["properties"].keys())
            schema_with_additional_props["required"] = all_properties

        return schema_with_additional_props

    def _parse_response(self, content: str, response_schema: dict[str, Any] | None) -> str | dict[str, Any]:
        """Parse the AI response based on whether schema was provided.

        Args:
            content: The response content from Claude
            response_schema: Optional schema that was used

        Returns:
            Parsed response as string or dict

        """
        if response_schema is not None:
            try:
                parsed_raw = json.loads(content)
                if not isinstance(parsed_raw, dict):
                    error_msg = "Structured response must be a dictionary"
                    raise TypeError(error_msg)
                parsed: dict[str, Any] = parsed_raw
            except json.JSONDecodeError as e:
                error_msg = f"Failed to parse structured response as JSON: {e}"
                raise RuntimeError(error_msg) from e
            else:
                return parsed
        else:
            return str(content)

    def generate_response(
        self,
        user_input: str,
        system_prompt: str,
        response_schema: dict[str, Any] | None = None,
    ) -> str | dict[str, Any]:
        """Generate a response from Claude AI.

        :param user_input: The text provided by the chat user.
        :param system_prompt: The instruction set (e.g., "You are a helpful assistant...").
        :param response_schema: An optional JSON schema (dict).
                                If provided, the AI must return a structured Dict matching this schema.
                                If None, the AI returns a conversational String.

        :return: A string (conversation) or a Dict (structured action data).
        """
        # Prepare the message parameters
        message_params: dict[str, Any] = {
            "model": DEFAULT_MODEL,
            "max_tokens": 1024,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_input}],
        }

        # If response_schema is provided, add instructions for JSON output
        if response_schema is not None:
            prepared_schema = self._prepare_schema(response_schema)
            schema_json = json.dumps(prepared_schema)
            schema_instruction = (
                f"\n\nIMPORTANT: You must respond with valid JSON matching this exact schema: {schema_json}"
            )
            message_params["system"] = system_prompt + schema_instruction

        def _raise_empty_response() -> None:
            error_msg = "AI service returned empty response"
            raise RuntimeError(error_msg)

        try:
            response = self._client.messages.create(**message_params)

            # Extract text content from Claude's response
            if not response.content:
                _raise_empty_response()

            content = response.content[0].text if response.content else None

            if content is None:
                _raise_empty_response()

            return self._parse_response(content, response_schema)

        except RuntimeError:
            # Re-raise RuntimeError as-is
            raise
        except Exception as e:
            error_msg = f"AI service failed to process request: {e}"
            raise RuntimeError(error_msg) from e
