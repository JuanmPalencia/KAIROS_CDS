"""
Conftest for pytest - provides test fixtures for KAIROS backend testing.
Uses an in-memory SQLite database instead of PostgreSQL.
"""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Disable rate limiting for tests
os.environ["SECURITY_RATE_LIMIT_ENABLED"] = "false"

from app.storage.db import Base, get_db
from app.storage.models_sql import User
from app.auth.security import get_password_hash


# In-memory SQLite for tests
SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI test client with overridden database dependency."""
    # Import here to avoid circular imports and early engine creation
    from app.main import app

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user(db_session):
    """Create an admin user in the test database."""
    user = User(
        username="testadmin",
        email="admin@test.com",
        full_name="Test Admin",
        hashed_password=get_password_hash("admin123"),
        role="ADMIN",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def operator_user(db_session):
    """Create an operator user in the test database."""
    user = User(
        username="testoperator",
        email="operator@test.com",
        full_name="Test Operator",
        hashed_password=get_password_hash("operator123"),
        role="OPERATOR",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_token(client, admin_user):
    """Get a valid JWT token for the admin user."""
    response = client.post(
        "/api/auth/login",
        data={"username": "testadmin", "password": "admin123"},
    )
    return response.json()["access_token"]


@pytest.fixture
def operator_token(client, operator_user):
    """Get a valid JWT token for the operator user."""
    response = client.post(
        "/api/auth/login",
        data={"username": "testoperator", "password": "operator123"},
    )
    return response.json()["access_token"]


def auth_header(token: str) -> dict:
    """Helper to create Authorization header."""
    return {"Authorization": f"Bearer {token}"}
