"""Configuration for the incident notification consumer."""
import os


class Config:
    KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "pulsepoint-kafka-kafka-bootstrap:9092")
    KAFKA_INCIDENTS_TOPIC = os.getenv("KAFKA_INCIDENTS_TOPIC", "incidents")
    KAFKA_CONSUMER_GROUP = os.getenv("KAFKA_CONSUMER_GROUP", "pulsepoint-chatops")
    KAFKA_AUTO_OFFSET_RESET = os.getenv("KAFKA_AUTO_OFFSET_RESET", "earliest")
    SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
    DASHBOARD_URL = os.getenv("DASHBOARD_URL", "http://localhost:30080")


config = Config()
