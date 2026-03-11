from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Application settings - loads from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="POKEMON_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database settings
    db_path: Path = Path("pokemon_cards.db")
    db_echo: bool = False

    # API settings
    api_title: str = "Pokemon Collection API"
    api_version: str = "1.0.0"

    # Logging settings
    log_level: str = "INFO"
    log_file: Path | None = (
        None  # Set to path like "logs/app.log" to enable file logging
    )


# Singleton instance
settings = AppSettings()
