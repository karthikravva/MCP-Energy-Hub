"""
Application configuration using Pydantic Settings
"""

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    app_name: str = "MCP Energy Hub"
    app_version: str = "1.0.0"
    debug: bool = False

    # Database (defaults to SQLite for easy deployment, use PostgreSQL for production)
    database_url: str = "sqlite+aiosqlite:///./mcp_energy.db"
    database_url_sync: str = "sqlite:///./mcp_energy.db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # EIA API
    eia_api_key: str = "1ZcuqVdyzysHYlYp6tyJgfvEBJwMOMklQ5ywwSjT"
    eia_base_url: str = "https://api.eia.gov/v2"

    # ISO API Keys
    caiso_api_key: Optional[str] = None
    ercot_api_key: Optional[str] = None
    pjm_api_key: Optional[str] = None
    nyiso_api_key: Optional[str] = None
    isone_api_key: Optional[str] = None
    miso_api_key: Optional[str] = None
    spp_api_key: Optional[str] = None

    # Ingestion
    ingestion_interval_minutes: int = 5
    batch_ingestion_hour: int = 2

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
