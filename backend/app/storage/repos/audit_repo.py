import logging
from sqlalchemy.orm import Session
from ..models_sql import AuditLog
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class AuditRepo:
    @staticmethod
    def log(
        db: Session,
        action: str,
        resource: Optional[str] = None,
        resource_id: Optional[str] = None,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        details: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """Create an audit log entry with blockchain hash."""
        ts = datetime.utcnow()
        log = AuditLog(
            timestamp=ts,
            user_id=user_id,
            username=username,
            action=action,
            resource=resource,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.add(log)
        db.commit()
        db.refresh(log)

        # Compute blockchain hash immediately (sync, fast)
        # Blockchain registration is manual via POST /api/blockchain/retry/{id}
        try:
            from ...blockchain.notarizer import compute_audit_hash
            hash_val = compute_audit_hash(
                audit_id=log.id,
                timestamp=ts.isoformat(),
                user_id=user_id,
                username=username,
                action=action,
                resource=resource,
                resource_id=resource_id,
                details=details,
                ip_address=ip_address,
            )
            log.blockchain_hash = hash_val
            db.commit()
        except Exception as e:
            logger.warning("Failed to compute blockchain hash for audit #%d: %s", log.id, e)

        return log

    @staticmethod
    def update_tx_id(db: Session, audit_id: int, tx_id: str):
        """Update the blockchain transaction ID after async registration."""
        entry = db.query(AuditLog).filter(AuditLog.id == audit_id).first()
        if entry:
            entry.blockchain_tx_id = tx_id
            db.commit()

    @staticmethod
    def get_logs(db: Session, limit: int = 100, user_id: Optional[int] = None):
        """Get audit logs"""
        query = db.query(AuditLog).order_by(AuditLog.timestamp.desc())
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        return query.limit(limit).all()
