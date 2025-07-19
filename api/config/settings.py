from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Settings for the application.
    """

    # Database settings
    postgres_url: str
    debug: bool = False

    # jwt secret
    access_token_secret_key: str = ""
    algorithm: str = ""
    access_token_expires_minute: int = 30
    refresh_token_secret_key: str = ""
    refresh_token_expires_day: int = 7

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()


def get_settings() -> Settings:
    """
    Get the application settings.
    """
    return settings
