import os
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    PROJECT_NAME: str = "SmartStock AI"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = "development-secret-key-must-be-changed-in-production-32bytes"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            if isinstance(v, str):
                import json

                try:
                    return json.loads(v)
                except Exception:
                    return ["http://localhost:3000"]
            return v
        return ["http://localhost:3000"]

    # Database
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./smartstock_dev.db"
    )
    DATABASE_URL_SYNC: str = Field(
        default="sqlite:///./smartstock_dev.db"
    )

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: str = "redis://localhost:6379/0"

    # Market Data Provider & Live Data Integration
    MARKET_DATA_PROVIDER: str = "yahoo"  # Options: yahoo, truedata, benchmark_fixture
    MARKET_DATA_API_KEY: str = ""
    TRUEDATA_USERNAME: str = ""
    TRUEDATA_PASSWORD: str = ""
    TRUEDATA_URL: str = "https://history.truedata.in"
    TRUEDATA_WS_URL: str = "wss://ws.truedata.in"
    TRUEDATA_PORT: int = 8082

    # Optional OpenAI-compatible model for the conversational stock assistant
    AI_API_KEY: str = ""
    AI_BASE_URL: str = "https://api.openai.com/v1"
    AI_MODEL: str = "gpt-4o-mini"

    # Email / SMTP Configuration
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAILS_FROM_EMAIL: str = "noreply@smartstock.com"

    # Security & Tokens
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Default Wallet Configuration
    DEFAULT_VIRTUAL_BALANCE_PAISE: int = 50000  # ₹500.00


settings = Settings()
