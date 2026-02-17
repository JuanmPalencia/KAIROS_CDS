"""Tests for the Authentication endpoints."""
from tests.conftest import auth_header


class TestLogin:
    """Tests for POST /api/auth/login."""

    def test_login_success(self, client, admin_user):
        response = client.post(
            "/api/auth/login",
            data={"username": "testadmin", "password": "admin123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "testadmin"
        assert data["user"]["role"] == "ADMIN"

    def test_login_wrong_password(self, client, admin_user):
        response = client.post(
            "/api/auth/login",
            data={"username": "testadmin", "password": "wrongpassword"},
        )
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        response = client.post(
            "/api/auth/login",
            data={"username": "ghost", "password": "nope"},
        )
        assert response.status_code == 401


class TestGetMe:
    """Tests for GET /api/auth/me."""

    def test_get_me_authenticated(self, client, admin_token):
        response = client.get("/api/auth/me", headers=auth_header(admin_token))
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testadmin"
        assert data["role"] == "ADMIN"

    def test_get_me_no_token(self, client):
        response = client.get("/api/auth/me")
        assert response.status_code in (401, 403)


class TestRegister:
    """Tests for POST /api/auth/register."""

    def test_register_user_as_admin(self, client, admin_token):
        response = client.post(
            "/api/auth/register",
            json={
                "username": "newviewer",
                "email": "viewer@test.com",
                "password": "Viewer123",
                "full_name": "New Viewer",
                "role": "VIEWER",
            },
            headers=auth_header(admin_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newviewer"
        assert data["role"] == "VIEWER"

    def test_register_duplicate_username(self, client, admin_user, admin_token):
        response = client.post(
            "/api/auth/register",
            json={
                "username": "testadmin",
                "email": "dup@test.com",
                "password": "Pass1234",
                "full_name": "Dup User",
                "role": "VIEWER",
            },
            headers=auth_header(admin_token),
        )
        assert response.status_code == 400

    def test_register_without_admin_role(self, client, operator_token):
        response = client.post(
            "/api/auth/register",
            json={
                "username": "unauthorized",
                "email": "unauth@test.com",
                "password": "Pass1234",
                "full_name": "Unauth",
                "role": "VIEWER",
            },
            headers=auth_header(operator_token),
        )
        assert response.status_code == 403


class TestInitAdmin:
    """Tests for POST /api/auth/init-admin."""

    def test_init_admin_on_empty_db(self, client):
        response = client.post("/api/auth/init-admin")
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert len(data["users"]) == 4  # admin, operator, doctor, viewer

    def test_init_admin_when_users_exist(self, client, admin_user):
        response = client.post("/api/auth/init-admin")
        assert response.status_code == 400
