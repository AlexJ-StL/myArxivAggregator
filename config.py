# config.py - Configuration settings for arXiv aggregator
import os

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ArXiv API URL for fetching recent cs.AI papers (Atom feed)
ARXIV_API_URL = "https://export.arxiv.org/api/query?search_query=cat:cs.AI&sortBy=lastUpdatedDate&sortOrder=descending&max_results=8&start=0"
ARXIV_ML_URL = "https://export.arxiv.org/api/query?search_query=cat:cs.LG&sortBy=lastUpdatedDate&sortOrder=descending&max_results=8&start=0"
ARXIV_CV_URL = "https://export.arxiv.org/api/query?search_query=cat:cs.CV&sortBy=lastUpdatedDate&sortOrder=descending&max_results=8&start=0"
ARXIV_RO_URL = "https://export.arxiv.org/api/query?search_query=cat:cs.RO&sortBy=lastUpdatedDate&sortOrder=descending&max_results=8&start=0"
ARXIV_CR_URL = "https://export.arxiv.org/api/query?search_query=cat:cs.CR&sortBy=lastUpdatedDate&sortOrder=descending&max_results=8&start=0"

# Local JSON file to track which arXiv IDs have already been processed
SEEN_IDS_FILE = "seen_arxiv_ids.json"

# Ollama configuration (loaded from environment variables with fallbacks)
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
OLLAMA_VISION_MODEL = os.getenv("OLLAMA_VISION_MODEL", "llava:latest")
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/generate")
OLLAMA_CHAT_API_URL = os.getenv("OLLAMA_CHAT_API_URL", "http://localhost:11434/api/chat")

# FTP server configuration (loaded from environment variables)
FTP_HOST: str | None = os.getenv("FTP_HOST")
FTP_USER: str | None = os.getenv("FTP_USER")
FTP_PASS: str | None = os.getenv("FTP_PASS")
FTP_REMOTE_DIR = os.getenv("FTP_REMOTE_DIR", ".")

# Unsplash API configuration (loaded from environment variables)
UNSPLASH_ACCESS_KEY: str | None = os.getenv("UNSPLASH_ACCESS_KEY")
UNSPLASH_SECRET_KEY: str | None = os.getenv("UNSPLASH_SECRET_KEY")
UNSPLASH_APPLICATION_ID: str | None = os.getenv("UNSPLASH_APPLICATION_ID")
UNSPLASH_API_URL = "https://api.unsplash.com"


def validate_credentials() -> None:
    """Validate that required environment variables are set.

    This function validates credentials at runtime when needed,
    rather than at import time. Call this before using features
    that require credentials (e.g., FTP upload, Unsplash API).

    Raises:
        ValueError: If any required environment variables are missing.
    """
    missing_vars = []

    if not FTP_HOST:
        missing_vars.append("FTP_HOST")
    if not FTP_USER:
        missing_vars.append("FTP_USER")
    if not FTP_PASS:
        missing_vars.append("FTP_PASS")
    if not UNSPLASH_ACCESS_KEY:
        missing_vars.append("UNSPLASH_ACCESS_KEY")
    if not UNSPLASH_SECRET_KEY:
        missing_vars.append("UNSPLASH_SECRET_KEY")
    if not UNSPLASH_APPLICATION_ID:
        missing_vars.append("UNSPLASH_APPLICATION_ID")

    if missing_vars:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_vars)}. "
            f"Please check your .env file and ensure all required variables are set."
        )
