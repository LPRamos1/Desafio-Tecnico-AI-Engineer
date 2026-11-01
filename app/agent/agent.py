from app.agent.prompt import SYSTEM_PROMPT
from app.agent.session import Session
from app.llm.gemini_client import  GeminiClient


class Agent:
    """Orchestrate customer interactions with the language model."""

    def __init__(self, gemini_client: GeminiClient, session: Session):
        """
        Initialize the agent with dependencies.
        Args:
            gemini_client (GeminiClient): Language model client.
            session (Session): Customer conversation session.
        """
        self.gemini_client = gemini_client
        self.session = session


    def handle_message(self, message: str):
        """
        Process a costumer message and return the model response.
        Args:
            message (str): Customer message.
        Returns:
            str: Assistante response.
        """
        self.session.add_message("user", message)
        history = self.session.get_history()

        contents = [{
            "role": "user" if item ["role"] == "user" else "model",
            "parts": [{"text": item["content"]}]
        } for item in history
        ]

        response = self.gemini_client.generate_response(
            contents=contents,
            system_instruction=SYSTEM_PROMPT
        )

        self.session.add_message("assistant", response)

        return response
    