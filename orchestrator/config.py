"""
PPTX POC - Orchestrator Configuration
Environment-based configuration using pydantic-settings
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Service info
    app_name: str = "PPTX Orchestrator API"
    app_version: str = "0.1.0"
    debug: bool = False

    # Ollama configuration
    ollama_host: str = "http://ollama:11434"
    ollama_model: str = "ministral-3:14b-instruct-2512-q8_0"
    ollama_timeout: int = 60  # seconds

    # PPTX Generator service
    pptx_generator_url: str = "http://pptx-generator:8001"
    pptx_generator_timeout: int = 30  # seconds

    # Input validation limits
    max_topic_length: int = 500
    max_slides: int = 10
    default_slides: int = 3

    # CORS settings
    cors_origins: list[str] = ["*"]  # Restrict in production
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses lru_cache to avoid reading .env file on every request.
    """
    return Settings()
