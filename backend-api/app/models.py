"""SQLAlchemy models for the application."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class User(Base):
    """User model for authentication."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    targets = relationship("Target", back_populates="user", cascade="all, delete-orphan")


class Target(Base):
    """Target model for monitored URLs/APIs."""
    __tablename__ = "targets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    url = Column(String(2048), nullable=False)
    check_interval_seconds = Column(Integer, default=300, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="targets")
    checks = relationship("Check", back_populates="target", cascade="all, delete-orphan")
    incidents = relationship("Incident", back_populates="target", cascade="all, delete-orphan")


class Check(Base):
    """Health check result model."""
    __tablename__ = "checks"
    
    id = Column(Integer, primary_key=True, index=True)
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=False)
    status_code = Column(Integer, nullable=False)
    response_time_ms = Column(Float, nullable=False)
    success = Column(Boolean, nullable=False)
    checked_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    target = relationship("Target", back_populates="checks")


class IncidentStatus(str, enum.Enum):
    """Enum for incident status."""
    OPEN = "open"
    RESOLVED = "resolved"


class Incident(Base):
    """Incident model for tracking outages."""
    __tablename__ = "incidents"
    
    id = Column(Integer, primary_key=True, index=True)
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=False)
    status = Column(Enum(IncidentStatus), default=IncidentStatus.OPEN, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    summary = Column(Text, nullable=True)  # Reserved for AI-generated explanation in Phase 8
    
    # Relationships
    target = relationship("Target", back_populates="incidents")
