"""Tests for general API endpoints — fleet, incidents, analytics, metrics."""
import pytest
from tests.conftest import auth_header


def test_root(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "service" in response.json()


def test_health_check(client):
    """Test health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_init_admin(client):
    """Test creating initial admin user"""
    response = client.post("/api/auth/init-admin")
    assert response.status_code == 200
    assert "users" in response.json()


def test_login(client):
    """Test login flow"""
    # Create admin first
    client.post("/api/auth/init-admin")
    
    # Try login
    response = client.post(
        "/api/auth/login",
        data={"username": "admin", "password": "admin123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_create_vehicle(client, admin_token):
    """Test creating a vehicle"""
    response = client.post(
        "/fleet/vehicles",
        json={
            "id": "TEST-001",
            "type": "AMB",
            "lat": 40.4168,
            "lon": -3.7038,
            "enabled": True
        },
        headers=auth_header(admin_token),
    )
    assert response.status_code == 200


def test_seed_ambulances(client):
    """Test seeding ambulances"""
    response = client.post("/fleet/seed-ambulances")
    assert response.status_code == 200
    assert len(response.json()["created"]) >= 1  # seeds from FLEET_SEED


def test_create_incident(client):
    """Test creating an incident"""
    response = client.post(
        "/events/incidents",
        json={
            "lat": 40.4168,
            "lon": -3.7038,
            "severity": 3,
            "incident_type": "CARDIO",
            "description": "Test incident"
        }
    )
    assert response.status_code == 200
    assert "incident_id" in response.json()


def test_list_incidents(client):
    """Test listing incidents"""
    # Create an incident first
    client.post(
        "/events/incidents",
        json={"lat": 40.4168, "lon": -3.7038, "severity": 3}
    )
    
    # List incidents
    response = client.get("/events/incidents")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_analytics_dashboard(client, admin_token):
    """Test analytics dashboard"""
    response = client.get(
        "/api/analytics/dashboard?days=7",
        headers=auth_header(admin_token),
    )
    assert response.status_code == 200
    assert "summary" in response.json()


def test_metrics_endpoint(client):
    """Test Prometheus metrics"""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text
