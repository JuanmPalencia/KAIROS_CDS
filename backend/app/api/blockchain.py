"""API endpoints de blockchain para verificación pública y administración.

- GET /api/blockchain/verify/{hash} → Público (sin auth), verifica un hash
- GET /api/blockchain/status → Admin, estado general del sistema blockchain
- GET /api/blockchain/records → Admin, lista registros recientes
"""

from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc
# typing: no unused imports

from ..storage.db import get_db
from ..storage.models_sql import AuditLog
from ..blockchain.notarizer import (
    verify_audit_hash,
    list_blockchain_records,
    register_on_blockchain,
)
from ..blockchain.batch_notarizer import (
    get_pending_hashes,
    create_merkle_batch,
    broadcast_merkle_batch,
    create_and_broadcast_batch,
    get_merkle_proof_for_audit,
    verify_audit_in_batch,
    list_batches,
)
from ..blockchain.integrity import build_audit_payload, compute_hash, verify_integrity
from ..auth.dependencies import get_current_user, require_role, User
from .. import config as app_config

router = APIRouter(prefix="/api/blockchain", tags=["blockchain"])


# ══════════════════════════════════════════════════════════════════════
# ENDPOINT PÚBLICO - Verificación de integridad (sin autenticación)
# ══════════════════════════════════════════════════════════════════════

@router.get("/verify/{hash}")
async def verify_hash(hash: str, db: Session = Depends(get_db)):
    """Verifica un hash de auditoría contra blockchain (PÚBLICO, sin auth).

    Cualquier persona puede verificar que un registro de auditoría
    no fue manipulado, proporcionando el hash SHA-256.

    Flujo:
    1. Busca el audit log en PostgreSQL por su blockchain_hash
    2. Recalcula el hash desde los campos del registro
    3. Verifica contra el ledger local / BSV blockchain
    4. Devuelve el resultado de verificación completo
    """
    # 1. Buscar en DB por hash
    audit_entry = db.query(AuditLog).filter(
        AuditLog.blockchain_hash == hash
    ).first()

    if not audit_entry:
        return {
            "verified": False,
            "hash": hash,
            "error": "Hash not found in audit database",
            "suggestion": "Verify the hash is correct or check on WhatsOnChain directly"
        }

    # 2. Recalcular hash desde los datos del registro
    payload = build_audit_payload(
        audit_id=audit_entry.id,
        timestamp=audit_entry.timestamp.isoformat() if audit_entry.timestamp else "",
        user_id=audit_entry.user_id,
        username=audit_entry.username,
        action=audit_entry.action,
        resource=audit_entry.resource,
        resource_id=audit_entry.resource_id,
        details=audit_entry.details,
        ip_address=audit_entry.ip_address,
    )
    recalculated_hash = compute_hash(payload)
    hash_matches = recalculated_hash == hash

    # 3. Verificar contra blockchain/ledger local
    blockchain_record = verify_audit_hash(hash)

    result = {
        "verified": hash_matches,
        "hash": hash,
        "recalculated_hash": recalculated_hash,
        "hash_integrity": "VALID" if hash_matches else "TAMPERED",
        "audit_entry": {
            "id": audit_entry.id,
            "timestamp": audit_entry.timestamp.isoformat() if audit_entry.timestamp else None,
            "username": audit_entry.username,
            "action": audit_entry.action,
            "resource": audit_entry.resource,
            "resource_id": audit_entry.resource_id,
        },
        "blockchain": {
            "tx_id": audit_entry.blockchain_tx_id,
            "status": "on_chain" if (audit_entry.blockchain_tx_id and not audit_entry.blockchain_tx_id.startswith("local_")) else "local_only",
        }
    }

    # Agregar datos de verificación on-chain si existen
    if blockchain_record:
        result["blockchain"]["on_chain_verified"] = blockchain_record.get("on_chain_verified", False)
        result["blockchain"]["confirmations"] = blockchain_record.get("confirmations", 0)
        if "explorer_url" in blockchain_record:
            result["blockchain"]["explorer_url"] = blockchain_record["explorer_url"]

    return result


