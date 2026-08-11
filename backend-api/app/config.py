"""Configuration management for the backend API."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str = "postgresql://pulse_user:pulse_password@localhost:5432/pulsepoint"
    
    # JWT
    jwt_secret: str = "your_super_secret_jwt_key_change_this_in_production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # API
    api_port: int = 8000
    api_host: str = "0.0.0.0"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
