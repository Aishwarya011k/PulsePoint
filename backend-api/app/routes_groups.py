"""Target group management routes."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.cache import cache_delete, cache_delete_pattern
from app.database import get_db
from app.dependencies import get_current_user
from app.models import Group, User
from app.schemas import GroupCreateRequest, GroupResponse, GroupUpdateRequest

router = APIRouter(prefix="/groups", tags=["groups"])


def get_owned_group(group_id: int, db: Session, user: User) -> Group:
    group = db.query(Group).filter(Group.id == group_id, Group.user_id == user.id).first()
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    return group


@router.post("", response_model=GroupResponse)
def create_group(
    request: GroupCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    group = Group(user_id=current_user.id, name=request.name, color=request.color)
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


@router.get("", response_model=list[GroupResponse])
def list_groups(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return db.query(Group).filter(Group.user_id == current_user.id).order_by(Group.created_at).all()


@router.patch("/{group_id}", response_model=GroupResponse)
def update_group(
    group_id: int,
    request: GroupUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    group = get_owned_group(group_id, db, current_user)
    if request.name is not None:
        group.name = request.name
    if request.color is not None:
        group.color = request.color
    db.commit()
    db.refresh(group)
    cache_delete(f"targets:user:{current_user.id}")
    cache_delete_pattern(f"target:*:user:{current_user.id}")
    return group


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(
    group_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    group = get_owned_group(group_id, db, current_user)
    for target in group.targets:
        target.group_id = None
    db.delete(group)
    db.commit()
    cache_delete(f"targets:user:{current_user.id}")
    cache_delete_pattern(f"target:*:user:{current_user.id}")
