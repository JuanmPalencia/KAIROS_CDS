"""Tests for the Live API and Audit Log endpoints."""
from tests.conftest import auth_header


class TestLiveEndpoint:
    """Tests for GET /api/live."""

    def test_live_data_returns_structure(self, client):
        response = client.get("/api/live")
        assert response.status_code == 200
        data = response.json()
        assert "vehicles" in data
        assert "incidents" in data
        assert "fleet_metrics" in data
        assert isinstance(data["vehicles"], list)
        assert isinstance(data["incidents"], list)


class TestAuditLog:
    """Tests for GET /api/audit/logs and /api/audit/export/csv."""

    def test_audit_logs_admin(self, client, admin_token):
        response = client.get(
            "/api/audit/logs",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert "logs" in data
        assert "total" in data

    def test_audit_logs_operator_forbidden(self, client, operator_token):
        response = client.get(
            "/api/audit/logs",
            headers=auth_header(operator_token),
        )
        assert response.status_code == 403

    def test_audit_export_csv(self, client, admin_token):
        response = client.get(
            "/api/audit/export/csv",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")
