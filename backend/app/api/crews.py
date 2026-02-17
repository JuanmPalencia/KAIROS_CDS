"""Gestión de tripulaciones y turnos — Crew/Shift management."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
from ..storage.db import get_db
from ..storage.models_sql import CrewMember, Shift, Vehicle

router = APIRouter(prefix="/api/crews", tags=["crews"])


# ── Pydantic schemas ──

class CrewCreate(BaseModel):
    name: str
    role: str = "TES"  # TES, ENFERMERO, MEDICO, CONDUCTOR
    certification: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

class ShiftCreate(BaseModel):
    crew_member_id: str
    vehicle_id: Optional[str] = None
    shift_type: str = "DIA"
    start_time: str  # ISO string
    end_time: str
    notes: Optional[str] = None


# ── Seed data ──

CREW_SEED = [
    {"id": "CREW-001", "name": "Dr. Antonio García", "role": "MEDICO", "certification": "ACLS,ATLS,PHTLS", "phone": "+34 612 001 001"},
    {"id": "CREW-002", "name": "Laura Martínez (Enf.)", "role": "ENFERMERO", "certification": "ACLS,PHTLS", "phone": "+34 612 001 002"},
    {"id": "CREW-003", "name": "Carlos Ruiz (TES)", "role": "TES", "certification": "BLS,SVB_DEA", "phone": "+34 612 001 003"},
    {"id": "CREW-004", "name": "María López (Cond.)", "role": "CONDUCTOR", "certification": "BTP,BLS", "phone": "+34 612 001 004"},
    {"id": "CREW-005", "name": "Dra. Elena Sánchez", "role": "MEDICO", "certification": "ACLS,ATLS,PEDIATRIC", "phone": "+34 612 001 005"},
    {"id": "CREW-006", "name": "Pedro Fernández (Enf.)", "role": "ENFERMERO", "certification": "ACLS,PHTLS", "phone": "+34 612 001 006"},
    {"id": "CREW-007", "name": "Ana Torres (TES)", "role": "TES", "certification": "BLS,SVB_DEA", "phone": "+34 612 001 007"},
    {"id": "CREW-008", "name": "Javier Moreno (Cond.)", "role": "CONDUCTOR", "certification": "BTP,BLS", "phone": "+34 612 001 008"},
    {"id": "CREW-009", "name": "Dr. Roberto Díaz", "role": "MEDICO", "certification": "ACLS,NEONATAL", "phone": "+34 612 001 009"},
    {"id": "CREW-010", "name": "Lucía Hernández (Enf.)", "role": "ENFERMERO", "certification": "ACLS,OBSTETRICIA", "phone": "+34 612 001 010"},
    {"id": "CREW-011", "name": "Miguel Ángel Vega (TES)", "role": "TES", "certification": "BLS,SVB_DEA", "phone": "+34 612 001 011"},
    {"id": "CREW-012", "name": "Sofía Navarro (Cond.)", "role": "CONDUCTOR", "certification": "BTP,BLS", "phone": "+34 612 001 012"},
]


# ── Endpoints ──

@router.post("/seed")
def seed_crew(db: Session = Depends(get_db)):
    """Seed tripulación + turnos de ejemplo."""
    created = 0
    for data in CREW_SEED:
        existing = db.query(CrewMember).filter(CrewMember.id == data["id"]).first()
        if not existing:
            db.add(CrewMember(**data))
            created += 1
    db.commit()

    # Crear turnos de ejemplo — asignar tripulaciones a vehículos
    vehicles = db.query(Vehicle).filter(Vehicle.enabled == True).all()
    now = datetime.utcnow()
    hour = now.hour
    # Determinar turno actual según hora del día
    if 8 <= hour < 20:
        shift_type = "DIA"
        start = now.replace(hour=8, minute=0, second=0, microsecond=0)
        end = now.replace(hour=20, minute=0, second=0, microsecond=0)
    else:
        shift_type = "NOCHE"
        start = now.replace(hour=20, minute=0, second=0, microsecond=0)
        if hour < 8:
            start -= timedelta(days=1)
        end = start + timedelta(hours=12)
    shifts_created = 0

    # Asignar pares de crew a cada vehículo (conductor + sanitario)
    vehicle_assignments = {
        "SVA-001": ["CREW-001", "CREW-002", "CREW-004"],  # Médico + Enfermero + Conductor
        "SVA-002": ["CREW-005", "CREW-006", "CREW-008"],
        "SVB-001": ["CREW-003", "CREW-004"],  # TES + Conductor
        "SVB-002": ["CREW-007", "CREW-008"],
        "SVB-003": ["CREW-011", "CREW-012"],
        "VIR-001": ["CREW-009"],
        "VAMM-001": ["CREW-009", "CREW-010", "CREW-003"],
        "SAMU-001": ["CREW-005", "CREW-010"],
    }

    for vid, crew_ids in vehicle_assignments.items():
        veh = next((v for v in vehicles if v.id == vid), None)
        if not veh:
            continue
        for cid in crew_ids:
            existing_shift = db.query(Shift).filter(
                Shift.crew_member_id == cid,
                Shift.vehicle_id == vid,
                Shift.status == "ACTIVE"
            ).first()
            if not existing_shift:
                shift = Shift(
                    crew_member_id=cid,
                    vehicle_id=vid,
                    shift_type=shift_type,
                    start_time=start,
                    end_time=end,
                    status="ACTIVE",
                )
                db.add(shift)
                shifts_created += 1
    db.commit()
    return {"ok": True, "crew_created": created, "shifts_created": shifts_created}


@router.get("/members")
def list_crew(db: Session = Depends(get_db)):
    """Listar toda la tripulación."""
    members = db.query(CrewMember).filter(CrewMember.is_active == True).all()
    return [
        {
            "id": m.id,
            "name": m.name,
            "role": m.role,
            "certification": m.certification,
            "phone": m.phone,
            "is_active": m.is_active,
        }
        for m in members
    ]


@router.get("/members/{crew_id}")
def get_crew_member(crew_id: str, db: Session = Depends(get_db)):
    m = db.query(CrewMember).filter(CrewMember.id == crew_id).first()
    if not m:
        raise HTTPException(404, "Crew member not found")
    # Get active shift
    active_shift = db.query(Shift).filter(
        Shift.crew_member_id == crew_id,
        Shift.status == "ACTIVE"
    ).first()
    return {
        "id": m.id,
        "name": m.name,
        "role": m.role,
        "certification": m.certification,
        "phone": m.phone,
        "email": m.email,
        "is_active": m.is_active,
        "active_shift": {
            "vehicle_id": active_shift.vehicle_id,
            "shift_type": active_shift.shift_type,
            "start_time": active_shift.start_time.isoformat() if active_shift.start_time else None,
            "end_time": active_shift.end_time.isoformat() if active_shift.end_time else None,
        } if active_shift else None,
    }


@router.get("/shifts")
def list_shifts(status: Optional[str] = None, db: Session = Depends(get_db)):
    """Listar turnos, opcionalmente filtrados por estado."""
    q = db.query(Shift)
    if status:
        q = q.filter(Shift.status == status)
    shifts = q.order_by(Shift.start_time.desc()).limit(100).all()
    return [
        {
            "id": s.id,
            "crew_member_id": s.crew_member_id,
            "vehicle_id": s.vehicle_id,
            "shift_type": s.shift_type,
            "start_time": s.start_time.isoformat() if s.start_time else None,
            "end_time": s.end_time.isoformat() if s.end_time else None,
            "status": s.status,
            "notes": s.notes,
        }
        for s in shifts
    ]


@router.get("/vehicle/{vehicle_id}")
def get_vehicle_crew(vehicle_id: str, db: Session = Depends(get_db)):
    """Obtener tripulación activa de un vehículo."""
    shifts = db.query(Shift).filter(
        Shift.vehicle_id == vehicle_id,
        Shift.status == "ACTIVE"
    ).all()
    crew_ids = [s.crew_member_id for s in shifts]
    members = db.query(CrewMember).filter(CrewMember.id.in_(crew_ids)).all()
    return {
        "vehicle_id": vehicle_id,
        "crew": [
            {
                "id": m.id,
                "name": m.name,
                "role": m.role,
                "certification": m.certification,
                "phone": m.phone,
            }
            for m in members
        ]
    }


@router.post("/members")
def create_crew_member(body: CrewCreate, db: Session = Depends(get_db)):
    existing_count = db.query(CrewMember).count()
    new_id = f"CREW-{existing_count + 1:03d}"
    member = CrewMember(
        id=new_id, name=body.name, role=body.role,
        certification=body.certification, phone=body.phone, email=body.email
    )
    db.add(member)
    db.commit()
    return {"ok": True, "id": new_id}


@router.post("/shifts")
def create_shift(body: ShiftCreate, db: Session = Depends(get_db)):
    shift = Shift(
        crew_member_id=body.crew_member_id,
        vehicle_id=body.vehicle_id,
        shift_type=body.shift_type,
        start_time=datetime.fromisoformat(body.start_time),
        end_time=datetime.fromisoformat(body.end_time),
        notes=body.notes,
        status="ACTIVE",
    )
    db.add(shift)
    db.commit()
    return {"ok": True, "shift_id": shift.id}


@router.post("/shifts/{shift_id}/end")
def end_shift(shift_id: int, db: Session = Depends(get_db)):
    """Finalizar un turno activo."""
    shift = db.query(Shift).filter(Shift.id == shift_id).first()
    if not shift:
        raise HTTPException(404, "Shift not found")
    if shift.status != "ACTIVE":
        raise HTTPException(400, "Shift is not active")
    shift.status = "COMPLETED"
    shift.end_time = datetime.utcnow()
    db.commit()
    return {"ok": True, "shift_id": shift_id, "status": "COMPLETED"}
