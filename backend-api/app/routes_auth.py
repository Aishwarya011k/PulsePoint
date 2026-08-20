"""Authentication routes."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import create_access_token, hash_password, verify_password
from app.database import get_db
from app.models import User
from app.schemas import TokenResponse, UserLoginRequest, UserRegisterRequest

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(
    request: UserRegisterRequest,
    db: Annotated[Session, Depends(get_db)],
):
    """
    Register a new user and return an access token.

    Args:
        request: User registration details
        db: Database session

    Returns:
        Access token for the new user

    Raises:
        HTTPException: If user already exists
    """
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    hashed_password_value = hash_password(request.password)
    new_user = User(email=request.email, hashed_password=hashed_password_value)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    access_token = create_access_token(data={"sub": str(new_user.id)})
    return TokenResponse(access_token=access_token)


@router.post("/login", response_model=TokenResponse)
def login(
    request: UserLoginRequest,
    db: Annotated[Session, Depends(get_db)],
):
    """
    Authenticate a user and return an access token.

    Args:
        request: User login details
        db: Database session

    Returns:
        Access token for the authenticated user

    Raises:
        HTTPException: If credentials are invalid
    """
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(access_token=access_token)
