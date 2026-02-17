"""
Tests for Crew Management endpoints.
"""
import pytest
from tests.conftest import auth_header


def test_seed_crew(client, admin_token):
    """POST /api/crews/seed should create crew members."""
    resp = client.post("/api/crews/seed", headers=auth_header(admin_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["crew_created"] > 0


def test_list_members(client, admin_token):
    """GET /api/crews/members should return crew list."""
    # Seed first
    client.post("/api/crews/seed", headers=auth_header(admin_token))
    resp = client.get("/api/crews/members", headers=auth_header(admin_token))
    assert resp.status_code == 200
    members = resp.json()
    assert isinstance(members, list)
    assert len(members) > 0
    # Check expected fields
    m = members[0]
    assert "id" in m
    assert "name" in m
    assert "role" in m


def test_list_shifts(client, admin_token):
    """GET /api/crews/shifts should return shifts."""
    # Seed vehicles first (shifts depend on existing vehicles)
    client.post("/fleet/seed-ambulances")
    client.post("/api/crews/seed", headers=auth_header(admin_token))
    resp = client.get("/api/crews/shifts", headers=auth_header(admin_token))
    assert resp.status_code == 200
    shifts = resp.json()
    assert isinstance(shifts, list)
    assert len(shifts) > 0
    s = shifts[0]
    assert s["shift_type"] in ("DIA", "NOCHE", "GUARDIA_24H")
    assert s["status"] in ("ACTIVE", "SCHEDULED", "COMPLETED", "CANCELLED")


def test_end_shift(client, admin_token):
    """POST /api/crews/shifts/{id}/end should finalize a shift."""
    client.post("/api/crews/seed", headers=auth_header(admin_token))
    shifts = client.get("/api/crews/shifts", headers=auth_header(admin_token)).json()
    active_shifts = [s for s in shifts if s["status"] == "ACTIVE"]
    if active_shifts:
        sid = active_shifts[0]["id"]
        resp = client.post(f"/api/crews/shifts/{sid}/end", headers=auth_header(admin_token))
        assert resp.status_code == 200
        assert resp.json()["status"] == "COMPLETED"


def test_get_member_detail(client, admin_token):
    """GET /api/crews/members/{id} should return member details."""
    client.post("/api/crews/seed", headers=auth_header(admin_token))
    members = client.get("/api/crews/members", headers=auth_header(admin_token)).json()
    mid = members[0]["id"]
    resp = client.get(f"/api/crews/members/{mid}", headers=auth_header(admin_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == mid
