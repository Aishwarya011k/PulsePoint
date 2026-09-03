"""Configuration for the checks consumer service."""
import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application settings."""

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://pulse_user:aishu@localhost:5432/pulsepoint",
    )
    KAFKA_BOOTSTRAP_SERVERS = os.getenv(
        "KAFKA_BOOTSTRAP_SERVERS",
        "pulsepoint-kafka-kafka-bootstrap:9092",
    )
    KAFKA_CHECKS_TOPIC = os.getenv("KAFKA_CHECKS_TOPIC", "checks")
    KAFKA_CONSUMER_GROUP = os.getenv("KAFKA_CONSUMER_GROUP", "pulsepoint-checks-consumer")
    KAFKA_AUTO_OFFSET_RESET = os.getenv("KAFKA_AUTO_OFFSET_RESET", "earliest")
    REDIS_URL = os.getenv(
        "REDIS_URL",
        "redis://redis:6379",
    )


config = Config()
