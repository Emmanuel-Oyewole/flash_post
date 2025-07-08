from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Settings for the application.
    """
    # Database settings
    postgres_ul: str = ""

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()

def get_settings() -> Settings:
    """
    Get the application settings.
    """
    return settings