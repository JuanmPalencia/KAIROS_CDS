from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy.orm import Session
from ..storage.db import get_db
from ..storage.models_sql import Vehicle, AuditLog
from .chat import _messages as chat_messages

router = APIRouter(prefix="/fleet", tags=["fleet"])

# ── Subtipos reales de ambulancias en España ────────────────────────
# SVB  = Soporte Vital Básico  (Mercedes Sprinter / VW Crafter ~80L depósito)
# SVA  = Soporte Vital Avanzado (Fiat Ducato / MB Sprinter ~90L, UCI móvil)
# VIR  = Vehículo de Intervención Rápida (SUV/todoterreno ~70L, 1er respondiente)
# VAMM = Vehículo Asistencia Médica Múltiple (camión ligero ~120L, catástrofes)
# SAMU = Servicio Atención Médica Urgente (helicóptero-simulado / SUV ~75L)

FLEET_SEED = [
    # ── SVB — Soporte Vital Básico (las más comunes) ──────────────
    {"id": "SVB-001", "subtype": "SVB", "tank": 80,  "lat": 40.4530, "lon": -3.6883, "base": "Base SAMUR Chamartín"},
    {"id": "SVB-002", "subtype": "SVB", "tank": 80,  "lat": 40.4072, "lon": -3.6920, "base": "Base SAMUR Retiro"},
    {"id": "SVB-003", "subtype": "SVB", "tank": 85,  "lat": 40.3850, "lon": -3.7100, "base": "Base SAMUR Usera"},

    # ── SVA — Soporte Vital Avanzado (UCI móvil) ──────────────────
    {"id": "SVA-001", "subtype": "SVA", "tank": 90,  "lat": 40.4400, "lon": -3.7000, "base": "Base SUMMA Tetuán"},
    {"id": "SVA-002", "subtype": "SVA", "tank": 90,  "lat": 40.4200, "lon": -3.7100, "base": "Base SUMMA Centro"},

    # ── VIR — Vehículo Intervención Rápida (1er respondiente) ─────
    {"id": "VIR-001", "subtype": "VIR", "tank": 70,  "lat": 40.4300, "lon": -3.6760, "base": "Base VIR Salamanca"},

    # ── VAMM — Asistencia Médica Múltiple (catástrofes) ───────────
    {"id": "VAMM-001","subtype": "VAMM","tank": 120, "lat": 40.4650, "lon": -3.7050, "base": "Base VAMM Norte"},

    # ── SAMU — Servicio Atención Médica Urgente ───────────────────
    {"id": "SAMU-001","subtype": "SAMU","tank": 75,  "lat": 40.3970, "lon": -3.7250, "base": "Base SAMU Sur"},
]


@router.post("/vehicles")
def create_vehicle(v: dict, db: Session = Depends(get_db)):
    """
    Body:
    {"id":"SVA-001","type":"AMB","subtype":"SVA","lat":40.44,"lon":-3.70,"enabled":true}
    """
    veh = Vehicle(
        id=v["id"],
        type=v.get("type", "AMB"),
        subtype=v.get("subtype", "SVB"),
        status=v.get("status", "IDLE"),
        lat=float(v.get("lat", 40.4168)),
        lon=float(v.get("lon", -3.7038)),
        speed=float(v.get("speed", 0.0)),
        fuel=float(v.get("fuel", 100.0)),
        tank_capacity=float(v.get("tank_capacity", 80.0)),
        trust_score=int(v.get("trust_score", 100)),
        enabled=bool(v.get("enabled", True)),
    )
    db.merge(veh)
    db.commit()
    return {"created": veh.id}

@router.post("/seed-ambulances")
def seed_ambulances(db: Session = Depends(get_db)):
    """
    Crea la flota realista de ambulancias españolas según FLEET_SEED.
    SVB (Soporte Vital Básico), SVA (Soporte Vital Avanzado),
    VIR (Intervención Rápida), VAMM (Asistencia Múltiple), SAMU.
    """
    created = []
    for entry in FLEET_SEED:
        veh = Vehicle(
            id=entry["id"],
            type="AMB",
            subtype=entry["subtype"],
            status="IDLE",
            lat=entry["lat"],
            lon=entry["lon"],
            speed=0.0,
            fuel=round(80 + 20 * __import__("random").random(), 1),  # 80-100%
            tank_capacity=float(entry["tank"]),
            trust_score=100,
            enabled=True,
        )
        db.merge(veh)
        created.append(veh.id)

    db.commit()
    return {"ok": True, "created": created, "count": len(created)}



@router.get("/vehicles")
def list_vehicles(db: Session = Depends(get_db)):
    rows = db.query(Vehicle).all()
    return [
        {
            "id": r.id,
            "type": r.type,
            "subtype": getattr(r, "subtype", "SVB"),
            "status": r.status,
            "lat": r.lat,
            "lon": r.lon,
            "speed": r.speed,
            "fuel": r.fuel,
            "tank_capacity": getattr(r, "tank_capacity", 80.0),
            "trust_score": r.trust_score,
            "enabled": r.enabled,
        }
        for r in rows
    ]


class VehiclePatch(BaseModel):
    status: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    fuel: Optional[float] = None
    speed: Optional[float] = None


STATUS_LABELS_ES = {
    "IDLE": "Disponible",
    "EN_ROUTE": "En Ruta",
    "ON_SCENE": "En Escena",
    "RETURNING": "Retornando",
    "MAINTENANCE": "Mantenimiento",
    "REFUELING": "Repostando",
}


@router.patch("/vehicles/{vehicle_id}")
def patch_vehicle(vehicle_id: str, patch: VehiclePatch, db: Session = Depends(get_db)):
    veh = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not veh:
        return {"error": "Vehicle not found"}, 404

        old_status = veh.status
        for field, val in patch.dict(exclude_none=True).items():
            setattr(veh, field, val)
        db.commit()

        # ── Notify rest of the system when status changes ──
        if patch.status and patch.status != old_status:
            new_label = STATUS_LABELS_ES.get(patch.status, patch.status)
            old_label = STATUS_LABELS_ES.get(old_status, old_status)

            # 1) Audit log entry
            try:
                audit = AuditLog(
                    user_id=0,
                    username="SISTEMA",
                    action="VEHICLE_STATUS_CHANGE",
                    resource="vehicle",
                    resource_id=vehicle_id,
                    details=f"{vehicle_id}: {old_label} → {new_label}",
                    ip_address="driver-app",
                )
                db.add(audit)
                db.commit()
            except Exception:
                db.rollback()

            # 2) Chat notification in dispatch channel
            try:
                chat_messages.append({
                    "id": str(uuid4()),
                    "user": "SISTEMA",
                    "role": "SYSTEM",
                    "text": f"🚑 {vehicle_id} cambió estado: {old_label} → {new_label}",
                    "channel": "dispatch",
                    "ts": datetime.now(timezone.utc).isoformat(),
                })
            except Exception:
                pass

        return {
            "id": veh.id,
            "status": veh.status,
            "lat": veh.lat,
            "lon": veh.lon,
            "fuel": veh.fuel,
            "speed": veh.speed,
        }
