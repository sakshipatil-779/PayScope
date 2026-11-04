"""Application configuration settings."""
from typing import List, Union
import json
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
    BACKEND_CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "https://pay-scope-lake.vercel.app",
        "https://payscope.vercel.app",
    ]
    BACKEND_CORS_ORIGIN_REGEX: str = r"^https:\/\/(pay-scope-lake|payscope)(-[a-zA-Z0-9_-]+)?\.vercel\.app$"

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        base_origins = [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:3001",
            "https://pay-scope-lake.vercel.app",
            "https://payscope.vercel.app",
        ]
        
        parsed_origins: List[str] = []
        if isinstance(v, str):
            v_str = v.strip()
            if v_str.startswith("[") and v_str.endswith("]"):
                try:
                    parsed = json.loads(v_str)
                    if isinstance(parsed, list):
                        parsed_origins = [str(i).strip().rstrip("/") for i in parsed if str(i).strip()]
                except Exception:
                    parsed_origins = [i.strip().rstrip("/") for i in v_str.strip("[]").split(",") if i.strip()]
            else:
                parsed_origins = [i.strip().rstrip("/") for i in v_str.split(",") if i.strip()]
        elif isinstance(v, list):
            parsed_origins = [str(i).strip().rstrip("/") for i in v if str(i).strip()]
        
        all_origins = base_origins + parsed_origins
        seen = set()
        deduped: List[str] = []
        for origin in all_origins:
            if origin and origin != "*" and origin not in seen:
                seen.add(origin)
                deduped.append(origin)
        
        return deduped
    
    # Database Configuration (PostgreSQL 16 / Neon)
    POSTGRES_DB: str = "mandatelens"
    POSTGRES_USER: str = "mandatelens_dev"
    POSTGRES_PASSWORD: str = "mandatelens_dev_password"
    DATABASE_URL: str = "postgresql+psycopg://mandatelens_dev:mandatelens_dev_password@127.0.0.1:5432/mandatelens"
    TEST_DATABASE_URL: str = "postgresql+psycopg://mandatelens_dev:mandatelens_dev_password@127.0.0.1:5432/mandatelens_test"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str) -> str:
        if not v:
            return v
        # Detect unconfigured placeholder URLs (such as example 'ep-xyz.neon.tech' or 'CHANGE_ME')
        if "ep-xyz.neon.tech" in v or "CHANGE_ME" in v:
            return "postgresql+psycopg://mandatelens_dev:mandatelens_dev_password@127.0.0.1:5432/mandatelens"
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+psycopg://", 1)
        elif v.startswith("postgresql://") and not v.startswith("postgresql+psycopg://"):
            return v.replace("postgresql://", "postgresql+psycopg://", 1)
        return v
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
