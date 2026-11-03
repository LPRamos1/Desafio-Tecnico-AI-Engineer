import os

from pathlib import Path
from dotenv import load_dotenv


load_dotenv()

# Gemini API configs
API_KEY = os.getenv("GEMINI_API_KEY")
LLM_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
LLM_FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-3.5-flash-lite")  # optional, used if primary fails/times out
LLM_TIMEOUT_MS = 60_000  # per HTTP request; avoids minutes-long hangs on congested models

# Defensive measures
CHAR_LIMIT_PER_MSG = 2000
MAX_MSG_PER_HISTORY = 20
MAX_TOOL_CALLS = 5  # max tool calls per customer message (prevents loops)

# Paths
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"  # CSVs: data/products.csv, data/orders.csv, ...
VECTORSTORE_DIR = BASE_DIR / "vectorstore"
COLLECTION_NAME = "store_policies"

# Embedding model configuration
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
 
# Retrieval
RETRIEVAL_TOP_K = 5  # manual sections 3 and 3.1 conflict: both must reach the model
 

 
