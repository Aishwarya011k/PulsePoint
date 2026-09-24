"""Incident detail and postmortem routes."""
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.cache import cache_delete
from app.database import get_db
from app.dependencies import get_current_user
from app.models import Incident, IncidentStatus, Target, User
from app.schemas import IncidentResponse, PostmortemUpdateRequest

router = APIRouter(prefix="/incidents", tags=["incidents"])


def get_owned_incident(incident_id: int, db: Session, user: User) -> Incident:
    incident = (
        db.query(Incident)
        .join(Target)
        .filter(Incident.id == incident_id, Target.user_id == user.id)
        .first()
    )
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return incident


@router.get("/{incident_id}", response_model=IncidentResponse)
def get_incident(
    incident_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    incident = get_owned_incident(incident_id, db, current_user)
    return incident


@router.patch("/{incident_id}/postmortem", response_model=IncidentResponse)
def update_postmortem(
    incident_id: int,
    request: PostmortemUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    incident = get_owned_incident(incident_id, db, current_user)
    if incident.status != IncidentStatus.RESOLVED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Postmortems require a resolved incident")
    incident.postmortem_note = request.note.strip()
    incident.postmortem_author = current_user.email
    incident.postmortem_updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(incident)
    cache_delete(f"target:{incident.target_id}:user:{current_user.id}")
    return incident
