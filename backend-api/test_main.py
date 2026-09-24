"""Tests for the Backend API."""

import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("INTERNAL_API_TOKEN", "test-token")

import pytest
from app.auth import hash_password
from app.database import Base, get_db
from app.main import app
from app.models import Group, Target, User
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    """Override database dependency for tests."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture
def test_db():
    """Provide a clean test database per test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(test_db):
    """Create a test user."""
    user = User(
        email="test@example.com",
        hashed_password=hash_password("testpassword123"),
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


def test_register():
    """Test user registration."""
    response = client.post(
        "/auth/register",
        json={"email": "newuser@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_register_duplicate_email():
    """Test registration with duplicate email."""
    client.post(
        "/auth/register",
        json={"email": "duplicate@example.com", "password": "password123"},
    )

    response = client.post(
        "/auth/register",
        json={"email": "duplicate@example.com", "password": "password456"},
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_login():
    """Test user login."""
    client.post(
        "/auth/register",
        json={"email": "login@example.com", "password": "password123"},
    )

    response = client.post(
        "/auth/login",
        json={"email": "login@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials():
    """Test login with invalid credentials."""
    response = client.post(
        "/auth/login",
        json={"email": "nonexistent@example.com", "password": "wrong"},
    )
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]


def test_create_target():
    """Test creating a target."""
    reg_response = client.post(
        "/auth/register",
        json={"email": "target@example.com", "password": "password123"},
    )
    token = reg_response.json()["access_token"]

    response = client.post(
        "/targets",
        json={
            "name": "Example API",
            "url": "https://api.example.com/health",
            "check_interval_seconds": 300,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Example API"
    assert data["url"] == "https://api.example.com/health"


def test_list_targets():
    """Test listing targets."""
    reg_response = client.post(
        "/auth/register",
        json={"email": "listuser@example.com", "password": "password123"},
    )
    token = reg_response.json()["access_token"]

    for i in range(2):
        client.post(
            "/targets",
            json={
                "name": f"Target {i}",
                "url": f"https://example{i}.com",
                "check_interval_seconds": 300,
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    response = client.get(
        "/targets",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Target 0"


def test_delete_target():
    """Test deleting a target."""
    reg_response = client.post(
        "/auth/register",
        json={"email": "deleteuser@example.com", "password": "password123"},
    )
    token = reg_response.json()["access_token"]

    create_response = client.post(
        "/targets",
        json={
            "name": "To Delete",
            "url": "https://delete.example.com",
            "check_interval_seconds": 300,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    target_id = create_response.json()["id"]

    response = client.delete(
        f"/targets/{target_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204

    get_response = client.get(
        f"/targets/{target_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_response.status_code == 404


def test_unauthorized_access():
    """Test accessing endpoints without authentication."""
    response = client.get("/targets")
    assert response.status_code == 403


def test_group_targets_and_delete_group_ungroups_targets():
    """Groups can be assigned to targets and deleted without deleting targets."""
    token = client.post(
        "/auth/register",
        json={"email": "groups@example.com", "password": "password123"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    group = client.post("/groups", json={"name": "Production", "color": "#22c55e"}, headers=headers)
    assert group.status_code == 200
    group_id = group.json()["id"]
    target = client.post(
        "/targets",
        json={"name": "API", "url": "https://example.com", "group_id": group_id},
        headers=headers,
    )
    assert target.status_code == 200
    target_id = target.json()["id"]
    assert target.json()["group_id"] == group_id

    assert client.delete(f"/groups/{group_id}", headers=headers).status_code == 204
    target_after_delete = client.get(f"/targets/{target_id}", headers=headers)
    assert target_after_delete.status_code == 200
    assert target_after_delete.json()["group_id"] is None


def test_postmortem_requires_resolved_incident(test_db, test_user):
    """Open incidents cannot receive postmortem notes."""
    target = Target(user_id=test_user.id, name="API", url="https://example.com")
    test_db.add(target)
    test_db.commit()
    test_db.refresh(target)
    token = client.post(
        "/auth/login",
        json={"email": test_user.email, "password": "testpassword123"},
    ).json()["access_token"]

    from app.models import Incident, IncidentStatus
    incident = Incident(target_id=target.id, status=IncidentStatus.OPEN)
    test_db.add(incident)
    test_db.commit()
    test_db.refresh(incident)
    response = client.patch(
        f"/incidents/{incident.id}/postmortem",
        json={"note": "Investigation notes"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
