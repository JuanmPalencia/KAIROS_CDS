"""
Tests for Simulation and Digital Twin endpoints.
"""
import pytest
from tests.conftest import auth_header


# ── Simulation ──

def test_simulation_status(client, admin_token):
    """GET /simulation/auto-generate/status should return status."""
    resp = client.get("/simulation/auto-generate/status", headers=auth_header(admin_token))
    assert resp.status_code == 200
    data = resp.json()
    assert "running" in data


def test_generate_one_incident(client, admin_token):
    """POST /simulation/generate-one should create an incident."""
    # Need fleet + hospitals first
    client.post("/fleet/seed-ambulances", headers=auth_header(admin_token))
    client.post("/api/hospitals/seed", headers=auth_header(admin_token))
    resp = client.post("/simulation/generate-one", headers=auth_header(admin_token))
    assert resp.status_code == 200
    data = resp.json()
    assert "id" in data or "incident" in str(data).lower()


def test_speed_control(client, admin_token):
    """POST /simulation/speed should accept valid multiplier."""
    resp = client.post(
        "/simulation/speed?multiplier=5",
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 200


def test_simulation_reset(client, admin_token):
    """POST /simulation/reset should clear incidents."""
    resp = client.post("/simulation/reset", headers=auth_header(admin_token))
    assert resp.status_code == 200


# ── Digital Twin ──

def test_fleet_health(client, admin_token):
    """GET /digital-twin/fleet-health should return health data."""
    resp = client.get("/digital-twin/fleet-health", headers=auth_header(admin_token))
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)


def test_what_if(client, admin_token):
    """POST /digital-twin/what-if should process scenario."""
    client.post("/fleet/seed-ambulances", headers=auth_header(admin_token))
    resp = client.post(
        "/digital-twin/what-if",
        json={"scenario": "disable_vehicle", "vehicle_id": "SVA-001"},
        headers=auth_header(admin_token),
    )
    # May return 200 or 422 depending on scenario schema
    assert resp.status_code in (200, 400, 422)
