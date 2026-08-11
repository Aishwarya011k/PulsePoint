"""Tests for the Backend API."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.models import User
from app.auth import hash_password

# Use in-memory SQLite for tests
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
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
    """Provide a test database."""
    Base.metadata.create_all(bind=engine)
    yield TestingSessionLocal()
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
    # Register first user
    client.post(
        "/auth/register",
        json={"email": "duplicate@example.com", "password": "password123"},
    )
    
    # Try to register with same email
    response = client.post(
        "/auth/register",
        json={"email": "duplicate@example.com", "password": "password456"},
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_login():
    """Test user login."""
    # Register first
    client.post(
        "/auth/register",
        json={"email": "login@example.com", "password": "password123"},
    )
    
    # Then login
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
    # Register and login
    reg_response = client.post(
        "/auth/register",
        json={"email": "target@example.com", "password": "password123"},
    )
    token = reg_response.json()["access_token"]
    
    # Create target
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
    # Register and login
    reg_response = client.post(
        "/auth/register",
        json={"email": "listuser@example.com", "password": "password123"},
    )
    token = reg_response.json()["access_token"]
    
    # Create two targets
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
    
    # List targets
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
    # Register and login
    reg_response = client.post(
        "/auth/register",
        json={"email": "deleteuser@example.com", "password": "password123"},
    )
    token = reg_response.json()["access_token"]
    
    # Create target
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
    
    # Delete target
    response = client.delete(
        f"/targets/{target_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204
    
    # Verify it's deleted
    get_response = client.get(
        f"/targets/{target_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_response.status_code == 404


def test_unauthorized_access():
    """Test accessing endpoints without authentication."""
    response = client.get("/targets")
    assert response.status_code == 403
