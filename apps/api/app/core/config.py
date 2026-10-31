"""Application configuration settings."""
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Core settings for PayScope API."""
    
    PROJECT_NAME: str = "PayScope API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    # Server configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # CORS settings - development defaults and production origins
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "https://payscope.vercel.app",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["*"]
    
    # Database Configuration (PostgreSQL 16 / Neon)
    POSTGRES_DB: str = "mandatelens"
    POSTGRES_USER: str = "mandatelens_dev"
    POSTGRES_PASSWORD: str = "mandatelens_dev_password"
    DATABASE_URL: str = "postgresql+psycopg://mandatelens_dev:mandatelens_dev_password@127.0.0.1:5432/mandatelens"
    TEST_DATABASE_URL: str = "postgresql+psycopg://mandatelens_dev:mandatelens_dev_password@127.0.0.1:5432/mandatelens_test"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str) -> str:
        if v and v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+psycopg://", 1)
        elif v and v.startswith("postgresql://") and not v.startswith("postgresql+psycopg://"):
            return v.replace("postgresql://", "postgresql+psycopg://", 1)
        return v
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
