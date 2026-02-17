"""Servicio de notarización por batch usando Merkle Tree.

Flujo:
1. Acumula audit logs que tienen blockchain_hash pero no están en ningún batch
2. Construye un Merkle Tree con todos los hashes pendientes
3. Sube 1 sola TX a BSV con el merkle_root como OP_RETURN
4. Guarda el batch en DB y enlaza cada audit log a ese batch
5. Cada audit log queda verificable individualmente con su Merkle Proof

Coste: ~$0.01-0.03 por batch (sin importar cuántos logs contenga)
→ 1000 logs/día = 1 TX/día = $0.01/día vs $10-30/día con TX individuales
"""

from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy.orm import Session

from .merkle import build_merkle_tree, get_merkle_proof, verify_merkle_proof
from .adapter import get_blockchain_adapter
from ..storage.models_sql import AuditLog, MerkleBatch

logger = logging.getLogger(__name__)

# ── Prefix para identificar Merkle Root TXs en blockchain ────────────
MERKLE_OP_PREFIX = "KAIROS_MERKLE"


def get_pending_hashes(db: Session) -> list[dict[str, Any]]:
    """Obtiene audit logs con hash pero sin batch asignado."""
    entries = (
        db.query(AuditLog)
        .filter(
            AuditLog.blockchain_hash.isnot(None),
            AuditLog.merkle_batch_id.is_(None),
        )
        .order_by(AuditLog.id)
        .all()
    )
    return [
        {"id": e.id, "hash": e.blockchain_hash, "action": e.action}
        for e in entries
    ]


def create_merkle_batch(db: Session) -> dict[str, Any]:
    """Crea un batch Merkle con todos los audit logs pendientes.

    Construye el Merkle Tree, guarda el batch en DB, y enlaza
    cada audit log al batch. NO sube a blockchain todavía.

    Returns:
        Info del batch creado, o error si no hay logs pendientes.
    """
    pending = get_pending_hashes(db)

    if not pending:
        return {"status": "empty", "message": "No pending audit logs to batch"}

    leaf_hashes = [p["hash"] for p in pending]
    audit_ids = [p["id"] for p in pending]

    # Construir Merkle Tree
    tree = build_merkle_tree(leaf_hashes)

    # Guardar batch en DB
    batch = MerkleBatch(
        merkle_root=tree["root"],
        leaf_count=tree["leaf_count"],
        leaf_hashes=json.dumps(leaf_hashes),
        merkle_tree_json=json.dumps(tree["levels"]),
        status="PENDING",
    )
    db.add(batch)
    db.flush()  # Obtener el ID antes del commit

    # Enlazar cada audit log al batch
    db.query(AuditLog).filter(AuditLog.id.in_(audit_ids)).update(
        {AuditLog.merkle_batch_id: batch.id},
        synchronize_session="fetch",
    )
    db.commit()
    db.refresh(batch)

    logger.info(
        "[MERKLE] Created batch #%d: %d leaves, root=%s",
        batch.id, batch.leaf_count, batch.merkle_root[:16],
    )

    return {
        "status": "created",
        "batch_id": batch.id,
        "merkle_root": batch.merkle_root,
        "leaf_count": batch.leaf_count,
        "audit_ids": audit_ids,
    }


def broadcast_merkle_batch(db: Session, batch_id: int) -> dict[str, Any]:
    """Sube el Merkle Root de un batch a BSV en una sola transacción.

    1 TX con OP_RETURN = todo el batch certificado.
    """
    batch = db.query(MerkleBatch).filter(MerkleBatch.id == batch_id).first()
    if not batch:
        return {"status": "error", "message": "Batch not found"}

    if batch.status == "ON_CHAIN":
        return {
            "status": "already_on_chain",
            "tx_id": batch.tx_id,
            "explorer_url": batch.explorer_url,
        }

    adapter = get_blockchain_adapter()

    # Registramos el merkle_root como si fuera un evidence record
    evidence = {
        "analysis_hash": batch.merkle_root,
        "audit_id": f"merkle_batch_{batch.id}",
        "timestamp_utc": batch.created_at.isoformat() if batch.created_at else "",
        "username": "system",
        "action": MERKLE_OP_PREFIX,
        "resource": "MERKLE_BATCH",
        "resource_id": str(batch.id),
    }

    result = adapter.register(evidence)
    tx_id = result.get("tx_id", "")

    if result.get("status") == "on_chain":
        batch.tx_id = tx_id
        batch.status = "ON_CHAIN"
        batch.network = result.get("network", "main")
        batch.explorer_url = result.get("explorer_url")

        # Actualizar todos los audit logs del batch con el tx_id
        db.query(AuditLog).filter(AuditLog.merkle_batch_id == batch.id).update(
            {AuditLog.blockchain_tx_id: tx_id},
            synchronize_session="fetch",
        )
        db.commit()

        logger.info(
            "[MERKLE] Batch #%d broadcast OK: %d logs → tx %s",
            batch.id, batch.leaf_count, tx_id,
        )
    else:
        batch.status = "FAILED"
        db.commit()
        logger.warning(
            "[MERKLE] Batch #%d broadcast failed: %s",
            batch.id, result.get("warning", result.get("error", "unknown")),
        )

    return {
        "status": batch.status.lower(),
        "batch_id": batch.id,
        "tx_id": batch.tx_id,
        "explorer_url": batch.explorer_url,
        "leaf_count": batch.leaf_count,
        "broadcast_result": result.get("status"),
    }


