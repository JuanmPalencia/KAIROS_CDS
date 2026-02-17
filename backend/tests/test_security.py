"""
Tests for Security endpoints.
"""
import pytest
from tests.conftest import auth_header


def test_security_dashboard(client, admin_token):
    """GET /api/security/dashboard returns security stats."""
    resp = client.get("/api/security/dashboard", headers=auth_header(admin_token))
    assert resp.status_code == 200
    data = resp.json()
    assert "stats" in data
    assert "protections" in data
    assert "config" in data


def test_security_events(client, admin_token):
    """GET /api/security/events returns event list."""
    resp = client.get("/api/security/events", headers=auth_header(admin_token))
    assert resp.status_code == 200
    data = resp.json()
    assert "events" in data
    assert isinstance(data["events"], list)


def test_scan_input_clean(client, admin_token):
    """POST /api/security/scan-input should detect no threats in clean text."""
    resp = client.post(
        "/api/security/scan-input",
        json={"value": "Hello world, this is a normal message"},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["clean"] is True


def test_scan_input_sql_injection(client, admin_token):
    """POST /api/security/scan-input should detect SQL injection."""
    resp = client.post(
        "/api/security/scan-input",
        json={"value": "SELECT * FROM users WHERE 1=1; DROP TABLE users;--"},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["threats_found"] is True
    assert len(data["threats"]) > 0


def test_scan_input_xss(client, admin_token):
    """POST /api/security/scan-input should detect XSS."""
    resp = client.post(
        "/api/security/scan-input",
        json={"value": "<script>alert('xss')</script>"},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["threats_found"] is True


def test_check_password_weak(client, admin_token):
    """POST /api/security/check-password should rate a weak password."""
    resp = client.post(
        "/api/security/check-password",
        json={"password": "123"},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] is False


def test_check_password_strong(client, admin_token):
    """POST /api/security/check-password should accept a strong password."""
    resp = client.post(
        "/api/security/check-password",
        json={"password": "S3cureP@ssw0rd!2026"},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] is True


def test_csrf_token(client, admin_token):
    """GET /api/security/csrf-token should return a token."""
    resp = client.get("/api/security/csrf-token", headers=auth_header(admin_token))
    assert resp.status_code == 200
    data = resp.json()
    assert "csrf_token" in data
    assert len(data["csrf_token"]) > 10


def test_blocked_ips(client, admin_token):
    """GET /api/security/blocked-ips should return list."""
    resp = client.get("/api/security/blocked-ips", headers=auth_header(admin_token))
    assert resp.status_code == 200
    data = resp.json()
    assert "blocked_ips" in data


def test_sessions(client, admin_token):
    """GET /api/security/sessions should return active sessions."""
    resp = client.get("/api/security/sessions", headers=auth_header(admin_token))
    assert resp.status_code == 200
    data = resp.json()
    assert "sessions" in data


def test_security_requires_admin(client, operator_token):
    """Security endpoints should reject non-admin users."""
    resp = client.get("/api/security/dashboard", headers=auth_header(operator_token))
    assert resp.status_code in (403, 401)
