"""Authentication routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from app.database import get_db
from app.models import User
from app.schemas import UserRegisterRequest, UserLoginRequest, TokenResponse
from app.auth import hash_password, verify_password, create_access_token
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(request: UserRegisterRequest, db: Session = Depends(get_db)):
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
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Create new user
    hashed_password = hash_password(request.password)
    new_user = User(email=request.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Generate token
    access_token = create_access_token(data={"sub": str(new_user.id)})
    
    return TokenResponse(access_token=access_token)


@router.post("/login", response_model=TokenResponse)
def login(request: UserLoginRequest, db: Session = Depends(get_db)):
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
    # Find user by email
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    
    # Generate token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return TokenResponse(access_token=access_token)
