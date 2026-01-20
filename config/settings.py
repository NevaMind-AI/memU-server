"""Application settings and configuration management."""
from pathlib import Path
from typing import Any

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Attributes are automatically loaded from environment variables
    or .env file with the same name (case-insensitive).
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # ===================================
    # Database Configuration
    # ===================================
    DATABASE_HOST: str = Field(default="localhost", description="PostgreSQL host")
    DATABASE_PORT: int = Field(default=5432, description="PostgreSQL port")
    DATABASE_USER: str = Field(..., description="PostgreSQL username")
    DATABASE_PASSWORD: str = Field(..., description="PostgreSQL password")
    DATABASE_NAME: str = Field(..., description="PostgreSQL database name")
    
    @computed_field
    @property
    def database_url(self) -> str:
        """Construct async PostgreSQL connection URL."""
        return (
            f"postgresql+psycopg://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}"
            f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        )
    
    # ===================================
    # Temporal Configuration
    # ===================================
    TEMPORAL_HOST: str = Field(default="localhost", description="Temporal server host")
    TEMPORAL_PORT: int = Field(default=7233, description="Temporal server port")
    TEMPORAL_NAMESPACE: str = Field(default="default", description="Temporal namespace")
    
    @computed_field
    @property
    def temporal_url(self) -> str:
        """Construct Temporal server URL."""
        return f"{self.TEMPORAL_HOST}:{self.TEMPORAL_PORT}"
    
    # ===================================
    # LLM Configuration
    # ===================================
    OPENAI_API_KEY: str = Field(..., description="OpenAI API key")
    OPENAI_BASE_URL: str = Field(
        default="https://api.openai.com/v1",
        description="OpenAI API base URL"
    )
    DEFAULT_LLM_MODEL: str = Field(
        default="gpt-4o-mini",
        description="Default LLM model to use"
    )
    
    # ===================================
    # Embedding Configuration
    # ===================================
    EMBEDDING_API_KEY: str = Field(..., description="Embedding service API key")
    EMBEDDING_BASE_URL: str = Field(
        default="https://api.voyageai.com/v1",
        description="Embedding service base URL"
    )
    EMBEDDING_MODEL: str = Field(
        default="voyage-3.5-lite",
        description="Embedding model to use"
    )
    
    # ===================================
    # Storage Configuration
    # ===================================
    STORAGE_PATH: str = Field(
        default="/var/data/memu-server",
        description="Path for file storage"
    )
    
    @computed_field
    @property
    def storage_dir(self) -> Path:
        """Get storage directory as Path object, ensure it exists."""
        path = Path(self.STORAGE_PATH)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    # ===================================
    # Application Configuration
    # ===================================
    APP_NAME: str = Field(default="MemU Server", description="Application name")
    APP_VERSION: str = Field(default="0.1.0", description="Application version")
    DEBUG: bool = Field(default=False, description="Debug mode")
    
    def model_dump_safe(self) -> dict[str, Any]:
        """
        Dump settings without sensitive information.
        
        Returns:
            Dictionary with settings, excluding sensitive keys.
        """
        data = self.model_dump()
        # Remove sensitive keys
        sensitive_keys = [
            "DATABASE_PASSWORD",
            "OPENAI_API_KEY",
            "EMBEDDING_API_KEY",
        ]
        for key in sensitive_keys:
            if key in data:
                data[key] = "***HIDDEN***"
        return data


# Global settings instance
settings = Settings()