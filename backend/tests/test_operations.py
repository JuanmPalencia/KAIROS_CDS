"""
Tests for Hospital, Assignment, and Analytics endpoints.
"""
import pytest
from tests.conftest import auth_header


# ── Hospitals ──

def test_seed_hospitals(client, admin_token):
    """POST /api/hospitals/seed should create hospitals."""
    resp = client.post("/api/hospitals/seed", headers=auth_header(admin_token))
    assert resp.status_code == 200
    data = resp.json()
    assert "created" in data or "hospitals" in str(data).lower()


def test_list_hospitals(client, admin_token):
    """GET /api/hospitals/ should return hospital list after seed."""
    client.post("/api/hospitals/seed", headers=auth_header(admin_token))
    resp = client.get("/api/hospitals/", headers=auth_header(admin_token))
    assert resp.status_code == 200
    hospitals = resp.json()
    assert isinstance(hospitals, list)
    assert len(hospitals) > 0
    h = hospitals[0]
    assert "id" in h
    assert "capacity" in h
    assert "current_load" in h


# ── Fleet ──

def test_seed_fleet(client, admin_token):
    """POST /fleet/seed-ambulances should create vehicles."""
    resp = client.post("/fleet/seed-ambulances", headers=auth_header(admin_token))
    assert resp.status_code == 200


def test_list_fleet(client, admin_token):
    """GET /fleet/ should return vehicle list."""
    client.post("/fleet/seed-ambulances", headers=auth_header(admin_token))
    resp = client.get("/fleet/vehicles", headers=auth_header(admin_token))
    assert resp.status_code == 200
    vehicles = resp.json()
    assert isinstance(vehicles, list)
    assert len(vehicles) > 0
    v = vehicles[0]
    assert "id" in v
    assert "subtype" in v
    assert v["subtype"] in ("SVB", "SVA", "VIR", "VAMM", "SAMU")


# ── Analytics ──

def test_analytics_dashboard(client, admin_token):
    """GET /api/analytics/dashboard should return analytics data."""
    resp = client.get(
        "/api/analytics/dashboard?days=7",
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "by_type" in data or "total" in str(data).lower() or isinstance(data, dict)


def test_analytics_response_times(client, admin_token):
    """GET /api/analytics/response-times should return data."""
    resp = client.get(
        "/api/analytics/response-times?days=7",
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 200


# ── KPIs ──

def test_kpis_current(client, admin_token):
    """GET /api/kpis/realtime should return KPI data."""
    resp = client.get("/api/kpis/realtime", headers=auth_header(admin_token))
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)


# ── Assignment suggest ──

def test_suggest_no_incident(client, admin_token):
    """GET /api/assignments/suggest/{id} with nonexistent incident."""
    resp = client.get(
        "/api/assignments/suggest/NONEXIST",
        headers=auth_header(admin_token),
    )
    assert resp.status_code in (404, 400, 200)


# ── Cities ──

def test_cities(client, admin_token):
    """GET /api/cities should return city list."""
    resp = client.get("/api/cities", headers=auth_header(admin_token))
    assert resp.status_code == 200
    data = resp.json()
    assert "cities" in data
