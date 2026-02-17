from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import json

from ..storage.db import get_db
from ..storage.models_sql import IncidentSQL, Hospital, Vehicle, PatientCareReport, PatientTracking
from ..core.ai_assignment import suggest_hospital_assignment, suggest_vehicle_assignment
from ..auth.dependencies import get_current_user, User, require_role
from ..storage.repos.audit_repo import AuditRepo

router = APIRouter(prefix="/api/assignments", tags=["assignments"])


class AssignmentSuggestionResponse(BaseModel):
    incident_id: str
    vehicle_suggestion: Optional[dict]
    hospital_suggestion: Optional[dict]


class AssignmentDecision(BaseModel):
    incident_id: str
    vehicle_id: Optional[str] = None
    hospital_id: Optional[str] = None
    override_reason: Optional[str] = None  # If operator overrides AI suggestion


@router.get("/suggest/{incident_id}", response_model=AssignmentSuggestionResponse)
async def get_assignment_suggestions(
    incident_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "OPERATOR"]))
):
    """Get AI suggestions for vehicle and hospital assignment"""
    incident = db.query(IncidentSQL).filter(IncidentSQL.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Get available vehicles
    available_vehicles = db.query(Vehicle).filter(
        Vehicle.enabled == True,
        Vehicle.status == "IDLE"
    ).all()
    
    # Get AI suggestions
    vehicle_suggestion = suggest_vehicle_assignment(db, incident, available_vehicles)
    hospital_suggestion = suggest_hospital_assignment(db, incident)
    
    # Store suggestions in incident (for audit/review)
    if hospital_suggestion:
        incident.suggested_hospital_id = hospital_suggestion["hospital_id"]
        incident.ai_confidence = hospital_suggestion["confidence"]
        incident.ai_reasoning = hospital_suggestion["reasoning"]
        db.commit()
    
    return AssignmentSuggestionResponse(
        incident_id=incident_id,
        vehicle_suggestion=vehicle_suggestion,
        hospital_suggestion=hospital_suggestion
    )


@router.post("/confirm")
async def confirm_assignment(
    decision: AssignmentDecision,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "OPERATOR"]))
):
    """Operator confirms or overrides AI assignment"""
    incident = db.query(IncidentSQL).filter(IncidentSQL.id == decision.incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Update incident with human decision
    if decision.vehicle_id:
        vehicle = db.query(Vehicle).filter(Vehicle.id == decision.vehicle_id).first()
        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        
        incident.assigned_vehicle_id = decision.vehicle_id
        incident.status = "ASSIGNED"
        vehicle.status = "EN_ROUTE"
    
    if decision.hospital_id:
        hospital = db.query(Hospital).filter(Hospital.id == decision.hospital_id).first()
        if not hospital:
            raise HTTPException(status_code=404, detail="Hospital not found")
        
        incident.assigned_hospital_id = decision.hospital_id
        hospital.current_load += incident.affected_count
    
    db.commit()
    
    # Log the decision
    action_type = "AI_ACCEPTED" if (
        decision.hospital_id == incident.suggested_hospital_id and not decision.override_reason
    ) else "AI_OVERRIDDEN"
    
    AuditRepo.log(
        db,
        user_id=current_user.id,
        username=current_user.username,
        action=action_type,
        resource="INCIDENT_ASSIGNMENT",
        resource_id=decision.incident_id,
        details=json.dumps({
            "vehicle_id": decision.vehicle_id,
            "hospital_id": decision.hospital_id,
            "suggested_hospital": incident.suggested_hospital_id,
            "override_reason": decision.override_reason,
            "ai_confidence": incident.ai_confidence
        }),
        ip_address=request.client.host if request.client else None
    )
    
    return {
        "status": "success",
        "incident_id": decision.incident_id,
        "assigned_vehicle": decision.vehicle_id,
        "assigned_hospital": decision.hospital_id,
        "action_logged": action_type
    }


@router.post("/resolve/{incident_id}")
async def resolve_incident(
    incident_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "OPERATOR"]))
):
    """Mark incident as resolved (patient delivered to hospital)"""
    incident = db.query(IncidentSQL).filter(IncidentSQL.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Update incident status
    from datetime import datetime
    incident.status = "RESOLVED"
    incident.resolved_at = datetime.utcnow()
    
    # Save vehicle_id before releasing (for patient/audit records)
    vehicle_id = incident.assigned_vehicle_id
    
    # Release vehicle
    if vehicle_id:
        vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
        if vehicle:
            vehicle.status = "IDLE"
    
    # Update hospital load (decrement when patient is treated and leaves)
    if incident.assigned_hospital_id:
        hospital = db.query(Hospital).filter(Hospital.id == incident.assigned_hospital_id).first()
        if hospital and hospital.current_load > 0:
            hospital.current_load = max(0, hospital.current_load - incident.affected_count)
    
    # Auto-create patient + tracking if not already existing
    existing_pcr = db.query(PatientCareReport).filter(
        PatientCareReport.incident_id == incident_id
    ).first()
    if not existing_pcr:
        pcr_count = db.query(PatientCareReport).count()
        pcr_id = f"PCR-{pcr_count + 1:03d}"
        pcr = PatientCareReport(
            id=pcr_id,
            incident_id=incident_id,
            vehicle_id=vehicle_id,
            patient_name=f"Paciente {incident.type or 'Emergencia'}",
            chief_complaint=incident.description or incident.type or "Emergencia médica",
            receiving_hospital_id=incident.assigned_hospital_id,
        )
        db.add(pcr)

        pt = PatientTracking(
            incident_id=incident_id,
            epcr_id=pcr_id,
            patient_name=pcr.patient_name,
            current_phase="AT_HOSPITAL_ER",
            vehicle_id=vehicle_id,
            hospital_id=incident.assigned_hospital_id,
            admission_time=datetime.utcnow(),
        )
        db.add(pt)
    else:
        # Update existing tracking to AT_HOSPITAL_ER
        existing_pt = db.query(PatientTracking).filter(
            PatientTracking.incident_id == incident_id
        ).first()
        if existing_pt and existing_pt.current_phase in ("ON_SCENE", "IN_AMBULANCE"):
            existing_pt.current_phase = "AT_HOSPITAL_ER"
            existing_pt.admission_time = datetime.utcnow()
    
    db.commit()
    
    # Log resolution
    AuditRepo.log(
        db,
        user_id=current_user.id,
        username=current_user.username,
        action="RESOLVE",
        resource="INCIDENT",
        resource_id=incident_id,
        details=json.dumps({
            "vehicle_id": vehicle_id,
            "hospital_id": incident.assigned_hospital_id,
            "duration_minutes": (incident.resolved_at - incident.created_at).total_seconds() / 60
        }),
        ip_address=request.client.host if request.client else None
    )
    
    return {
        "status": "success",
        "incident_id": incident_id,
        "resolved_at": incident.resolved_at
    }
