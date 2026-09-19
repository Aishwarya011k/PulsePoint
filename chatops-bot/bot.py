"""Consume AI incidents and send concise Slack alerts."""
import json
import logging

import httpx
from confluent_kafka import Consumer, KafkaError
from prometheus_client import Counter, start_http_server

from config import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
ALERTS = Counter("pulsepoint_chatops_alerts_total", "Incident alerts sent to ChatOps")


def format_alert(incident: dict) -> dict:
    severity = str(incident.get("severity", "unknown")).upper()
    target = incident.get("target_name") or f"Target #{incident['target_id']}"
    text = (
        f"PulsePoint {severity}: {target} - {incident.get('anomaly_type', 'anomaly')}\n"
        f"Confidence: {incident.get('confidence', 'unknown')}\n"
        f"{incident.get('summary', 'AI summary unavailable')}\n"
        f"Dashboard: {config.DASHBOARD_URL}/targets/{incident['target_id']}"
    )
    return {"text": text}


def send_alert(incident: dict) -> bool:
    if not config.SLACK_WEBHOOK_URL:
        logger.warning("SLACK_WEBHOOK_URL is empty; incident was consumed but no alert was sent")
        return False
    response = httpx.post(config.SLACK_WEBHOOK_URL, json=format_alert(incident), timeout=5.0)
    response.raise_for_status()
    ALERTS.inc()
    return True


def consume_incidents():
    start_http_server(9003)
    consumer = Consumer({"bootstrap.servers": config.KAFKA_BOOTSTRAP_SERVERS, "group.id": config.KAFKA_CONSUMER_GROUP, "auto.offset.reset": config.KAFKA_AUTO_OFFSET_RESET, "enable.auto.commit": False})
    consumer.subscribe([config.KAFKA_INCIDENTS_TOPIC])
    try:
        while True:
            message = consumer.poll(1.0)
            if message is None:
                continue
            if message.error():
                if message.error().code() != KafkaError._PARTITION_EOF:
                    logger.error("Kafka error: %s", message.error())
                continue
            try:
                send_alert(json.loads(message.value().decode()))
                consumer.commit(asynchronous=False)
            except (httpx.HTTPError, ValueError):
                logger.exception("Failed to deliver incident; leaving it uncommitted for retry")
    except KeyboardInterrupt:
        logger.info("Stopping ChatOps bot")
    finally:
        consumer.close()


if __name__ == "__main__":
    consume_incidents()
