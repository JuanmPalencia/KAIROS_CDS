from fastapi import APIRouter, HTTPException, Depends, Request, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from ..storage.db import get_db
from ..storage.models_sql import IncidentSQL
from ..storage.repos.audit_repo import AuditRepo
from ..auth.dependencies import get_current_user, User
from ..core.data_collector import collect_incident

router = APIRouter(prefix="/events", tags=["events"])

class IncidentCreate(BaseModel):
    lat: float
    lon: float
    severity: int = 3
    incident_type: str = "GENERAL"
    description: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    affected_count: int = 1

@router.get("/incidents")
def list_incidents(city: Optional[str] = Query(None), db: Session = Depends(get_db)):
    """Get all non-closed incidents"""
    q = db.query(IncidentSQL).filter(IncidentSQL.status != "CLOSED")
    if city:
        q = q.filter(IncidentSQL.city == city)
    incs = q.all()
    return [
        {
            "id": i.id,
            "lat": i.lat,
            "lon": i.lon,
            "severity": i.severity,
            "status": i.status,
            "incident_type": i.incident_type,
            "description": i.description,
            "address": i.address,
            "city": i.city,
            "province": i.province,
            "affected_count": i.affected_count,
            "assigned_vehicle_id": i.assigned_vehicle_id,
            "created_at": i.created_at.isoformat() if i.created_at else None,
            "updated_at": i.updated_at.isoformat() if i.updated_at else None,
        }
        for i in incs
    ]


@router.get("/incidents/{incident_id}")
def get_incident(incident_id: str, db: Session = Depends(get_db)):
    """Get incident detail"""
    inc = db.query(IncidentSQL).filter(IncidentSQL.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    return {
        "id": inc.id,
        "lat": inc.lat,
        "lon": inc.lon,
        "severity": inc.severity,
        "status": inc.status,
        "incident_type": inc.incident_type,
        "description": inc.description,
        "address": inc.address,
        "city": inc.city,
        "province": inc.province,
        "affected_count": inc.affected_count,
        "assigned_vehicle_id": inc.assigned_vehicle_id,
        "created_at": inc.created_at.isoformat() if inc.created_at else None,
        "updated_at": inc.updated_at.isoformat() if inc.updated_at else None,
        "resolved_at": inc.resolved_at.isoformat() if inc.resolved_at else None,
    }


@router.post("/incidents")
def create_incident(body: IncidentCreate, request: Request, db: Session = Depends(get_db)):
    """Create a new incident (public endpoint for emergency calls)"""
    # generar id simple INC-xxx
    existing = db.query(IncidentSQL).count()
    inc_id = f"INC-{existing+1:03d}"

    inc = IncidentSQL(
        id=inc_id,
        lat=body.lat,
        lon=body.lon,
        severity=body.severity,
        incident_type=body.incident_type,
        description=body.description,
        address=body.address,
        city=body.city,
        province=body.province,
        affected_count=body.affected_count,
        status="OPEN",
        assigned_vehicle_id=None,
        created_at=datetime.utcnow(),
    )
    db.add(inc)
    db.commit()
    db.refresh(inc)
    
    # Audit log (no user for public endpoint)
    AuditRepo.log(
        db=db,
        action="CREATE",
        resource="INCIDENT",
        resource_id=inc.id,
        details=f"Type: {inc.incident_type}, Severity: {inc.severity}",
        ip_address=request.client.host if request.client else None
    )

    # Recoger datos anonimizados para reentrenamiento de IA
    try:
        collect_incident({
            "id": inc.id,
            "description": inc.description or "",
            "incident_type": inc.incident_type,
            "affected_count": inc.affected_count,
            "severity": inc.severity,
            "lat": inc.lat,
            "lon": inc.lon,
            "address": body.address,
            "city": body.city,
        })
    except Exception:
        pass  # No bloquear la creación si falla la recolección

    return {"ok": True, "incident_id": inc.id, "incident": {
        "id": inc.id,
        "lat": inc.lat,
        "lon": inc.lon,
        "severity": inc.severity,
        "status": inc.status,
        "incident_type": inc.incident_type,
    }}


@router.get("/incidents/{incident_id}/timeline")
def get_incident_timeline(incident_id: str, db: Session = Depends(get_db)):
    """Get timeline of events for an incident"""
    from ..storage.models_sql import AuditLog
    
    inc = db.query(IncidentSQL).filter(IncidentSQL.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Build timeline from incident data + audit logs
    timeline = []
    
    # Created
    timeline.append({
        "timestamp": inc.created_at.isoformat() if inc.created_at else None,
        "event": "CREATED",
        "label": "Incidente creado",
        "icon": "🚨",
        "details": f"Tipo: {inc.incident_type}, Severidad: {inc.severity}/5"
    })
    
    # Audit logs related to this incident
    audit_logs = db.query(AuditLog).filter(
        AuditLog.resource == "INCIDENT",
        AuditLog.resource_id == incident_id
    ).order_by(AuditLog.timestamp).all()
    
    for log in audit_logs:
        icon = "📝"
        if "ASSIGN" in (log.action or ""):
            icon = "🚑"
        elif "RESOLVE" in (log.action or ""):
            icon = "✅"
        elif "AI" in (log.details or ""):
            icon = "🤖"
        
        timeline.append({
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            "event": log.action,
            "label": log.details or log.action,
            "icon": icon,
            "details": f"Por: {log.username or 'Sistema'}"
        })
    
    # Assigned
    if inc.assigned_vehicle_id:
        timeline.append({
            "timestamp": inc.updated_at.isoformat() if inc.updated_at else None,
            "event": "ASSIGNED",
            "label": f"Ambulancia {inc.assigned_vehicle_id} asignada",
            "icon": "🚑",
            "details": f"Hospital: {inc.assigned_hospital_id or 'Pendiente'}"
        })
    
    # Resolved
    if inc.resolved_at:
        timeline.append({
            "timestamp": inc.resolved_at.isoformat(),
            "event": "RESOLVED",
            "label": "Incidente resuelto",
            "icon": "✅",
            "details": ""
        })
    
    # Sort by timestamp
    timeline.sort(key=lambda x: x["timestamp"] or "")
    
    return {
        "incident_id": incident_id,
        "timeline": timeline,
        "current_status": inc.status,
    }
