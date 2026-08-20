"""Configuration management for the backend API."""
import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = "sqlite:///./pulsepoint.db"

    # JWT
    jwt_secret: str = "h3lf5UcDTKJUOcyrrEslPi9ZSHOgw7l6bsCA2SkSCoa"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # API
    api_port: int = 8000
    api_host: str = "0.0.0.0"
    internal_api_token: str = "3894c24bcc81591472a3a2878b80682c2cc35a44aa55d2fd59258c7a93bfd775"

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        """Ignore .env during pytest runs so tests use SQLite reliably."""
        if os.getenv("PYTEST_CURRENT_TEST") or os.getenv("TESTING") == "1":
            return (
                init_settings,
                env_settings,
                file_secret_settings,
            )
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )


settings = Settings()
