"""Application configuration settings."""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Core settings for MandateLens API."""
    
    PROJECT_NAME: str = "MandateLens API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    # Server configuration
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    
    # CORS settings - development defaults for Next.js
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    
    # Database Configuration (PostgreSQL 16)
    POSTGRES_DB: str = "mandatelens"
    POSTGRES_USER: str = "mandatelens_dev"
    POSTGRES_PASSWORD: str = "mandatelens_dev_password"
    DATABASE_URL: str = "postgresql+psycopg://mandatelens_dev:mandatelens_dev_password@127.0.0.1:5432/mandatelens"
    TEST_DATABASE_URL: str = "postgresql+psycopg://mandatelens_dev:mandatelens_dev_password@127.0.0.1:5432/mandatelens_test"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
