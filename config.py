"""
config.py - Configuration and Environment Variables

Handles all configuration settings for the Newsletter RAG application.
Loads API keys and settings from environment variables with sensible defaults.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ============================================================================
# Load environment variables from .env file
# ============================================================================
load_dotenv()

# ============================================================================
# API Keys - Required for the application to function
# ============================================================================

# Google Gemini API key for embeddings and chat completions
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY environment variable is required. "
        "Get your API key from https://makersuite.google.com/app/apikey"
    )

# ============================================================================
# Gmail OAuth Configuration
# ============================================================================

# Path to OAuth 2.0 credentials file downloaded from Google Cloud Console
GMAIL_CREDENTIALS_FILE = os.getenv(
    "GMAIL_CREDENTIALS_FILE", 
    "credentials.json"
)

# Path to store the OAuth token after authorization
GMAIL_TOKEN_FILE = os.getenv(
    "GMAIL_TOKEN_FILE", 
    "token.json"
)

# Gmail API scopes - we only need read access to emails
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly"
]

# ============================================================================
# ChromaDB Configuration
# ============================================================================

# Directory to store the vector database
CHROMA_PERSIST_DIR = os.getenv(
    "CHROMA_PERSIST_DIR", 
    str(Path.home() / ".newsletter_rag" / "chroma_db")
)

# Collection name for storing newsletter embeddings
CHROMA_COLLECTION_NAME = os.getenv(
    "CHROMA_COLLECTION_NAME", 
    "newsletters"
)

# ============================================================================
# Embedding Configuration
# ============================================================================

# Gemini embedding model to use
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL", 
    "models/embedding-001"
)

# Chunk size for splitting text (in characters)
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))

# Overlap between chunks to maintain context
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))

# ============================================================================
# Chat Configuration
# ============================================================================

# Gemini model for chat completions
CHAT_MODEL = os.getenv(
    "CHAT_MODEL", 
    "gemini-1.5-flash"
)

# Number of relevant chunks to retrieve for context
TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", "5"))

# Maximum tokens for chat response
MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "2048"))

# ============================================================================
# Newsletter Detection Configuration
# ============================================================================

# Maximum number of emails to fetch in one batch
MAX_EMAILS_PER_FETCH = int(os.getenv("MAX_EMAILS_PER_FETCH", "100"))

# How many days back to search for newsletters
DAYS_TO_FETCH = int(os.getenv("DAYS_TO_FETCH", "30"))

# ============================================================================
# Application Settings
# ============================================================================

# Enable debug logging
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Application title
APP_TITLE = "Newsletter RAG"

# ============================================================================
# Helper function to ensure directories exist
# ============================================================================

def ensure_directories():
    """Create necessary directories if they don't exist."""
    Path(CHROMA_PERSIST_DIR).mkdir(parents=True, exist_ok=True)
    
    # Create credentials directory if needed
    creds_dir = Path(GMAIL_CREDENTIALS_FILE).parent
    if creds_dir != Path("."):
        creds_dir.mkdir(parents=True, exist_ok=True)


# ============================================================================
# Validation
# ============================================================================

def validate_config():
    """Validate that all required configuration is present."""
    errors = []
    
    if not GEMINI_API_KEY:
        errors.append("GEMINI_API_KEY is not set")
    
    if not Path(GMAIL_CREDENTIALS_FILE).exists():
        errors.append(
            f"Gmail credentials file not found: {GMAIL_CREDENTIALS_FILE}. "
            "Download it from Google Cloud Console."
        )
    
    if errors:
        raise ValueError("\n".join(errors))
    
    return True


if __name__ == "__main__":
    # Print configuration for debugging
    print("Newsletter RAG Configuration")
    print("=" * 50)
    print(f"GEMINI_API_KEY: {'*' * 20}...")
    print(f"GMAIL_CREDENTIALS_FILE: {GMAIL_CREDENTIALS_FILE}")
    print(f"GMAIL_TOKEN_FILE: {GMAIL_TOKEN_FILE}")
    print(f"CHROMA_PERSIST_DIR: {CHROMA_PERSIST_DIR}")
    print(f"CHROMA_COLLECTION_NAME: {CHROMA_COLLECTION_NAME}")
    print(f"EMBEDDING_MODEL: {EMBEDDING_MODEL}")
    print(f"CHAT_MODEL: {CHAT_MODEL}")
    print(f"CHUNK_SIZE: {CHUNK_SIZE}")
    print(f"CHUNK_OVERLAP: {CHUNK_OVERLAP}")
    print(f"TOP_K_RESULTS: {TOP_K_RESULTS}")
    print(f"MAX_EMAILS_PER_FETCH: {MAX_EMAILS_PER_FETCH}")
    print(f"DAYS_TO_FETCH: {DAYS_TO_FETCH}")
    print(f"DEBUG: {DEBUG}")
