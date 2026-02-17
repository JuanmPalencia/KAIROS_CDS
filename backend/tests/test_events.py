"""Tests for the Events (Incidents) API endpoints."""
from tests.conftest import auth_header


class TestCreateIncident:
    """Tests for POST /events/incidents."""

    def test_create_incident(self, client):
        response = client.post(
            "/events/incidents",
            json={
                "lat": 40.4168,
                "lon": -3.7038,
                "severity": 3,
                "incident_type": "CARDIO",
                "description": "Test cardiac incident",
                "address": "Calle de Alcalá 1",
                "city": "Madrid",
                "province": "Madrid",
                "affected_count": 2,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "incident_id" in data
        assert data["incident"]["severity"] == 3
        assert data["incident"]["incident_type"] == "CARDIO"

    def test_create_incident_no_auth(self, client):
        """Create incident is a public endpoint (no auth required)."""
        response = client.post(
            "/events/incidents",
            json={
                "lat": 40.4168,
                "lon": -3.7038,
                "severity": 1,
            },
        )
        assert response.status_code == 200


class TestGetIncidents:
    """Tests for GET /events/incidents."""

    def test_get_incidents_empty(self, client):
        response = client.get("/events/incidents")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_incidents_after_create(self, client):
        # Create an incident first
        client.post(
            "/events/incidents",
            json={
                "lat": 40.42,
                "lon": -3.70,
                "severity": 4,
                "incident_type": "TRAUMA",
            },
        )

        response = client.get("/events/incidents")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["incident_type"] == "TRAUMA"


class TestIncidentTimeline:
    """Tests for GET /events/incidents/{id}/timeline."""

    def test_timeline_for_created_incident(self, client):
        # Create an incident
        create_res = client.post(
            "/events/incidents",
            json={
                "lat": 40.4168,
                "lon": -3.7038,
                "severity": 2,
                "incident_type": "GENERAL",
            },
        )
        incident_id = create_res.json()["incident_id"]

        response = client.get(f"/events/incidents/{incident_id}/timeline")
        assert response.status_code == 200
        data = response.json()
        assert "timeline" in data
        assert isinstance(data["timeline"], list)
        # Should have at least a CREATED event
        assert any(evt.get("event") == "CREATED" or "Creado" in evt.get("label", "") for evt in data["timeline"])
