from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from pathlib import Path

# Get the project root directory (two levels up from this file)
PROJECT_ROOT = Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    """
    Settings for the application.
    """

    # Redis settings
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None

    # email settings
    brevo_smtp_host: str = ""
    brevo_smtp_port: int = 587
    brevo_smtp_username: str = ""
    brevo_smtp_password: str = ""
    brevo_sender: str = ""
    no_reply_email: str = ""

    # OTP settings
    otp_secret: str = ""
    otp_expires_seconds: int = 300

    # Database settings
    postgres_url: str
    debug: bool = False

    # jwt secret
    access_token_secret_key: str = ""
    algorithm: str = ""
    access_token_expires_minute: int = 30
    refresh_token_secret_key: str = ""
    refresh_token_expires_day: int = 7

    # Password policy
    min_length: int = 10
    max_length: int = 20
    includes_special_chars: bool = True
    includes_numbers: bool = True
    includes_lowercase: bool = True
    includes_uppercase: bool = True

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        case_sensitive=False,
        extra="ignore",
        env_file_encoding="utf-8",
    )


settings = Settings()


def get_settings() -> Settings:
    """
    Get the application settings.
    """
    return settings
