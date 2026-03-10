from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Application settings - loads from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="POKEMON_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    db_path: str = "pokemon_cards.db"
    db_echo: bool = False
    api_title: str = "Pokemon Collection API"
    api_version: str = "1.0.0"


# Singleton instance
settings = AppSettings()
