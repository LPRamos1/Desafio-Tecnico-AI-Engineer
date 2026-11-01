from uuid import uuid4
from datetime import datetime

from app.config.settings import MAX_MSG_PER_HISTORY


class Session:
    """Represent an individual custumer conversation."""


    def __init__(self, customer_name: str | None = None):
        """
        Initialize a new conversation session.
        Args:
            customer_name (str | None): Optional customer display name
        """
        self.session_id = str(uuid4())
        self.customer_name = customer_name
        self.history = []
        self.created_at = datetime.now().astimezone()
        self.last_activity_date = self.created_at.date()


    def _check_daily_reset(self) -> None:
        """Reset conversation history when a new day starts."""

        current_date = datetime.now().astimezone().date()
        if current_date != self.last_activity_date:
            self.clear_history()
            self.last_activity_date = current_date



    def add_message(self, role: str, content: str):
        """
        Add a message to the conversation history.
        Args: 
            role (str): Message role, such as user or assistent.
            content (str): Message content.
        """
        self._check_daily_reset()
        self.history.append({
            "role": role,
            "content": content
        })
        self.history = self.history[-MAX_MSG_PER_HISTORY:]


    def get_history(self):
        """
        Retrieve the conversation history.
        Returns:
            list[dict]: Message stored in the session.
        """
        self._check_daily_reset()
        return self.history.copy()


    def clear_history(self) -> None:
        """Clear all messages from the conversation history."""
        self.history.clear()

class SessionManager:
    """Manage customer conversation sessions."""


    def __init__(self):
        """Initialize the session manager."""
        self.sessions = {}


    def create_session(self, customer_name: str | None = None):
        """Create and register a new conversation session.
        Args:
            customer_name (str | None): Optional customer display name.
        Returns:
            Session: Newly created conversation session.
        """

        session = Session(customer_name)
        self.sessions[session.session_id] = session

        return session


    def get_session(self, session_id: str):
        """
        Retrieve a session by its identifier.
        Args:
            session_id (str): Unique session identifier.
        Returns:
            Session | None: Found session or None.
        """
        return self.sessions.get(session_id)


    def delete_session(self, session_id: str):
        """
        Delete a session from the manager.
        Args:
            session_id (str): Unique session identifier.
        Returns:
            bool: True if the session was deleted, otherwise False.
        """
        return self.sessions.pop(session_id, None) is not None
    