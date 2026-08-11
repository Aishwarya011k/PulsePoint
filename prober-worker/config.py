"""Configuration for the prober worker."""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration settings."""
    
    # Database
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://pulse_user:pulse_password@localhost:5432/pulsepoint"
    )
    
    # Scheduler
    CHECK_INTERVAL_SECONDS = 60  # Base interval to check for targets that need checking
    
    # HTTP Client
    HTTP_TIMEOUT_SECONDS = 10
    HTTP_RETRIES = 1


config = Config()
