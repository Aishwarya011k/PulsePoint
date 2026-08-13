import math
import re
from datetime import datetime, timedelta
from typing import List, Dict
from sqlalchemy.orm import Session
from app.models import Target, Check


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "target"


def generate_unique_slug(db: Session, name: str) -> str:
    base_slug = slugify(name)
    candidate = base_slug
    suffix = 1
    while db.query(Target).filter(Target.public_slug == candidate).first():
        candidate = f"{base_slug}-{suffix}"
        suffix += 1
    return candidate


def percentile(values: List[float], percent: float) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(values)
    k = (len(sorted_values) - 1) * percent / 100
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_values[int(k)]
    d = k - f
    return sorted_values[f] + (sorted_values[c] - sorted_values[f]) * d


def build_timeseries_response(
    checks: List[Check],
    start_time: datetime,
    bucket_seconds: int,
) -> Dict:
    buckets: Dict[datetime, Dict[str, object]] = {}
    for check in checks:
        if check.checked_at < start_time:
            continue
        bucket_index = int((check.checked_at - start_time).total_seconds() // bucket_seconds)
        bucket_start = start_time + timedelta(seconds=bucket_index * bucket_seconds)
        bucket = buckets.setdefault(
            bucket_start,
            {
                "response_times": [],
                "success_count": 0,
                "total_count": 0,
                "has_failure": False,
            },
        )
        bucket["response_times"].append(check.response_time_ms)
        bucket["success_count"] += 1 if check.success else 0
        bucket["total_count"] += 1
        if not check.success:
            bucket["has_failure"] = True

    points = []
    for bucket_start in sorted(buckets.keys()):
        bucket = buckets[bucket_start]
        avg_response = (
            sum(bucket["response_times"]) / len(bucket["response_times"])
            if bucket["response_times"]
            else 0.0
        )
        points.append(
            {
                "timestamp": bucket_start,
                "response_time_ms": avg_response,
                "success": bucket["success_count"] == bucket["total_count"],
                "has_failure": bucket["has_failure"],
            }
        )

    return points


def calculate_uptime_percentage(checks: List[Check]) -> float:
    if not checks:
        return 100.0
    success_count = sum(1 for check in checks if check.success)
    return round(success_count / len(checks) * 100, 2)


def build_daily_uptime_history(checks: List[Check], days: int) -> List[Dict[str, object]]:
    now = datetime.utcnow()
    history = []
    for day_offset in range(days - 1, -1, -1):
        day_start = datetime(
            year=(now - timedelta(days=day_offset)).year,
            month=(now - timedelta(days=day_offset)).month,
            day=(now - timedelta(days=day_offset)).day,
        )
        day_end = day_start + timedelta(days=1)
        daily_checks = [check for check in checks if day_start <= check.checked_at < day_end]
        uptime = calculate_uptime_percentage(daily_checks)
        if uptime == 100.0:
            status = "operational"
        elif uptime >= 90.0:
            status = "degraded"
        else:
            status = "outage"
        history.append(
            {
                "date": day_start.date().isoformat(),
                "uptime_percentage": uptime,
                "status": status,
            }
        )
    return history


def current_status_from_checks(checks: List[Check]) -> str:
    if not checks:
        return "unknown"
    latest = max(checks, key=lambda check: check.checked_at)
    return "operational" if latest.success else "degraded"
