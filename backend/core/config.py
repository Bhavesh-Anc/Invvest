"""
Configuration settings for QuantEdge Pro API
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings"""

    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"

    # API Configuration
    API_V1_PREFIX: str = "/api"
    PROJECT_NAME: str = "QuantEdge Pro API"
    VERSION: str = "1.0.0"

    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://localhost:3000",
        # Add your Vercel deployment URL here
        "https://*.vercel.app",
    ]

    # Database (SQLite for now, can upgrade to PostgreSQL)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./data/quantedge.db"
    )

    # Market Data APIs
    ZERODHA_API_KEY: str = os.getenv("ZERODHA_API_KEY", "")
    ZERODHA_API_SECRET: str = os.getenv("ZERODHA_API_SECRET", "")

    UPSTOX_API_KEY: str = os.getenv("UPSTOX_API_KEY", "")
    UPSTOX_API_SECRET: str = os.getenv("UPSTOX_API_SECRET", "")

    ANGEL_ONE_API_KEY: str = os.getenv("ANGEL_ONE_API_KEY", "")
    ANGEL_ONE_CLIENT_ID: str = os.getenv("ANGEL_ONE_CLIENT_ID", "")

    # Cache Configuration
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    CACHE_TTL: int = 60  # seconds

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100

    # ML Models Path
    MODELS_PATH: str = "./models"

    # Data Storage
    DATA_PATH: str = "./data"

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
