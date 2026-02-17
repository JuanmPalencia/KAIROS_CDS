"""Servicio asíncrono de notarización blockchain para audit logs.

Se ejecuta como background task de FastAPI: después de guardar el
audit log en PostgreSQL, calcula el hash inmediatamente y registra
en BSV de forma asíncrona sin bloquear la respuesta HTTP.
"""

from __future__ import annotations

import logging
from typing import Any

from .integrity import build_audit_payload, compute_hash, build_evidence_record
from .adapter import get_blockchain_adapter

logger = logging.getLogger(__name__)

# Instancia singleton del adapter (reutilizable)
_adapter = None


def _get_adapter():
    global _adapter
    if _adapter is None:
        _adapter = get_blockchain_adapter()
    return _adapter


def compute_audit_hash(
    audit_id: int,
    timestamp: str,
    user_id: int | None,
    username: str | None,
    action: str,
    resource: str | None,
    resource_id: str | None,
    details: str | None,
    ip_address: str | None,
) -> str:
    """Calcula el hash SHA-256 de un registro de auditoría.

    Se llama de forma síncrona inmediatamente después de crear el
    audit log en PostgreSQL, antes de devolver la respuesta HTTP.
    """
    payload = build_audit_payload(
        audit_id=audit_id,
        timestamp=timestamp,
        user_id=user_id,
        username=username,
        action=action,
        resource=resource,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address,
    )
    return compute_hash(payload)


def register_on_blockchain(
    audit_id: int,
    timestamp: str,
    user_id: int | None,
    username: str | None,
    action: str,
    resource: str | None,
    resource_id: str | None,
    details: str | None,
    ip_address: str | None,
    blockchain_hash: str,
) -> dict[str, Any]:
    """Registra un audit log en BSV blockchain.

    Se ejecuta como background task. Actualiza la DB con el tx_id
    una vez la transacción es confirmada.
    """
    adapter = _get_adapter()

    payload = build_audit_payload(
        audit_id=audit_id,
        timestamp=timestamp,
        user_id=user_id,
        username=username,
        action=action,
        resource=resource,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address,
    )

    evidence = build_evidence_record(payload)
    result = adapter.register(evidence)

    logger.info(
        "[NOTARIZE] Audit #%d (%s) → %s [tx: %s]",
        audit_id, action, result.get("status"), result.get("tx_id", "none"),
    )

    return result


def verify_audit_hash(analysis_hash: str) -> dict[str, Any] | None:
    """Verifica un hash de auditoría contra el registro blockchain."""
    adapter = _get_adapter()
    return adapter.verify(analysis_hash)


def list_blockchain_records(limit: int = 50) -> list[dict[str, Any]]:
    """Lista los registros de blockchain más recientes."""
    adapter = _get_adapter()
    return adapter.list_records(limit=limit)
