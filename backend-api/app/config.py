"""Configuration management for the backend API."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str = "postgresql://pulse_user:pulse_password@postgres:5432/pulsepoint"
    
    # JWT
    jwt_secret: str = "h3lf5UcDTKJUOcyrrEslPi9ZSHOgw7l6bsCA2SkSCoa"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # API
    api_port: int = 8000
    api_host: str = "0.0.0.0"
    internal_api_token: str = "3894c24bcc81591472a3a2878b80682c2cc35a44aa55d2fd59258c7a93bfd775"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
