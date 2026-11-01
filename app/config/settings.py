import os
import dotenv


dotenv.load_dotenv()

# Gemini API configs
API_KEY = os.getenv("GEMINI_API_KEY")
LLM_MODEL = "gemini-3.8-flash"

# Defensive measures
CHAR_LIMIT_PER_MSG = 2000
MAX_MSG_PER_HISTORY = 20

