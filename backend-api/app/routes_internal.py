from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Target
from app.config import settings
from app.websocket_manager import manager

router = APIRouter(prefix="/internal", tags=["internal"])


class CheckCompletedRequest(BaseModel):
    target_id: int
    status_code: int
    response_time_ms: float
    success: bool
    checked_at: datetime


@router.post("/check-completed")
def check_completed(
    request: CheckCompletedRequest,
    x_internal_token: str = Header(..., alias="X-Internal-Token"),
    db: Session = Depends(get_db),
):
    if x_internal_token != settings.internal_api_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    target = db.query(Target).filter(Target.id == request.target_id).first()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target not found")

    message = {
        "type": "check_completed",
        "payload": {
            "target_id": request.target_id,
            "status_code": request.status_code,
            "response_time_ms": request.response_time_ms,
            "success": request.success,
            "checked_at": request.checked_at.isoformat(),
        },
    }
    manager.broadcast(message)
    return {"status": "ok"}
