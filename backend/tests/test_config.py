import pytest
import os
from unittest.mock import patch
from src.config import Config


def test_config_load_from_env():
    """Test loading configuration from environment variables"""
    with patch.dict(
        os.environ,
        {
            "API_FOOTBALL_KEY": "test_key",
            "GEMINI_API_KEY": "test_gemini",
            "FIRESTORE_PROJECT_ID": "test_project",
            "CACHE_TTL_HOURS": "12",
            "DEBUG": "true",
        },
    ):
        config = Config()
        assert config.API_FOOTBALL_KEY == "test_key"
        assert config.GEMINI_API_KEY == "test_gemini"
        assert config.FIRESTORE_PROJECT_ID == "test_project"
        assert config.CACHE_TTL_HOURS == 12
        assert config.DEBUG is True


def test_config_missing_vars_raises_error():
    """Test that missing required variables raises ValueError"""
    import sys
    # Config skips validation when pytest is in sys.modules, so we temporarily remove it
    original_modules = sys.modules.copy()
    pytest_module = sys.modules.pop("pytest", None)
    try:
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Missing required environment variables"):
                Config()
    finally:
        # Restore pytest module
        if pytest_module:
            sys.modules["pytest"] = pytest_module


def test_config_defaults():
    """Test configuration default values"""
    with patch.dict(
        os.environ,
        {
            "API_FOOTBALL_KEY": "key",
            "GEMINI_API_KEY": "key",
            "FIRESTORE_PROJECT_ID": "project",
        },
        clear=True,
    ):
        config = Config()
        assert config.CACHE_TTL_HOURS == 24
        assert config.CACHE_DIR == "cache"
        assert config.API_FOOTBALL_DELAY_SECONDS == 0.5
        assert config.MAX_RETRIES == 3
        assert config.DEBUG is False
