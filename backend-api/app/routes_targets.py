"""Target management routes."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
import httpx
from app.database import get_db
from app.models import User, Target, Check, Incident, IncidentStatus
from app.schemas import (
    TargetCreateRequest,
    TargetResponse,
    TargetDetailResponse,
    CheckResponse,
    CheckHistoryResponse,
)
from app.dependencies import get_current_user

router = APIRouter(prefix="/targets", tags=["targets"])


def perform_check(url: str) -> dict:
    """
    Perform an HTTP health check on a URL.
    
    Args:
        url: URL to check
        
    Returns:
        Dictionary with status_code, response_time_ms, and success
    """
    import time
    
    try:
        start_time = time.time()
        with httpx.Client(timeout=10) as client:
            response = client.get(url, follow_redirects=True)
        end_time = time.time()
        
        response_time_ms = (end_time - start_time) * 1000
        success = 200 <= response.status_code < 300
        
        return {
            "status_code": response.status_code,
            "response_time_ms": response_time_ms,
            "success": success,
        }
    except Exception as e:
        # Connection error, timeout, etc.
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
        checked_at=datetime.utcnow(),
    )
    db.add(new_check)
    
    # Manage incidents based on status transition
    if previous_success and not check_result["success"]:
        # Transition from success to failure: open new incident
        new_incident = Incident(
            target_id=target_id,
            status=IncidentStatus.OPEN,
            started_at=datetime.utcnow(),
        )
        db.add(new_incident)
    elif not previous_success and check_result["success"]:
        # Transition from failure to success: resolve open incident
        open_incident = db.query(Incident).filter(
            Incident.target_id == target_id,
            Incident.status == IncidentStatus.OPEN,
        ).first()
        if open_incident:
            open_incident.status = IncidentStatus.RESOLVED
            open_incident.resolved_at = datetime.utcnow()
    
    db.commit()


@router.post("", response_model=TargetResponse)
def create_target(
    request: TargetCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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
    return new_target


@router.get("", response_model=list[TargetResponse])
def list_targets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all targets for the current user.
    
    Args:
        db: Database session
        current_user: Authenticated user
        
    Returns:
        List of user's targets
    """
    targets = db.query(Target).filter(Target.user_id == current_user.id).all()
    return targets


@router.get("/{target_id}", response_model=TargetDetailResponse)
def get_target(
    target_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get details of a specific target including recent checks.
    
    Args:
        target_id: ID of the target
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Target with recent checks
        
    Raises:
        HTTPException: If target not found or not owned by user
    """
    target = db.query(Target).filter(Target.id == target_id).first()
    if not target or target.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target not found",
        )
    
    # Get recent checks (last 10)
    recent_checks = db.query(Check).filter(
        Check.target_id == target_id
    ).order_by(desc(Check.checked_at)).limit(10).all()
    
    return TargetDetailResponse(
        id=target.id,
        name=target.name,
        url=target.url,
        check_interval_seconds=target.check_interval_seconds,
        created_at=target.created_at,
        recent_checks=recent_checks,
    )


@router.delete("/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_target(
    target_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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


@router.post("/{target_id}/check-now", response_model=CheckResponse)
def manual_check(
    target_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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
    
    # Perform the check
    check_result = perform_check(target.url)
    
    # Record the check and manage incidents
    record_check(db, target_id, check_result)
    
    # Get the newly created check
    new_check = db.query(Check).filter(
        Check.target_id == target_id
    ).order_by(desc(Check.checked_at)).first()
    
    return new_check


@router.get("/{target_id}/checks", response_model=CheckHistoryResponse)
def get_check_history(
    target_id: int,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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
    
    # Get total count
    total = db.query(Check).filter(Check.target_id == target_id).count()
    
    # Get paginated results
    checks = db.query(Check).filter(
        Check.target_id == target_id
    ).order_by(desc(Check.checked_at)).offset(offset).limit(limit).all()
    
    return CheckHistoryResponse(
        total=total,
        limit=limit,
        offset=offset,
        checks=checks,
    )
