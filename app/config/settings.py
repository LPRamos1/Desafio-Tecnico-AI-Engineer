import os
import dotenv


dotenv.load_dotenv()

# Gemini API configs
API_KEY = os.getenv("GEMINI_API_KEY")
LLM_MODEL = "gemini-3.8-flash"

# Defensive measures
CHAR_LIMIT_PER_MSG = 2000
MAX_MSG_PER_HISTORY = 20

# Embedding model configuration
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# Vector database configuration
VECTORSTORE_DIR = "vectorstore"
COLLECTION_NAME = "store_policies"
