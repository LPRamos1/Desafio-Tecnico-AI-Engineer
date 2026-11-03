import copy
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


# Root dir of the project
ROOT_DIR = Path(__file__).resolve().parents[2]
LOG_DIR = ROOT_DIR / "logs"

LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "app.log"

# Message format
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

class ConsoleFormatter(logging.Formatter):
    """Format console messages without displaying exception tracebacks."""

    def format(self, record):
        record_copy = copy.copy(record)
        record_copy.exc_info = None
        record_copy.exc_text = None

        return super().format(record_copy)


# File handler
file_handler = RotatingFileHandler(
    LOG_FILE,
    maxBytes=5 * 1024 * 1024,
    backupCount=3,
    encoding="utf-8"
)

file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(
    ConsoleFormatter(LOG_FORMAT, datefmt=DATE_FORMAT)
)

# Log configs
logger = logging.getLogger("emporio_ai")
logger.setLevel(logging.DEBUG)
logger.propagate = False

if not logger.handlers:
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
