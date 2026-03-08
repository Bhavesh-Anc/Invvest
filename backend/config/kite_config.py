"""
Kite API Configuration
Manages API credentials and settings for Zerodha Kite Connect
"""

import os
from pathlib import Path
from typing import Optional
import json
import logging

logger = logging.getLogger(__name__)

# Configuration file path
CONFIG_DIR = Path(__file__).parent.parent.parent / ".kite"
CONFIG_FILE = CONFIG_DIR / "config.json"
TOKEN_FILE = CONFIG_DIR / "access_token.txt"


class KiteConfig:
    """Manages Kite API configuration and credentials"""

    def __init__(self):
        self.api_key: Optional[str] = None
        self.api_secret: Optional[str] = None
        self.access_token: Optional[str] = None
        self.user_id: Optional[str] = None

        # Load from environment variables first
        self.api_key = os.getenv("KITE_API_KEY")
        self.api_secret = os.getenv("KITE_API_SECRET")
        self.access_token = os.getenv("KITE_ACCESS_TOKEN")

        # Load from config file if not in env
        if not self.api_key or not self.api_secret:
            self.load_from_file()

        # Load access token from file if not in env
        if not self.access_token:
            self.load_access_token()

    def load_from_file(self):
        """Load configuration from JSON file"""
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    self.api_key = config.get("api_key")
                    self.api_secret = config.get("api_secret")
                    self.user_id = config.get("user_id")
                    logger.info("Kite config loaded from file")
        except Exception as e:
            logger.warning(f"Failed to load config from file: {e}")

    def save_to_file(self):
        """Save configuration to JSON file (excluding access_token)"""
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)

            config = {
                "api_key": self.api_key,
                "api_secret": self.api_secret,
                "user_id": self.user_id,
            }

            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)

            logger.info("Kite config saved to file")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def load_access_token(self):
        """Load access token from file"""
        try:
            if TOKEN_FILE.exists():
                with open(TOKEN_FILE, 'r') as f:
                    self.access_token = f.read().strip()
                    logger.info("Access token loaded from file")
        except Exception as e:
            logger.warning(f"Failed to load access token: {e}")

    def save_access_token(self, access_token: str):
        """Save access token to file"""
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with open(TOKEN_FILE, 'w') as f:
                f.write(access_token)
            self.access_token = access_token
            logger.info("Access token saved to file")
        except Exception as e:
            logger.error(f"Failed to save access token: {e}")

    def is_configured(self) -> bool:
        """Check if API key and secret are configured"""
        return bool(self.api_key and self.api_secret)

    def has_access_token(self) -> bool:
        """Check if access token is available"""
        return bool(self.access_token)


# Singleton instance
_config_instance: Optional[KiteConfig] = None


def get_kite_config() -> KiteConfig:
    """Get singleton KiteConfig instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = KiteConfig()
    return _config_instance
