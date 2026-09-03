"""Target management routes."""
from datetime import UTC, datetime
from time import time
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.cache import cache_delete, cache_get, cache_set
from app.database import get_db
from app.dependencies import get_current_user
from app.models import Check, Incident, IncidentStatus, Target, User
from app.schemas import (
    CheckHistoryResponse,
    CheckResponse,
    TargetCreateRequest,
    TargetDetailResponse,
    TargetResponse,
)

router = APIRouter(prefix="/targets", tags=["targets"])


def perform_check(url: str) -> dict:
    """
    Perform an HTTP health check on a URL.

    Args:
        url: URL to check

    Returns:
        Dictionary with status_code, response_time_ms, and success
    """
    try:
        start_time = time()
        with httpx.Client(timeout=10) as client:
            response = client.get(url, follow_redirects=True)
        end_time = time()

        response_time_ms = (end_time - start_time) * 1000
        success = 200 <= response.status_code < 300

        return {
            "status_code": response.status_code,
            "response_time_ms": response_time_ms,
            "success": success,
        }
    except httpx.HTTPError:
        return {
            "status_code": 0,
            "response_time_ms": 0,
            "success": False,
        }


def record_check(db: Session, target_id: int, check_result: dict):
    """
    Record a check result and manage incidents.

    Args:
        db: Database session
        target_id: ID of the target being checked
        check_result: Result dictionary from perform_check()
    """
    target = db.query(Target).filter(Target.id == target_id).first()
    if not target:
        return

    previous_check = db.query(Check).filter(Check.target_id == target_id).order_by(desc(Check.checked_at)).first()
    previous_success = previous_check.success if previous_check else True

    new_check = Check(
        target_id=target_id,
        status_code=check_result["status_code"],
        response_time_ms=check_result["response_time_ms"],
        success=check_result["success"],
        checked_at=datetime.now(UTC),
    )
    db.add(new_check)

    if previous_success and not check_result["success"]:
        new_incident = Incident(
            target_id=target_id,
            status=IncidentStatus.OPEN,
            started_at=datetime.now(UTC),
        )
        db.add(new_incident)
    elif not previous_success and check_result["success"]:
        open_incident = db.query(Incident).filter(
            Incident.target_id == target_id,
            Incident.status == IncidentStatus.OPEN,
        ).first()
        if open_incident:
            open_incident.status = IncidentStatus.RESOLVED
            open_incident.resolved_at = datetime.now(UTC)

    db.commit()


@router.post("", response_model=TargetResponse)
def create_target(
    request: TargetCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Create a new monitoring target.

    Args:
        request: Target creation details
        db: Database session
        current_user: Authenticated user

    Returns:
        Created target
    """
    new_target = Target(
        user_id=current_user.id,
        name=request.name,
        url=request.url,
        check_interval_seconds=request.check_interval_seconds,
    )
    db.add(new_target)
    db.commit()
    db.refresh(new_target)
    
    # Invalidate targets list cache for this user
    cache_delete(f"targets:user:{current_user.id}")
    
    return new_target


@router.get("", response_model=list[TargetResponse])
def list_targets(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    response: Response,
):
    """
    List all targets for the current user.

    Results are cached per user with a 10-second TTL.
    Check the X-Cache response header to verify caching behavior.

    Args:
        db: Database session
        current_user: Authenticated user
        response: FastAPI response object for headers

    Returns:
        List of user's targets
    """
    cache_key = f"targets:user:{current_user.id}"
    
    # Try to get from cache first
    cached_targets = cache_get(cache_key)
    if cached_targets is not None:
        response.headers["X-Cache"] = "HIT"
        return cached_targets
    
    # Cache miss - query database
    targets = db.query(Target).filter(Target.user_id == current_user.id).all()
    response.headers["X-Cache"] = "MISS"
    
    # Store in cache with 10-second TTL
    cache_set(cache_key, targets, ttl=10)
    
    return targets


@router.get("/{target_id}", response_model=TargetDetailResponse)
def get_target(
    target_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    response: Response,
):
    """
    Get details of a specific target including recent checks.

    Results are cached per target with a 10-second TTL.
    Check the X-Cache response header to verify caching behavior.

    Args:
        target_id: ID of the target
        db: Database session
        current_user: Authenticated user
        response: FastAPI response object for headers

    Returns:
        Target with recent checks

    Raises:
        HTTPException: If target not found or not owned by user
    """
    cache_key = f"target:{target_id}:user:{current_user.id}"
    
    # Try to get from cache first
    cached_target = cache_get(cache_key)
    if cached_target is not None:
        response.headers["X-Cache"] = "HIT"
        return cached_target
    
    # Cache miss - query database
    target = db.query(Target).filter(Target.id == target_id).first()
    if not target or target.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target not found",
        )

    recent_checks = db.query(Check).filter(Check.target_id == target_id).order_by(desc(Check.checked_at)).limit(10).all()

    target_detail = TargetDetailResponse(
        id=target.id,
        name=target.name,
        url=target.url,
        check_interval_seconds=target.check_interval_seconds,
        created_at=target.created_at,
        recent_checks=recent_checks,
    )
    
    response.headers["X-Cache"] = "MISS"
    
    # Store in cache with 10-second TTL
    cache_set(cache_key, target_detail, ttl=10)
    
    return target_detail


@router.delete("/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_target(
    target_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Delete a target and all associated data.

    Args:
        target_id: ID of the target
        db: Database session
        current_user: Authenticated user

    Raises:
        HTTPException: If target not found or not owned by user
    """
    target = db.query(Target).filter(Target.id == target_id).first()
    if not target or target.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target not found",
        )

    db.delete(target)
    db.commit()
    
    # Invalidate both the specific target cache and the user's targets list cache
    cache_delete(f"target:{target_id}:user:{current_user.id}")
    cache_delete(f"targets:user:{current_user.id}")


@router.post("/{target_id}/check-now", response_model=CheckResponse)
def manual_check(
    target_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Trigger an immediate manual health check for a target.

    Args:
        target_id: ID of the target
        db: Database session
        current_user: Authenticated user

    Returns:
        Check result

    Raises:
        HTTPException: If target not found or not owned by user
    """
    target = db.query(Target).filter(Target.id == target_id).first()
    if not target or target.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target not found",
        )

    check_result = perform_check(target.url)
    record_check(db, target_id, check_result)

    new_check = db.query(Check).filter(Check.target_id == target_id).order_by(desc(Check.checked_at)).first()
    
    # Invalidate the target detail cache since we just added a new check
    cache_delete(f"target:{target_id}:user:{current_user.id}")
    
    return new_check


@router.get("/{target_id}/checks", response_model=CheckHistoryResponse)
def get_check_history(
    target_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    Get paginated check history for a target.

    Args:
        target_id: ID of the target
        limit: Number of checks to return (default 20, max 100)
        offset: Number of checks to skip (default 0)
        db: Database session
        current_user: Authenticated user

    Returns:
        Paginated check history

    Raises:
        HTTPException: If target not found or not owned by user
    """
    target = db.query(Target).filter(Target.id == target_id).first()
    if not target or target.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target not found",
        )

    total = db.query(Check).filter(Check.target_id == target_id).count()
    checks = db.query(Check).filter(Check.target_id == target_id).order_by(desc(Check.checked_at)).offset(offset).limit(limit).all()

    return CheckHistoryResponse(
        total=total,
        limit=limit,
        offset=offset,
        checks=checks,
    )
