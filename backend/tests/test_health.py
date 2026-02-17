"""Tests for the Health endpoint."""


def test_health_check(client):
    """GET /health should return 200 with ok: True."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
