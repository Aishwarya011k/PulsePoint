"""Main prober worker that performs health checks on a schedule."""
import logging
import time
from datetime import UTC, datetime

import httpx
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import desc

from config import config
from database import Check, Incident, IncidentStatus, SessionLocal, Target

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


def perform_check(url: str) -> dict:
    """
    Perform an HTTP health check on a URL.
    
    Args:
        url: URL to check
        
    Returns:
        Dictionary with status_code, response_time_ms, and success
    """
    try:
        start_time = time.time()
        with httpx.Client(timeout=config.HTTP_TIMEOUT_SECONDS) as client:
            response = client.get(url, follow_redirects=True)
        end_time = time.time()
        
        response_time_ms = (end_time - start_time) * 1000
        success = 200 <= response.status_code < 300
        
        logger.info(
            f"Check successful for {url}: status={response.status_code}, "
            f"time={response_time_ms:.1f}ms"
        )
        
        return {
            "status_code": response.status_code,
            "response_time_ms": response_time_ms,
            "success": success,
        }
    except httpx.TimeoutException:
        logger.warning(f"Check timeout for {url}")
        return {
            "status_code": 0,
            "response_time_ms": config.HTTP_TIMEOUT_SECONDS * 1000,
            "success": False,
        }
    except httpx.HTTPError as exc:
        logger.error(f"Check failed for {url}: {exc}")
        return {
            "status_code": 0,
            "response_time_ms": 0,
            "success": False,
        }


def record_check(db, target_id: int, check_result: dict):
    """
    Record a check result and manage incidents.
    
    Args:
        db: Database session
        target_id: ID of the target being checked
        check_result: Result dictionary from perform_check()
    """
    try:
        target = db.query(Target).filter(Target.id == target_id).first()
        if not target:
            logger.warning(f"Target {target_id} not found")
            return
        
        # Get the previous check to detect status transitions
        previous_check = db.query(Check).filter(
            Check.target_id == target_id
        ).order_by(desc(Check.checked_at)).first()
        
        previous_success = previous_check.success if previous_check else True
        
        # Record the new check
        new_check = Check(
            target_id=target_id,
            status_code=check_result["status_code"],
            response_time_ms=check_result["response_time_ms"],
            success=check_result["success"],
            checked_at=datetime.now(UTC),
        )
        db.add(new_check)
        
        # Manage incidents based on status transition
        if previous_success and not check_result["success"]:
            # Transition from success to failure: open new incident
            logger.warning(f"Target {target_id} ({target.name}) went DOWN")
            new_incident = Incident(
                target_id=target_id,
                status=IncidentStatus.OPEN,
                started_at=datetime.now(UTC),
            )
            db.add(new_incident)
        elif not previous_success and check_result["success"]:
            # Transition from failure to success: resolve open incident
            logger.info(f"Target {target_id} ({target.name}) came BACK UP")
            open_incident = db.query(Incident).filter(
                Incident.target_id == target_id,
                Incident.status == IncidentStatus.OPEN,
            ).first()
            if open_incident:
                open_incident.status = IncidentStatus.RESOLVED
                open_incident.resolved_at = datetime.now(UTC)
        
        db.commit()
        logger.info(f"Check recorded for target {target_id}")
    except (ValueError, TypeError) as exc:
        logger.error(f"Error recording check for target {target_id}: {exc}")
        db.rollback()


def check_targets():
    """
    Check all targets that are due for a health check.
    
    This job runs periodically and checks all targets whose last check
    was more than their check_interval_seconds ago.
    
    TODO: In Phase 2+, add distributed lock or claim pattern for multi-replica safety
    """
    db = SessionLocal()
    try:
        logger.info("Starting health check cycle")
        
        # Get all targets
        targets = db.query(Target).all()
        
        if not targets:
            logger.info("No targets to check")
            return
        
        logger.info(f"Found {len(targets)} targets to check")
        
        for target in targets:
            # Get the last check
            last_check = db.query(Check).filter(
                Check.target_id == target.id
            ).order_by(desc(Check.checked_at)).first()
            
            # Determine if this target needs a check
            if last_check:
                time_since_check = datetime.now(UTC) - last_check.checked_at
                seconds_since_check = time_since_check.total_seconds()
                needs_check = seconds_since_check >= target.check_interval_seconds
            else:
                # Never been checked, so check now
                needs_check = True
            
            if needs_check:
                logger.info(f"Checking target {target.id}: {target.name} ({target.url})")
                check_result = perform_check(target.url)
                record_check(db, target.id, check_result)
            else:
                logger.debug(
                    f"Skipping target {target.id} - not due yet "
                    f"(interval: {target.check_interval_seconds}s)"
                )
        
        logger.info("Health check cycle completed")
    except (RuntimeError, ValueError) as exc:
        logger.error(f"Error in check_targets: {exc}")
    finally:
        db.close()


def start_worker():
    """Start the prober worker with APScheduler."""
    logger.info("Starting PulsePoint Prober Worker")
    
    # Create scheduler
    scheduler = BackgroundScheduler()
    
    # Add job to check targets every CHECK_INTERVAL_SECONDS
    scheduler.add_job(
        check_targets,
        'interval',
        seconds=config.CHECK_INTERVAL_SECONDS,
        id='check_targets',
        name='Health check cycle',
        misfire_grace_time=60,
    )
    
    # Start scheduler
    scheduler.start()
    logger.info(
        f"Scheduler started - will check targets every {config.CHECK_INTERVAL_SECONDS}s"
    )
    
    try:
        # Keep the scheduler running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down prober worker...")
        scheduler.shutdown()
        logger.info("Prober worker stopped")


if __name__ == "__main__":
    start_worker()
