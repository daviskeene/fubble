import os
from typing import Optional, Dict, Any, List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "FUBBLE"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./fubble.db")

    # JWT settings
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY", "super-secret-key-please-change-in-production"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS settings
    ALLOWED_ORIGINS: List[str] = ["*"]

    # Email settings
    SMTP_SERVER: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None

    # Payment service settings
    PAYMENT_API_KEY: Optional[str] = None
    PAYMENT_API_SECRET: Optional[str] = None

    # Billing settings
    DEFAULT_PAYMENT_TERM_DAYS: int = 30
    TAX_RATE: float = 0.0
    CURRENCY: str = "USD"

    # In Pydantic v2, the Config class is replaced with model_config
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


# Create global settings object
settings = Settings()


# Function to get settings
def get_settings() -> Settings:
    return settings
