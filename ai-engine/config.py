"""Configuration for the predictive anomaly engine."""
import os


class Config:
    KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "pulsepoint-kafka-kafka-bootstrap:9092")
    KAFKA_CHECKS_TOPIC = os.getenv("KAFKA_CHECKS_TOPIC", "checks")
    KAFKA_INCIDENTS_TOPIC = os.getenv("KAFKA_INCIDENTS_TOPIC", "incidents")
    KAFKA_CONSUMER_GROUP = os.getenv("KAFKA_CONSUMER_GROUP", "pulsepoint-ai-engine")
    KAFKA_AUTO_OFFSET_RESET = os.getenv("KAFKA_AUTO_OFFSET_RESET", "earliest")
    REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://pulse_user:aishu@postgres:5432/pulsepoint")
    LOKI_URL = os.getenv("LOKI_URL", "http://loki.monitoring.svc.cluster.local:3100")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
    LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "8"))
    ANOMALY_COOLDOWN_SECONDS = int(os.getenv("ANOMALY_COOLDOWN_SECONDS", "900"))
    LATENCY_ZSCORE = float(os.getenv("LATENCY_ZSCORE", "2.0"))
    FAILURE_RATE_THRESHOLD = float(os.getenv("FAILURE_RATE_THRESHOLD", "0.3"))
    DASHBOARD_URL = os.getenv("DASHBOARD_URL", "http://localhost:30080")


config = Config()
