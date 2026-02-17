from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional

from ..storage.db import get_db
from ..storage.models_sql import AuditLog
from ..auth.dependencies import get_current_user, require_role, User

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("/logs")
async def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    action: Optional[str] = None,
    username: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    """Get audit logs (Admin only)"""
    query = db.query(AuditLog).order_by(desc(AuditLog.timestamp))
    
    if action:
        query = query.filter(AuditLog.action.ilike(f"%{action}%"))
    if username:
        query = query.filter(AuditLog.username.ilike(f"%{username}%"))
    
    total = query.count()
    logs = query.offset(skip).limit(limit).all()
    
    return {
        "logs": [
            {
                "id": log.id,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                "user_id": log.user_id,
                "username": log.username,
                "action": log.action,
                "resource": log.resource,
                "resource_id": log.resource_id,
                "details": log.details,
                "ip_address": log.ip_address,
                "blockchain_hash": log.blockchain_hash,
                "blockchain_tx_id": log.blockchain_tx_id,
            }
            for log in logs
        ],
        "total": total
    }


@router.get("/export/csv")
async def export_audit_csv(
    limit: int = Query(500, ge=1, le=5000),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    """Export audit logs as CSV"""
    from fastapi.responses import StreamingResponse
    import io
    import csv
    
    logs = db.query(AuditLog).order_by(desc(AuditLog.timestamp)).limit(limit).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Timestamp", "Username", "Action", "Resource", "Resource ID", "Details", "IP", "Blockchain Hash", "TX ID", "WhatsOnChain"])
    
    for log in logs:
        woc_link = ""
        if log.blockchain_tx_id and not log.blockchain_tx_id.startswith("local_"):
            woc_link = f"https://whatsonchain.com/tx/{log.blockchain_tx_id}"
        writer.writerow([
            log.timestamp.isoformat() if log.timestamp else "",
            log.username or "",
            log.action or "",
            log.resource or "",
            log.resource_id or "",
            log.details or "",
            log.ip_address or "",
            log.blockchain_hash or "",
            log.blockchain_tx_id or "",
            woc_link,
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit_logs.csv"}
    )