def create_and_broadcast_batch(db: Session) -> dict[str, Any]:
    """Shortcut: crea un batch y lo sube a BSV en un solo paso."""
    batch_result = create_merkle_batch(db)

    if batch_result.get("status") != "created":
        return batch_result

    return broadcast_merkle_batch(db, batch_result["batch_id"])


def get_merkle_proof_for_audit(db: Session, audit_id: int) -> dict[str, Any]:
    """Genera el Merkle Proof para un audit log específico.

    Con este proof, cualquiera puede verificar que el audit log
    está incluido en el batch sin necesidad de todos los demás logs.
    """
    entry = db.query(AuditLog).filter(AuditLog.id == audit_id).first()
    if not entry:
        return {"error": "Audit log not found"}

    if not entry.blockchain_hash:
        return {"error": "Audit log has no hash"}

    if not entry.merkle_batch_id:
        return {"error": "Audit log not in any Merkle batch yet"}

    batch = db.query(MerkleBatch).filter(MerkleBatch.id == entry.merkle_batch_id).first()
    if not batch:
        return {"error": "Merkle batch not found"}

    # Reconstruir el árbol desde los niveles guardados
    tree = {
        "root": batch.merkle_root,
        "leaves": json.loads(batch.leaf_hashes),
        "leaf_count": batch.leaf_count,
        "levels": json.loads(batch.merkle_tree_json) if batch.merkle_tree_json else [],
    }

    proof = get_merkle_proof(entry.blockchain_hash, tree)
    if proof is None:
        return {"error": "Hash not found in Merkle tree (data inconsistency)"}

    return {
        "audit_id": entry.id,
        "audit_hash": entry.blockchain_hash,
        "merkle_root": batch.merkle_root,
        "batch_id": batch.id,
        "batch_status": batch.status,
        "tx_id": batch.tx_id,
        "explorer_url": batch.explorer_url,
        "leaf_count": batch.leaf_count,
        "proof": proof,
        "proof_steps": len(proof),
        "verification_command": (
            f"Recalcular hash desde leaf aplicando {len(proof)} pasos "
            f"→ debe coincidir con merkle_root: {batch.merkle_root[:16]}..."
        ),
    }


def verify_audit_in_batch(db: Session, audit_id: int) -> dict[str, Any]:
    """Verificación completa: recalcula el proof y lo valida contra la raíz."""
    proof_data = get_merkle_proof_for_audit(db, audit_id)

    if "error" in proof_data:
        return proof_data

    # Verificar el proof criptográficamente
    is_valid = verify_merkle_proof(
        leaf_hash=proof_data["audit_hash"],
        proof=proof_data["proof"],
        expected_root=proof_data["merkle_root"],
    )

    return {
        **proof_data,
        "verified": is_valid,
        "integrity": "VALID" if is_valid else "TAMPERED",
        "on_chain": proof_data["batch_status"] == "ON_CHAIN",
    }


def list_batches(db: Session, limit: int = 20) -> list[dict[str, Any]]:
    """Lista los Merkle batches más recientes."""
    batches = (
        db.query(MerkleBatch)
        .order_by(MerkleBatch.id.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": b.id,
            "created_at": b.created_at.isoformat() if b.created_at else None,
            "merkle_root": b.merkle_root,
            "leaf_count": b.leaf_count,
            "status": b.status,
            "tx_id": b.tx_id,
            "explorer_url": b.explorer_url,
        }
        for b in batches
    ]
