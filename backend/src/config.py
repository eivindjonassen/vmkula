"""Environment configuration management for vmkula-website backend"""

import os
import sys
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load .env file from project root (parent of backend/)
project_root = Path(__file__).parent.parent.parent
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path)


class Config:
    """Application configuration loaded from environment variables

    Load configuration from .env file in project root.
    See .env for required variables and Firebase project setup.
    """

    # Required API keys
    API_FOOTBALL_KEY: str
    GEMINI_API_KEY: str

    # Firebase/Firestore configuration (project: vmkula)
    FIRESTORE_PROJECT_ID: str
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str]

    # Cache configuration
    CACHE_TTL_HOURS: int = 24
    CACHE_DIR: str = "cache"

    # API rate limiting
    API_FOOTBALL_DELAY_SECONDS: float = 0.5
    MAX_RETRIES: int = 3

    # Development mode
    DEBUG: bool = False

    def __init__(self):
        """Load and validate environment variables"""
        self.load_from_env()
        self.validate()

    def load_from_env(self):
        """Load configuration from environment variables"""
        # Use test defaults if in test environment (pytest module loaded)
        is_test = "pytest" in sys.modules

        self.API_FOOTBALL_KEY = os.getenv(
            "API_FOOTBALL_KEY", "test-key" if is_test else ""
        )
        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "test-key" if is_test else "")
        self.FIRESTORE_PROJECT_ID = os.getenv(
            "FIRESTORE_PROJECT_ID", "test-project" if is_test else ""
        )
        self.GOOGLE_APPLICATION_CREDENTIALS = os.getenv(
            "GOOGLE_APPLICATION_CREDENTIALS"
        )

        # Optional settings with defaults
        self.CACHE_TTL_HOURS = int(os.getenv("CACHE_TTL_HOURS", "24"))
        self.CACHE_DIR = os.getenv("CACHE_DIR", "cache")
        self.API_FOOTBALL_DELAY_SECONDS = float(
            os.getenv("API_FOOTBALL_DELAY_SECONDS", "0.5")
        )
        self.MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
        self.DEBUG = os.getenv("DEBUG", "").lower() in ("true", "1", "yes")

    def validate(self):
        """Validate that all required environment variables are set"""
        # Skip validation in test environment (pytest module loaded)
        if "pytest" in sys.modules:
            return

        required_vars = {
            "API_FOOTBALL_KEY": self.API_FOOTBALL_KEY,
            "GEMINI_API_KEY": self.GEMINI_API_KEY,
            "FIRESTORE_PROJECT_ID": self.FIRESTORE_PROJECT_ID,
        }

        missing_vars = [name for name, value in required_vars.items() if not value]

        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}. "
                f"Please check your .env file or environment configuration."
            )


# Global configuration instance
config = Config()
