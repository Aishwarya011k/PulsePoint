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
        "postgresql://pulse_user:aishu@localhost:5432/pulsepoint"
    )

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS = os.getenv(
        "KAFKA_BOOTSTRAP_SERVERS",
        "pulsepoint-kafka-kafka-bootstrap:9092",
    )
    KAFKA_CHECKS_TOPIC = os.getenv("KAFKA_CHECKS_TOPIC", "checks")
    
    # Scheduler
    CHECK_INTERVAL_SECONDS = int(os.getenv("CHECK_INTERVAL_SECONDS", "60"))
    
    # HTTP Client
    HTTP_TIMEOUT_SECONDS = int(os.getenv("HTTP_TIMEOUT_SECONDS", "10"))
    HTTP_RETRIES = 1


config = Config()