@router.get("/verify-by-id/{audit_id}")
async def verify_by_audit_id(audit_id: int, db: Session = Depends(get_db)):
    """Verifica un registro de auditoría por su ID (PÚBLICO, sin auth)."""
    audit_entry = db.query(AuditLog).filter(AuditLog.id == audit_id).first()

    if not audit_entry:
        return {"verified": False, "error": "Audit log not found"}

    if not audit_entry.blockchain_hash:
        return {"verified": False, "error": "Audit log has no blockchain hash"}

    # Redirigir a verificación por hash
    return await verify_hash(audit_entry.blockchain_hash, db)


# ══════════════════════════════════════════════════════════════════════
# ENDPOINTS DE ADMIN - Gestión y estado
# ══════════════════════════════════════════════════════════════════════

@router.get("/status")
async def blockchain_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    """Estado general del sistema de notarización blockchain (Admin)."""
    from ..storage.models_sql import MerkleBatch

    total_logs = db.query(AuditLog).count()
    hashed_logs = db.query(AuditLog).filter(AuditLog.blockchain_hash.isnot(None)).count()
    on_chain_logs = db.query(AuditLog).filter(
        AuditLog.blockchain_tx_id.isnot(None),
        ~AuditLog.blockchain_tx_id.startswith("local_")
    ).count()
    local_only_logs = db.query(AuditLog).filter(
        AuditLog.blockchain_tx_id.isnot(None),
        AuditLog.blockchain_tx_id.startswith("local_")
    ).count()
    pending_logs = db.query(AuditLog).filter(
        AuditLog.blockchain_hash.isnot(None),
        AuditLog.merkle_batch_id.is_(None),
    ).count()
    in_batch_logs = db.query(AuditLog).filter(
        AuditLog.merkle_batch_id.isnot(None),
    ).count()

    # Merkle batch stats
    total_batches = db.query(MerkleBatch).count()
    on_chain_batches = db.query(MerkleBatch).filter(MerkleBatch.status == "ON_CHAIN").count()
    pending_batches = db.query(MerkleBatch).filter(MerkleBatch.status == "PENDING").count()

    return {
        "blockchain_enabled": bool(app_config.BSV_PRIVATE_KEY),
        "network": app_config.BSV_NETWORK,
        "mode": "merkle_batch",
        "total_audit_logs": total_logs,
        "hashed": hashed_logs,
        "on_chain": on_chain_logs,
        "local_only": local_only_logs,
        "pending_unbatched": pending_logs,
        "in_merkle_batch": in_batch_logs,
        "coverage_pct": round(hashed_logs / total_logs * 100, 1) if total_logs > 0 else 0,
        "merkle_batches": {
            "total": total_batches,
            "on_chain": on_chain_batches,
            "pending": pending_batches,
        },
    }


