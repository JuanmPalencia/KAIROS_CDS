"""ePCR — Informe Clínico Electrónico + Patient Tracking lifecycle."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from ..storage.db import get_db
from ..storage.models_sql import PatientCareReport, PatientTracking, IncidentSQL

router = APIRouter(prefix="/api/epcr", tags=["epcr"])


class EPCRCreate(BaseModel):
    incident_id: str
    vehicle_id: Optional[str] = None
    crew_member_id: Optional[str] = None
    patient_name: Optional[str] = None
    patient_age: Optional[int] = None
    patient_gender: Optional[str] = None
    patient_id_number: Optional[str] = None
    chief_complaint: Optional[str] = None
    symptoms: Optional[str] = None
    allergies: Optional[str] = None
    medications: Optional[str] = None
    medical_history: Optional[str] = None
    # Vitals
    heart_rate: Optional[int] = None
    blood_pressure_sys: Optional[int] = None
    blood_pressure_dia: Optional[int] = None
    respiratory_rate: Optional[int] = None
    spo2: Optional[int] = None
    temperature: Optional[float] = None
    glasgow_score: Optional[int] = None
    pain_scale: Optional[int] = None
    # MPDS
    mpds_code: Optional[str] = None
    mpds_determinant: Optional[str] = None
    # Treatment
    treatment: Optional[str] = None
    medications_administered: Optional[str] = None
    procedures: Optional[str] = None
    disposition: Optional[str] = None


class VitalsUpdate(BaseModel):
    heart_rate: Optional[int] = None
    blood_pressure_sys: Optional[int] = None
    blood_pressure_dia: Optional[int] = None
    respiratory_rate: Optional[int] = None
    spo2: Optional[int] = None
    temperature: Optional[float] = None
    glasgow_score: Optional[int] = None
    pain_scale: Optional[int] = None


class PatientPhaseUpdate(BaseModel):
    phase: str  # ON_SCENE, IN_AMBULANCE, AT_HOSPITAL_ER, ADMITTED, DISCHARGED
    hospital_id: Optional[str] = None
    hospital_bed: Optional[str] = None
    notes: Optional[str] = None
    discharge_disposition: Optional[str] = None


# ── MPDS Determinant codes ──
MPDS_PROTOCOLS = {
    "CARDIO": {"code": "10", "name": "Dolor torácico", "determinants": {
        "ALPHA": "Dolor no cardíaco probable",
        "BRAVO": "Desconocido, < 35 años", 
        "CHARLIE": "Dolor cardíaco o dificultad respiratoria",
        "DELTA": "Sin respuesta o parada cardíaca",
        "ECHO": "PCR confirmada"
    }},
    "RESPIRATORY": {"code": "06", "name": "Dificultad respiratoria", "determinants": {
        "CHARLIE": "Dificultad respiratoria anormal",
        "DELTA": "Sin respirar / cianosis"
    }},
    "NEUROLOGICAL": {"code": "28", "name": "ACV / Ictus", "determinants": {
        "CHARLIE": "Síntomas positivos FAST",
        "DELTA": "Inconsciente"
    }},
    "TRAUMA": {"code": "30", "name": "Traumatismo", "determinants": {
        "ALPHA": "No peligroso",
        "BRAVO": "Posible lesión peligrosa",
        "DELTA": "Trauma mayor / inconsciente"
    }},
    "PEDIATRIC": {"code": "24", "name": "Pediátrico", "determinants": {
        "CHARLIE": "Dificultad respiratoria niño",
        "DELTA": "No respira / inconsciente"
    }},
    "BURN": {"code": "07", "name": "Quemaduras", "determinants": {
        "ALPHA": "Quemadura menor",
        "CHARLIE": "Quemadura > 18% o vía aérea",
        "DELTA": "Quemados múltiples / atrapados"
    }},
    "DROWNING": {"code": "14", "name": "Ahogamiento", "determinants": {
        "CHARLIE": "Consciente post-inmersión",
        "DELTA": "Inconsciente / sumergido"
    }},
}


@router.post("/create")
def create_epcr(body: EPCRCreate, db: Session = Depends(get_db)):
    """Crear un nuevo ePCR para un incidente."""
    inc = db.query(IncidentSQL).filter(IncidentSQL.id == body.incident_id).first()
    if not inc:
        raise HTTPException(404, "Incident not found")

    existing_count = db.query(PatientCareReport).count()
    pcr_id = f"PCR-{existing_count + 1:03d}"

    pcr = PatientCareReport(
        id=pcr_id,
        incident_id=body.incident_id,
        vehicle_id=body.vehicle_id or inc.assigned_vehicle_id,
        crew_member_id=body.crew_member_id,
        patient_name=body.patient_name,
        patient_age=body.patient_age,
        patient_gender=body.patient_gender,
        patient_id_number=body.patient_id_number,
        chief_complaint=body.chief_complaint,
        symptoms=body.symptoms,
        allergies=body.allergies,
        medications=body.medications,
        medical_history=body.medical_history,
        heart_rate=body.heart_rate,
        blood_pressure_sys=body.blood_pressure_sys,
        blood_pressure_dia=body.blood_pressure_dia,
        respiratory_rate=body.respiratory_rate,
        spo2=body.spo2,
        temperature=body.temperature,
        glasgow_score=body.glasgow_score,
        pain_scale=body.pain_scale,
        mpds_code=body.mpds_code,
        mpds_determinant=body.mpds_determinant,
        treatment=body.treatment,
        medications_administered=body.medications_administered,
        procedures=body.procedures,
        disposition=body.disposition,
        receiving_hospital_id=inc.assigned_hospital_id,
    )
    db.add(pcr)

    # Also create patient tracking entry
    pt = PatientTracking(
        incident_id=body.incident_id,
        epcr_id=pcr_id,
        patient_name=body.patient_name,
        current_phase="ON_SCENE",
        vehicle_id=body.vehicle_id or inc.assigned_vehicle_id,
        hospital_id=inc.assigned_hospital_id,
    )
    db.add(pt)
    db.commit()
    return {"ok": True, "epcr_id": pcr_id}


@router.get("/incident/{incident_id}")
def get_epcr_by_incident(incident_id: str, db: Session = Depends(get_db)):
    """Obtener ePCR de un incidente."""
    pcr = db.query(PatientCareReport).filter(
        PatientCareReport.incident_id == incident_id
    ).first()
    if not pcr:
        return {"epcr": None}
    return {
        "epcr": {
            "id": pcr.id,
            "incident_id": pcr.incident_id,
            "vehicle_id": pcr.vehicle_id,
            "crew_member_id": pcr.crew_member_id,
            "patient_name": pcr.patient_name,
            "patient_age": pcr.patient_age,
            "patient_gender": pcr.patient_gender,
            "chief_complaint": pcr.chief_complaint,
            "symptoms": pcr.symptoms,
            "allergies": pcr.allergies,
            "medical_history": pcr.medical_history,
            "heart_rate": pcr.heart_rate,
            "blood_pressure_sys": pcr.blood_pressure_sys,
            "blood_pressure_dia": pcr.blood_pressure_dia,
            "respiratory_rate": pcr.respiratory_rate,
            "spo2": pcr.spo2,
            "temperature": pcr.temperature,
            "glasgow_score": pcr.glasgow_score,
            "pain_scale": pcr.pain_scale,
            "mpds_code": pcr.mpds_code,
            "mpds_determinant": pcr.mpds_determinant,
            "treatment": pcr.treatment,
            "medications_administered": pcr.medications_administered,
            "procedures": pcr.procedures,
            "disposition": pcr.disposition,
            "receiving_hospital_id": pcr.receiving_hospital_id,
            "scene_arrival": pcr.scene_arrival.isoformat() if pcr.scene_arrival else None,
            "hospital_arrival": pcr.hospital_arrival.isoformat() if pcr.hospital_arrival else None,
            "created_at": pcr.created_at.isoformat() if pcr.created_at else None,
        }
    }


@router.put("/{epcr_id}/vitals")
def update_vitals(epcr_id: str, body: VitalsUpdate, db: Session = Depends(get_db)):
    """Actualizar constantes vitales de un ePCR."""
    pcr = db.query(PatientCareReport).filter(PatientCareReport.id == epcr_id).first()
    if not pcr:
        raise HTTPException(404, "ePCR not found")
    for field in ["heart_rate", "blood_pressure_sys", "blood_pressure_dia",
                   "respiratory_rate", "spo2", "temperature", "glasgow_score", "pain_scale"]:
        val = getattr(body, field, None)
        if val is not None:
            setattr(pcr, field, val)
    db.commit()
    return {"ok": True}


@router.get("/mpds-protocols")
def get_mpds_protocols():
    """Obtener protocolos MPDS para triaje telefónico."""
    return MPDS_PROTOCOLS


# ── Patient Tracking ──

@router.get("/tracking/{incident_id}")
def get_patient_tracking(incident_id: str, db: Session = Depends(get_db)):
    """Obtener el estado de tracking del paciente."""
    pts = db.query(PatientTracking).filter(
        PatientTracking.incident_id == incident_id
    ).all()
    return [
        {
            "id": pt.id,
            "incident_id": pt.incident_id,
            "epcr_id": pt.epcr_id,
            "patient_name": pt.patient_name,
            "current_phase": pt.current_phase,
            "vehicle_id": pt.vehicle_id,
            "hospital_id": pt.hospital_id,
            "hospital_bed": pt.hospital_bed,
            "admission_time": pt.admission_time.isoformat() if pt.admission_time else None,
            "discharge_time": pt.discharge_time.isoformat() if pt.discharge_time else None,
            "discharge_disposition": pt.discharge_disposition,
            "notes": pt.notes,
            "created_at": pt.created_at.isoformat() if pt.created_at else None,
            "updated_at": pt.updated_at.isoformat() if pt.updated_at else None,
        }
        for pt in pts
    ]


@router.put("/tracking/{tracking_id}/phase")
def update_patient_phase(tracking_id: int, body: PatientPhaseUpdate, db: Session = Depends(get_db)):
    """Actualizar fase del paciente en su ciclo de vida."""
    pt = db.query(PatientTracking).filter(PatientTracking.id == tracking_id).first()
    if not pt:
        raise HTTPException(404, "Patient tracking not found")

    pt.current_phase = body.phase
    if body.hospital_id:
        pt.hospital_id = body.hospital_id
    if body.hospital_bed:
        pt.hospital_bed = body.hospital_bed
    if body.notes:
        pt.notes = body.notes

    if body.phase == "AT_HOSPITAL_ER":
        pt.admission_time = datetime.utcnow()
    elif body.phase == "DISCHARGED":
        pt.discharge_time = datetime.utcnow()
        pt.discharge_disposition = body.discharge_disposition or "HOME"

    db.commit()
    return {"ok": True, "phase": pt.current_phase}


@router.get("/all-tracking")
def list_all_patient_tracking(db: Session = Depends(get_db)):
    """Listar todos los pacientes en seguimiento activo."""
    pts = db.query(PatientTracking).filter(
        PatientTracking.current_phase.notin_(["DISCHARGED"])
    ).order_by(PatientTracking.created_at.desc()).all()
    return [
        {
            "id": pt.id,
            "incident_id": pt.incident_id,
            "patient_name": pt.patient_name,
            "current_phase": pt.current_phase,
            "vehicle_id": pt.vehicle_id,
            "hospital_id": pt.hospital_id,
            "hospital_bed": pt.hospital_bed,
            "created_at": pt.created_at.isoformat() if pt.created_at else None,
        }
        for pt in pts
    ]


@router.get("/all-tracking-full")
def list_all_patient_tracking_full(db: Session = Depends(get_db)):
    """Listar TODOS los pacientes (activos + dados de alta)."""
    pts = db.query(PatientTracking).order_by(PatientTracking.created_at.desc()).all()
    return [
        {
            "id": pt.id,
            "incident_id": pt.incident_id,
            "patient_name": pt.patient_name,
            "current_phase": pt.current_phase,
            "vehicle_id": pt.vehicle_id,
            "hospital_id": pt.hospital_id,
            "hospital_bed": pt.hospital_bed,
            "admission_time": pt.admission_time.isoformat() if pt.admission_time else None,
            "discharge_time": pt.discharge_time.isoformat() if pt.discharge_time else None,
            "notes": pt.notes,
            "created_at": pt.created_at.isoformat() if pt.created_at else None,
        }
        for pt in pts
    ]


@router.post("/seed-demo-patients")
def seed_demo_patients(db: Session = Depends(get_db)):
    """Crear pacientes de demo para visualización del tracking."""
    import random
    names = [
        "María García López", "Juan Martínez Ruiz", "Ana Fernández Torres",
        "Carlos López Sánchez", "Elena Díaz Moreno", "Miguel Hernández Gil",
        "Laura Pérez Navarro", "Pedro Rodríguez Blanco", "Sofia Romero Castro",
        "Alejandro Muñoz Vega",
    ]
    phases = ["ON_SCENE", "IN_AMBULANCE", "AT_HOSPITAL_ER", "ADMITTED"]
    hospitals = ["HOSP-001", "HOSP-002", "HOSP-003", "HOSP-004", "HOSP-005"]
    vehicles = ["AMB-001", "AMB-002", "AMB-003", "AMB-004", "AMB-005"]
    beds = ["Box A1", "Box A2", "Box B1", "Box B2", "Box C1", "UCI-1", "UCI-2", None]

    # Get existing incidents
    incs = db.query(IncidentSQL).limit(10).all()
    inc_ids = [i.id for i in incs] if incs else [f"INC-DEMO-{i:03d}" for i in range(1, 11)]

    created = 0
    for i, name in enumerate(names):
        phase = phases[i % len(phases)]
        pt = PatientTracking(
            incident_id=inc_ids[i % len(inc_ids)],
            patient_name=name,
            current_phase=phase,
            vehicle_id=vehicles[i % len(vehicles)],
            hospital_id=hospitals[i % len(hospitals)] if phase in ("AT_HOSPITAL_ER", "ADMITTED") else None,
            hospital_bed=random.choice(beds) if phase in ("AT_HOSPITAL_ER", "ADMITTED") else None,
            admission_time=datetime.utcnow() if phase in ("AT_HOSPITAL_ER", "ADMITTED") else None,
        )
        db.add(pt)
        created += 1

    db.commit()
    return {"ok": True, "created": created}
