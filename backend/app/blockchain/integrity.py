"""Hash determinístico y registro de evidencia para audit logs de KAIROS.

Portado desde Urban VS (NeuralHack 2026) y adaptado al dominio de
emergencias médicas. Genera hashes SHA-256 de registros de auditoría
para anclarlos de forma inmutable en BSV blockchain.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any


def canonical_json(data: dict[str, Any]) -> str:
    """Serializa dict a una cadena JSON canónica determinística.

    - Claves ordenadas recursivamente
    - Sin espacios en blanco (separadores compactos)
    - ensure_ascii para reproducibilidad multiplataforma
    """
    return json.dumps(
        data, sort_keys=True, separators=(",", ":"),
        ensure_ascii=True,
    )


def compute_hash(data: dict[str, Any]) -> str:
    """Hash SHA-256 de la representación JSON canónica.

    Normaliza los datos vía ida y vuelta JSON para asegurar que
    los tipos produzcan el mismo hash ya sea calculado desde el
    dict original o desde JSON re-parseado.
    """
    normalized = json.loads(canonical_json(data))
    canonical = json.dumps(
        normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_audit_payload(
    audit_id: int,
    timestamp: str,
    user_id: int | None,
    username: str | None,
    action: str,
    resource: str | None,
    resource_id: str | None,
    details: str | None,
    ip_address: str | None,
) -> dict[str, Any]:
    """Construye el payload canónico de un registro de auditoría (antes del hash).

    Solo incluye campos que definen la acción. No incluye campos derivados
    como blockchain_hash o blockchain_tx_id.
    """
    return {
        "audit_id": audit_id,
        "timestamp_utc": timestamp,
        "user_id": user_id,
        "username": username or "system",
        "action": action,
        "resource": resource,
        "resource_id": resource_id,
        "details": details,
        "ip_address": ip_address,
    }


def build_evidence_record(
    audit_payload: dict[str, Any],
) -> dict[str, Any]:
    """Construye el registro de evidencia para enviar a blockchain.

    Contiene el analysis_hash más metadatos para búsqueda.
    """
    analysis_hash = compute_hash(audit_payload)
    return {
        "analysis_hash": analysis_hash,
        "audit_id": audit_payload["audit_id"],
        "timestamp_utc": audit_payload["timestamp_utc"],
        "username": audit_payload["username"],
        "action": audit_payload["action"],
        "resource": audit_payload.get("resource"),
        "resource_id": audit_payload.get("resource_id"),
    }


def verify_integrity(audit_payload: dict[str, Any], expected_hash: str) -> bool:
    """Recalcula el hash y verifica que coincida con el almacenado."""
    return compute_hash(audit_payload) == expected_hash
