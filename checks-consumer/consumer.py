"""Consume check events from Kafka and persist them to Postgres."""
import json
import logging
from datetime import UTC, datetime

import redis
from config import config
from confluent_kafka import Consumer, KafkaError
from database import Check, Incident, IncidentStatus, SessionLocal, Target
from sqlalchemy import desc

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


def get_redis_client():
    """
    Get Redis client for caching recent checks.

    Returns gracefully None if Redis is unavailable.
    """
    try:
        client = redis.from_url(
            config.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        client.ping()
        return client
    except Exception as e:
        logger.warning("Failed to connect to Redis: %s; rolling-window state store disabled", e)
        return None


def push_to_rolling_window(redis_client, target_id: int, event: dict):
    """
    Push check result to a Redis rolling-window list per target.

    Uses LPUSH to add new checks to the left, and LTRIM to keep only the last 20.
    This creates a bounded list of recent checks that Phase 8's AI Engine can consume
    without re-querying Postgres for every target on every evaluation cycle.

    Key naming: target:{target_id}:recent_checks

    Args:
        redis_client: Redis client instance (or None if unavailable)
        target_id: ID of the target
        event: Check event data (status_code, response_time_ms, success, checked_at)
    """
    if redis_client is None:
        return

    try:
        key = f"target:{target_id}:recent_checks"
        # Store just the essential check data (not the entire event)
        check_data = {
            "status_code": event["status_code"],
            "response_time_ms": event["response_time_ms"],
            "success": event["success"],
            "checked_at": event["checked_at"],
        }
        redis_client.lpush(key, json.dumps(check_data))
        # Keep only the last 20 checks per target
        redis_client.ltrim(key, 0, 19)
        logger.debug("Pushed check to rolling window for target %s", target_id)
    except Exception as e:
        logger.warning("Failed to push to rolling window for target %s: %s", target_id, e)


def apply_check_event(session, target, event: dict, previous_success: bool):
    """Persist an event and manage incident transitions."""
    new_check = Check(
        target_id=event["target_id"],
        status_code=event["status_code"],
        response_time_ms=event["response_time_ms"],
        success=event["success"],
        checked_at=datetime.fromisoformat(event["checked_at"]),
    )
    session.add(new_check)

    incident_opened = False
    incident_resolved = False

    if previous_success and not event["success"]:
        logger.warning("Target %s (%s) went DOWN", target.id, target.name)
        new_incident = Incident(
            target_id=target.id,
            status=IncidentStatus.OPEN,
            started_at=datetime.now(UTC),
        )
        session.add(new_incident)
        incident_opened = True
    elif not previous_success and event["success"]:
        logger.info("Target %s (%s) came BACK UP", target.id, target.name)
        open_incident = session.query(Incident).filter(
            Incident.target_id == target.id,
            Incident.status == IncidentStatus.OPEN,
        ).first()
        if open_incident:
            open_incident.status = IncidentStatus.RESOLVED
            open_incident.resolved_at = datetime.now(UTC)
            incident_resolved = True

    session.commit()
    return {
        "incident_opened": incident_opened,
        "incident_resolved": incident_resolved,
        "stored": True,
    }


def consume_checks():
    """Read check events from Kafka and store them in Postgres."""
    logger.info("Starting checks consumer")
    redis_client = get_redis_client()
    
    consumer = Consumer({
        "bootstrap.servers": config.KAFKA_BOOTSTRAP_SERVERS,
        "group.id": config.KAFKA_CONSUMER_GROUP,
        "auto.offset.reset": config.KAFKA_AUTO_OFFSET_RESET,
        "enable.auto.commit": False,
    })
    consumer.subscribe([config.KAFKA_CHECKS_TOPIC])

    try:
        while True:
            message = consumer.poll(timeout=1.0)
            if message is None:
                continue
            if message.error():
                if message.error().code() == KafkaError._PARTITION_EOF:
                    continue
                logger.error("Kafka consumer error: %s", message.error())
                continue

            event = json.loads(message.value().decode("utf-8"))
            session = SessionLocal()
            try:
                target_id = event["target_id"]
                target = session.query(Target).filter(Target.id == target_id).first()
                if not target:
                    logger.warning("Skipping event for unknown target %s", target_id)
                    continue

                previous_check = session.query(Check).filter(
                    Check.target_id == target_id,
                ).order_by(desc(Check.checked_at)).first()
                previous_success = previous_check.success if previous_check else True

                result = apply_check_event(session, target, event, previous_success)
                logger.info(
                    "Stored check for target %s; incident_opened=%s incident_resolved=%s",
                    target_id,
                    result["incident_opened"],
                    result["incident_resolved"],
                )
                
                # After Postgres commit, push to Redis rolling-window store
                # This allows Phase 8's AI Engine to consume recent trends without re-querying Postgres
                push_to_rolling_window(redis_client, target_id, event)
                
                consumer.commit(asynchronous=False)
            except Exception:  # pragma: no cover - defensive logging path
                logger.exception("Error processing event for target %s", event.get("target_id"))
                session.rollback()
            finally:
                session.close()
    except KeyboardInterrupt:
        logger.info("Shutting down checks consumer")
    finally:
        consumer.close()


if __name__ == "__main__":
    consume_checks()
