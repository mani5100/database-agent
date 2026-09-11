# src/database_agent/core/config.py

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- App ---
    app_name: str = "database-agent"
    environment: str = "development"  # development | production
    debug: bool = True

    # --- Redis (session metadata store) ---
    redis_url: str = "redis://localhost:6379/0"
    redis_session_ttl_seconds: int = 1800  # idle session expiry, 30 min default

    # --- DuckDB (file-based sources: CSV, Excel, Google Sheets) ---
    duckdb_memory_limit: str = "1GB"

    # --- Connection limits ---
    max_active_sessions: int = 50  # soft cap, guards against unbounded pool growth
    connection_timeout_seconds: int = 10
    
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "gpt-oss:latest"


    qdrant_url: str = "http://localhost:6333"
    qdrant_collection_name: str = "semantic_layer_columns"

    # --- Ollama embeddings ---
    ollama_embedding_model: str = "nomic-embed-text:latest"
    
    
    # --- Google OAuth (private Google Sheets access) ---
    google_oauth_client_id: str = ""
    google_oauth_client_secret: str = ""
    google_oauth_redirect_uri: str = "http://localhost:8000/auth/google/callback"
    
    # --- LangSmith (tracing/observability) ---
    langsmith_tracing: bool = True
    langsmith_endpoint: str = "https://api.smith.langchain.com"
    langsmith_api_key: str = ""
    langsmith_project: str = "database-agent"
    
    checkpoint_db_uri: str = "postgresql://agent:agent@localhost:5434/checkpoints"
    
    # --- Allowed source types (used for request validation) ---
    allowed_source_types: tuple[str, ...] = (
        "postgres",
        "mysql",
        "csv",
        "excel",
        "google_sheets",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()