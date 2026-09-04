import os
import json
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application Settings loaded from environment variables or .env file."""

    model_config = SettingsConfigDict(
        env_file=(
            os.path.join(os.path.dirname(__file__), "..", ".env"),
            ".env",
        ),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    APP_NAME: str = "Pulse Discovery Engine"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = Field(
        default="sqlite:///./intently.db",
        description="Database connection URL"
    )

    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for Celery broker"
    )

    # Gemini LLM
    GEMINI_API_KEY: str = Field(
        default="",
        description="Google AI Studio Gemini API Key"
    )
    GEMINI_FLASH_MODEL: str = "gemini-3.6-flash"
    GEMINI_PRO_MODEL: str = "gemini-3.6-flash"

    # Security & Public Access
    PUBLIC_ACCESS_MODE: bool = Field(
        default=True,
        description="When True, allows public read access and unrestricted UI interaction for portfolio/demo deployment"
    )
    API_SECRET_KEY: str = Field(
        default="pulse-secret-dev-key-change-in-prod",
        description="API Key for internal/admin authentication"
    )
    CORS_ORIGINS: Union[List[str], str] = [
        "*",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Union[str, List[str]]) -> List[str]:
        if isinstance(value, str):
            value = value.strip()
            if value == "*":
                return ["*"]
            if value.startswith("[") and value.endswith("]"):
                try:
                    return json.loads(value)
                except Exception:
                    pass
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        # Normalize Railway postgres:// to postgresql+psycopg2://
        if value and value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+psycopg2://", 1)
        if value and value.startswith("postgresql://") and not value.startswith("postgresql+"):
            return value.replace("postgresql://", "postgresql+psycopg2://", 1)
        if value and value.startswith("sqlite:///./"):
            # Resolve relative SQLite path checking backend dir first, then workspace root
            db_name = value.replace("sqlite:///./", "")
            backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            root_dir = os.path.abspath(os.path.join(backend_dir, ".."))
            backend_db = os.path.join(backend_dir, db_name)
            root_db = os.path.join(root_dir, db_name)
            if os.path.exists(backend_db):
                db_path = backend_db.replace("\\", "/")
            elif os.path.exists(root_db):
                db_path = root_db.replace("\\", "/")
            else:
                db_path = backend_db.replace("\\", "/")
            return f"sqlite:///{db_path}"
        return value


settings = Settings()
