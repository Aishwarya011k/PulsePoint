"""Database models for the checks consumer service."""
import enum
from datetime import datetime

from config import config
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker

engine = create_engine(
    config.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    """User model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Target(Base):
    """Monitored target model."""

    __tablename__ = "targets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    url = Column(String(2048), nullable=False)
    check_interval_seconds = Column(Integer, default=300, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Check(Base):
    """Persisted health check result."""

    __tablename__ = "checks"

    id = Column(Integer, primary_key=True, index=True)
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=False)
    status_code = Column(Integer, nullable=False)
    response_time_ms = Column(Float, nullable=False)
    success = Column(Boolean, nullable=False)
    checked_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class IncidentStatus(str, enum.Enum):
    """Incident status enum."""

    OPEN = "open"
    RESOLVED = "resolved"


class Incident(Base):
    """Recorded incident state."""

    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=False)
    status = Column(Enum(IncidentStatus), default=IncidentStatus.OPEN, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    summary = Column(Text, nullable=True)
