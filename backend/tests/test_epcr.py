"""
Tests for ePCR and Patient Tracking endpoints.
"""
import pytest
from tests.conftest import auth_header


def test_mpds_protocols(client, admin_token):
    """GET /api/epcr/mpds-protocols should return protocol list."""
    resp = client.get("/api/epcr/mpds-protocols", headers=auth_header(admin_token))
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, (list, dict))


def test_all_tracking(client, admin_token):
    """GET /api/epcr/all-tracking should return tracking list."""
    resp = client.get("/api/epcr/all-tracking", headers=auth_header(admin_token))
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


def test_all_tracking_full(client, admin_token):
    """GET /api/epcr/all-tracking-full should include discharged."""
    resp = client.get("/api/epcr/all-tracking-full", headers=auth_header(admin_token))
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


def test_seed_demo_patients(client, admin_token):
    """POST /api/epcr/seed-demo-patients should create demo data."""
    # Need fleet and hospitals first
    client.post("/fleet/seed-ambulances", headers=auth_header(admin_token))
    client.post("/api/hospitals/seed", headers=auth_header(admin_token))
    resp = client.post("/api/epcr/seed-demo-patients", headers=auth_header(admin_token))
    assert resp.status_code == 200


def test_tracking_nonexistent(client, admin_token):
    """GET /api/epcr/tracking/{id} for nonexistent incident."""
    resp = client.get(
        "/api/epcr/tracking/NONEXIST",
        headers=auth_header(admin_token),
    )
    assert resp.status_code in (200, 404)
