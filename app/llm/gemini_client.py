# 3rd party imports
from multiprocessing import Value #####
from google import genai
from google.genai import types

# Project imports
from app.config.settings import API_KEY, LLM_MODEL
from app.config.logging_config import logger


class GeminiClient:
    """Handle communication with the language model provider."""
    def __init__(self):
        if not API_KEY:
            raise ValueError("Gemini API Key not found.")

        self.client = genai.Client(api_key=API_KEY)
        self.model = LLM_MODEL


    def generate_response(self, contents: list[dict], system_instruction: str):
        """Generate a response from the language model.
        Args:
            contents (list[dict]): Conversation messages sento to the model.
            system_instruction (str): Instructions defining model behavior.
        Returns:
            str: Generated response.
        """
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=types.GenerateContentConfig(system_instruction=system_instruction)
                )

            if not response.text:
                raise ValueError("The model returned an empty response.")
            return response.text
        
        except Exception:
            logger.exception("Error generating model response.")
            raise
