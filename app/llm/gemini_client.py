# 3rd party imports
from copy import error

from google import genai
from google.genai import types

# Project imports
from app.config.settings import (
    API_KEY,
    LLM_MODEL,
    LLM_FALLBACK_MODEL,
    LLM_TIMEOUT_MS,
    MAX_TOOL_CALLS
)
from app.config.logging_config import logger


class GeminiClient:
    """Handle communication with the language model provider."""

    def __init__(self):
        """
        Initialize the Gemini client and configure the available models.
        Raises:
            ValueError: If the Gemini API key is not configured.
        """

        if not API_KEY:
            raise ValueError("Gemini API Key not found.")

        self.client = genai.Client(api_key=API_KEY)

        self.models = [model for model in (LLM_MODEL, LLM_FALLBACK_MODEL) if model]

    def generate_response(self, contents: list[dict], system_instruction: str, tools: list | None = None):
        """
        Generate a response using Gemini and the available tools.
        The SDK automatically handles the function-calling loop,
        respecting the maximum number of tool calls.

        If the primary model fails or times out, the fallback model
        is attempted when configured.

        Args:
            contents: Conversation history sent to the model.
            system_instruction: Instructions defining the agent's behavior.
            tools: Python functions available for function calling.
        Returns:
            str: Generated response.
        Raises:
            Exception: If all configured models fail.
        """

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.2,
            tools=tools or None,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                maximum_remote_calls=MAX_TOOL_CALLS
            ),
            http_options=types.HttpOptions(timeout=LLM_TIMEOUT_MS)
        )

        last_error = None

        for model in self.models:
            try:
                response = self.client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config
                )

                if not response.text:
                    raise ValueError("The model returned an empty response.")
                
                logger.info("Model %s generated a response successfully.", model)
                return response.text

            except Exception:
                logger.exception("Model %s failed.", model)
                last_error = error

        logger.error("All configured models failed.")

        if last_error is not None:
            raise last_error

        raise RuntimeError("No configured Gemini model could generate a response.")

