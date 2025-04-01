# test_apikeys.py
import pytest
import secrets
import hashlib
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker, Session

# Import the FastAPI app instance from __init__.py
from ragnarok_server import app

# Import the Base and models from ragnarok_server/rdb
from ragnarok_server.rdb.base import Base
from ragnarok_server.rdb.user import User
from ragnarok_server.rdb.api_key import APIKey
from ragnarok_server.rdb.database import get_db


# Override the database with an in-memory SQLite for testing.
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool  # Ensure the same connection is reused
)
TestingSessionLocal = sessionmaker(bind=engine)

# Create all tables for the test database.
Base.metadata.create_all(bind=engine)


# Override the get_db dependency.
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


# Create a dummy test user and insert into test DB.
def create_test_user(db: Session) -> User:
    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="fakehash",
        is_active=True,
        tenant_id=1,
        is_tenant_admin=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# Override get_current_user dependency.
# Assume get_current_user is defined in ragnarok_server/toolkit/auth.py.
from ragnarok_server.auth import get_current_user


def override_get_current_user():
    db = next(override_get_db())
    user = db.query(User).filter_by(id=1).first()
    if not user:
        user = create_test_user(db)
    return user


app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)


def _hash_key(plaintext: str) -> str:
    """Helper function to compute SHA-256 hash."""
    return hashlib.sha256(plaintext.encode("utf-8")).hexdigest()


@pytest.fixture(autouse=True)
def run_around_tests():
    # Clear APIKey table before and after each test.
    db = next(override_get_db())
    db.query(APIKey).delete()
    db.commit()
    yield
    db.query(APIKey).delete()
    db.commit()


def test_create_api_key():
    """Test the API Key creation endpoint."""
    response = client.post("/api/keys", params={"remark": "Test key"})
    assert response.status_code == 200, response.text
    data = response.json()
    assert "id" in data
    assert "api_key" in data  # plaintext is returned only once
    assert data["remark"] == "Test key"
    # Verify that created_at is a valid ISO format timestamp.
    datetime.fromisoformat(data["created_at"])

    # Verify the API key record in the test database.
    db = next(override_get_db())
    key = db.query(APIKey).filter_by(id=data["id"]).first()
    assert key is not None
    # Ensure stored key_hash matches the hash of the returned plaintext.
    assert key.key_hash == _hash_key(data["api_key"])


def test_list_api_keys():
    """Test listing API keys."""
    # Create two API keys.
    client.post("/api/keys", params={"remark": "Key 1"})
    client.post("/api/keys", params={"remark": "Key 2"})
    response = client.get("/api/keys")
    assert response.status_code == 200, response.text
    data = response.json()
    # Expect two keys in the list.
    assert isinstance(data, list)
    assert len(data) == 2
    for key in data:
        assert "id" in key
        assert "remark" in key
        assert "enabled" in key
        assert "created_at" in key
        # The plaintext API key should not be returned.
        assert "api_key" not in key


def test_update_api_key():
    """Test updating an API key's enabled status and remark."""
    # Create an API key first.
    response = client.post("/api/keys", params={"remark": "Initial remark"})
    key_data = response.json()
    key_id = key_data["id"]

    # Update the API key: disable it and change the remark.
    response = client.patch(f"/api/keys/{key_id}/", json={"enabled": False, "remark": "Updated remark"})
    assert response.status_code == 200, response.text
    updated = response.json()
    assert updated["enabled"] is False
    assert updated["remark"] == "Updated remark"


def test_rotate_api_key():
    """Test rotating (renewing) an API key."""
    # Create an API key first.
    response = client.post("/api/keys", params={"remark": "Key to rotate"})
    key_data = response.json()
    key_id = key_data["id"]
    original_plaintext = key_data["api_key"]

    # Rotate the API key.
    response = client.post(f"/api/keys/{key_id}/rotate")
    assert response.status_code == 200, response.text
    rotated = response.json()
    # New plaintext should differ from the original.
    assert rotated["api_key"] != original_plaintext
    # The key ID should remain the same.
    assert rotated["id"] == key_id
    # The created_at timestamp should have been updated.
    assert rotated["created_at"] != key_data["created_at"]


def test_delete_api_key():
    """Test deleting an API key."""
    # Create an API key.
    response = client.post("/api/keys", params={"remark": "Key to delete"})
    key_data = response.json()
    key_id = key_data["id"]

    # Delete the API key.
    response = client.delete(f"/api/keys/{key_id}")
    assert response.status_code == 204, response.text

    # Verify that the key has been deleted.
    response = client.get("/api/keys")
    data = response.json()
    assert len(data) == 0