@router.get("/records")
async def blockchain_records(
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    """Lista registros de blockchain recientes del ledger local (Admin)."""
    records = list_blockchain_records(limit=limit)
    return {"records": records, "count": len(records)}


@router.post("/retry/{audit_id}")
async def retry_blockchain_registration(
    audit_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    """Reintentar el registro blockchain de un audit log específico (Admin)."""
    entry = db.query(AuditLog).filter(AuditLog.id == audit_id).first()
    if not entry:
        return {"error": "Audit log not found"}

    if not entry.blockchain_hash:
        return {"error": "Audit log has no hash to register"}

    if entry.blockchain_tx_id and not entry.blockchain_tx_id.startswith("local_"):
        return {"error": "Already registered on-chain", "tx_id": entry.blockchain_tx_id}

    # Lanzar registro como background task
    background_tasks.add_task(
        _background_register_and_update,
        audit_id=entry.id,
        timestamp=entry.timestamp.isoformat() if entry.timestamp else "",
        user_id=entry.user_id,
        username=entry.username,
        action=entry.action,
        resource=entry.resource,
        resource_id=entry.resource_id,
        details=entry.details,
        ip_address=entry.ip_address,
        blockchain_hash=entry.blockchain_hash,
    )

    return {"status": "retry_queued", "audit_id": audit_id}


def _background_register_and_update(
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
):
    """Background task: registra en blockchain y actualiza la DB con tx_id."""
    import logging
    logger = logging.getLogger(__name__)

    try:
        result = register_on_blockchain(
            audit_id=audit_id,
            timestamp=timestamp,
            user_id=user_id,
            username=username,
            action=action,
            resource=resource,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            blockchain_hash=blockchain_hash,
        )

        tx_id = result.get("tx_id")
        if tx_id:
            # Update DB with tx_id
            from ..storage.db import SessionLocal
            db = SessionLocal()
            try:
                from ..storage.repos.audit_repo import AuditRepo
                AuditRepo.update_tx_id(db, audit_id, tx_id)
            finally:
                db.close()

        logger.info(
            "[BLOCKCHAIN] Background register audit #%d → status=%s, tx=%s",
            audit_id, result.get("status"), tx_id,
        )

    except Exception as e:
        logger.error("[BLOCKCHAIN] Background register failed for audit #%d: %s", audit_id, e)


# ══════════════════════════════════════════════════════════════════════
# MERKLE TREE BATCH ENDPOINTS — Notarización eficiente
# ══════════════════════════════════════════════════════════════════════

@router.get("/merkle/pending")
async def merkle_pending(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    """Lista audit logs pendientes de incluir en un Merkle batch (Admin)."""
    pending = get_pending_hashes(db)
    return {"pending": len(pending), "audit_ids": [p["id"] for p in pending]}


@router.post("/merkle/batch")
async def merkle_create_batch(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    """Crea un Merkle batch con todos los audit logs pendientes (Admin).

    Agrupa N hashes en un Merkle Tree. Todavía no sube a BSV.
    Usa POST /merkle/broadcast/{batch_id} para enviar a blockchain.
    """
    return create_merkle_batch(db)


@router.post("/merkle/broadcast/{batch_id}")
async def merkle_broadcast(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    """Sube un Merkle batch a BSV blockchain en 1 sola TX (Admin).

    El Merkle Root se guarda como OP_RETURN. Todos los audit logs
    del batch quedan certificados con esa única transacción.
    """
    return broadcast_merkle_batch(db, batch_id)


@router.post("/merkle/batch-and-broadcast")
async def merkle_batch_and_broadcast(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    """Crea un batch y lo sube a BSV en un solo paso (Admin).

    Shortcut: agrupa todos los audit logs pendientes → Merkle Tree
    → 1 TX a BSV → todos certificados. ~$0.01 por batch.
    """
    return create_and_broadcast_batch(db)


@router.get("/merkle/proof/{audit_id}")
async def merkle_proof(
    audit_id: int,
    db: Session = Depends(get_db),
):
    """Genera el Merkle Proof para un audit log (PÚBLICO, sin auth).

    Devuelve el camino criptográfico del hash individual a la raíz
    del Merkle Tree. Cualquiera puede verificar con estos datos.
    """
    return get_merkle_proof_for_audit(db, audit_id)


@router.get("/merkle/verify/{audit_id}")
async def merkle_verify(
    audit_id: int,
    db: Session = Depends(get_db),
):
    """Verificación completa con Merkle Proof (PÚBLICO, sin auth).

    Recalcula el proof y valida que el hash del audit log
    produce la misma Merkle Root almacenada en BSV.
    """
    return verify_audit_in_batch(db, audit_id)


@router.get("/merkle/batches")
async def merkle_list_batches(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    """Lista Merkle batches recientes (Admin)."""
    batches = list_batches(db, limit=limit)
    return {"batches": batches, "count": len(batches)}

