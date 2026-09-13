"""Prometheus metrics for the backend API."""
import logging

from prometheus_client import Counter, Gauge, Histogram, make_asgi_app

from app.database import SessionLocal
from app.models import Incident, IncidentStatus, Target

logger = logging.getLogger(__name__)

REQUESTS = Counter(
    "pulsepoint_api_requests_total",
    "Total HTTP requests handled by the backend API.",
    ["method", "path", "status"],
)
REQUEST_LATENCY = Histogram(
    "pulsepoint_api_request_duration_seconds",
    "HTTP request duration in seconds.",
    ["method", "path"],
)
REGISTERED_TARGETS = Gauge(
    "pulsepoint_registered_targets",
    "Number of registered targets.",
)
OPEN_INCIDENTS = Gauge(
    "pulsepoint_open_incidents",
    "Number of currently open incidents.",
)


def refresh_database_metrics() -> None:
    """Refresh gauges from the authoritative Postgres tables."""
    session = SessionLocal()
    try:
        REGISTERED_TARGETS.set(session.query(Target).count())
        OPEN_INCIDENTS.set(
            session.query(Incident).filter(Incident.status == IncidentStatus.OPEN).count()
        )
    except Exception:
        logger.debug("Unable to refresh database metrics", exc_info=True)
    finally:
        session.close()


def metrics_app():
    """Return the ASGI application served at /metrics."""
    refresh_database_metrics()
    return make_asgi_app()
