"""Configuration settings for Neo4j Graph Intelligence."""
import os
from pydantic_settings import BaseSettings


class Neo4jSettings(BaseSettings):
    ENABLED: bool = os.getenv("NEO4J_ENABLED", "false").lower() in ("true", "1", "yes")
    URI: str = os.getenv("NEO4J_URI", "bolt://127.0.0.1:7687")
    USERNAME: str = os.getenv("NEO4J_USERNAME", "neo4j")
    PASSWORD: str = os.getenv("NEO4J_PASSWORD", "payscope_password")
    DATABASE: str = os.getenv("NEO4J_DATABASE", "neo4j")
    MAX_CONNECTION_LIFETIME: int = int(os.getenv("NEO4J_MAX_CONNECTION_LIFETIME", "3600"))
    MAX_CONNECTION_POOL_SIZE: int = int(os.getenv("NEO4J_MAX_CONNECTION_POOL_SIZE", "50"))

    class Config:
        env_prefix = "NEO4J_"
        extra = "ignore"


neo4j_settings = Neo4jSettings()
