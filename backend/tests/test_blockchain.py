"""
Tests for Blockchain / Audit immutability endpoints.
"""
import pytest
from tests.conftest import auth_header


def test_blockchain_status(client, admin_token):
    """GET /api/blockchain/status should return blockchain info."""
    resp = client.get("/api/blockchain/status", headers=auth_header(admin_token))
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)


def test_blockchain_records(client, admin_token):
    """GET /api/blockchain/records should return audit records."""
    resp = client.get("/api/blockchain/records", headers=auth_header(admin_token))
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, (list, dict))


def test_merkle_pending(client, admin_token):
    """GET /api/blockchain/merkle/pending should return pending logs."""
    resp = client.get("/api/blockchain/merkle/pending", headers=auth_header(admin_token))
    assert resp.status_code == 200


def test_merkle_batches(client, admin_token):
    """GET /api/blockchain/merkle/batches should return batch list."""
    resp = client.get("/api/blockchain/merkle/batches", headers=auth_header(admin_token))
    assert resp.status_code == 200


def test_verify_nonexistent(client, admin_token):
    """GET /api/blockchain/verify/{hash} with fake hash."""
    resp = client.get(
        "/api/blockchain/verify/0000000000000000000000000000000000000000000000000000000000000000",
        headers=auth_header(admin_token),
    )
    # Should return 200 with verification result or 404
    assert resp.status_code in (200, 404)


def test_audit_logs(client, admin_token):
    """GET /api/audit/logs should return paginated logs."""
    resp = client.get("/api/audit/logs", headers=auth_header(admin_token))
    assert resp.status_code == 200
    data = resp.json()
    assert "logs" in data or isinstance(data, list)
