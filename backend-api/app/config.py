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
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # API
    api_port: int = 8000
    api_host: str = "0.0.0.0"
    internal_api_token: str = "dev-internal-token-change-me"

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        """Use environment overrides when provided while keeping test defaults safe."""
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
