"""Consume checks, evaluate Redis history, and publish deduplicated incidents."""
import json
import logging
from datetime import UTC, datetime

import redis
from confluent_kafka import Consumer, KafkaError, Producer
from prometheus_client import Counter, start_http_server
from sqlalchemy import create_engine, text

from config import config
from detector import detect_anomalies
from summarizer import summarize_incident

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
ANOMALIES = Counter("pulsepoint_ai_anomalies_total", "Detected predictive anomalies", ["type"])


def get_redis():
    return redis.from_url(config.REDIS_URL, decode_responses=True, socket_connect_timeout=2, socket_timeout=2)


def get_target_name(engine, target_id: int) -> str:
    """Load display metadata only; recent checks remain Redis-backed."""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT name FROM targets WHERE id = :target_id"), {"target_id": target_id}).scalar_one_or_none()
            return result or f"Target #{target_id}"
    except Exception as exc:  # noqa: BLE001 - metadata must not block anomaly delivery
        logger.warning("Target metadata lookup failed for %s: %s", target_id, exc)
        return f"Target #{target_id}"


def read_window(client, event: dict) -> list[dict]:
    """Read the checks-consumer window and include the current event during Kafka races."""
    values = [json.loads(raw) for raw in client.lrange(f"target:{event['target_id']}:recent_checks", 0, 19)]
    if not any(item.get("checked_at") == event.get("checked_at") for item in values):
        values.insert(0, event)
    return values


def publish_incident(producer, client, database_engine, event: dict, signal: dict) -> bool:
    key = f"ai:anomaly:{event['target_id']}:{signal['anomaly_type']}"
    if not client.set(key, "1", nx=True, ex=config.ANOMALY_COOLDOWN_SECONDS):
        return False
    incident = {
        "target_id": event["target_id"],
        "target_name": get_target_name(database_engine, event["target_id"]),
        "anomaly_type": signal["anomaly_type"],
        "confidence": signal["confidence"],
        "severity": signal["severity"],
        "timestamp": datetime.now(UTC).isoformat(),
        "recent_window": signal.get("window", []),
        "details": signal["details"],
    }
    incident["summary"] = summarize_incident(incident)
    producer.produce(config.KAFKA_INCIDENTS_TOPIC, key=str(event["target_id"]), value=json.dumps(incident).encode())
    producer.flush(timeout=5)
    ANOMALIES.labels(signal["anomaly_type"]).inc()
    return True


def consume_checks():
    start_http_server(9002)
    client = get_redis()
    database_engine = create_engine(config.DATABASE_URL, pool_pre_ping=True)
    consumer = Consumer({"bootstrap.servers": config.KAFKA_BOOTSTRAP_SERVERS, "group.id": config.KAFKA_CONSUMER_GROUP, "auto.offset.reset": config.KAFKA_AUTO_OFFSET_RESET, "enable.auto.commit": False})
    producer = Producer({"bootstrap.servers": config.KAFKA_BOOTSTRAP_SERVERS, "acks": "all", "retries": 3})
    consumer.subscribe([config.KAFKA_CHECKS_TOPIC])
    try:
        while True:
            message = consumer.poll(1.0)
            if message is None:
                continue
            if message.error():
                if message.error().code() != KafkaError._PARTITION_EOF:
                    logger.error("Kafka error: %s", message.error())
                continue
            event = json.loads(message.value().decode())
            try:
                window = read_window(client, event)
                for signal in detect_anomalies(window, config.LATENCY_ZSCORE, config.FAILURE_RATE_THRESHOLD):
                    signal["window"] = window[:20]
                    if publish_incident(producer, client, database_engine, event, signal):
                        logger.warning("Published %s for target %s", signal["anomaly_type"], event["target_id"])
                consumer.commit(asynchronous=False)
            except Exception:
                logger.exception("Failed to process check event")
    except KeyboardInterrupt:
        logger.info("Stopping AI engine")
    finally:
        consumer.close()


if __name__ == "__main__":
    consume_checks()
