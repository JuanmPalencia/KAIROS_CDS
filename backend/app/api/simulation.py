# app/api/simulation.py
"""
API de simulación: generación automática de incidentes y reset del sistema.

Endpoints:
- POST /simulation/reset          — Limpia incidentes, auditoría, resets flota
- POST /simulation/auto-generate/start  — Inicia generación automática
- POST /simulation/auto-generate/stop   — Para generación automática
- GET  /simulation/auto-generate/status — Estado del generador
- POST /simulation/generate-one         — Genera un solo incidente aleatorio
- GET  /simulation/incident-types       — Lista tipos de incidentes disponibles
"""

import asyncio
import logging
import random
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..storage.db import SessionLocal, get_db
from ..storage.models_sql import IncidentSQL, AuditLog, MerkleBatch, Vehicle, PatientTracking, Hospital, PatientCareReport
from ..storage.repos.audit_repo import AuditRepo
from ..core.incident_generator import generate_random_incident, get_all_incident_types, INCIDENT_TYPES
from ..core.sim_adapter import get_speed_multiplier, set_speed_multiplier
from ..api.fleet import FLEET_SEED

router = APIRouter(prefix="/simulation", tags=["simulation"])
logger = logging.getLogger(__name__)

# ── Estado global del auto-generator ──────────────────────────────────
_auto_gen_task: asyncio.Task | None = None
_auto_gen_running: bool = False
_auto_gen_interval: int = 30  # segundos entre incidentes
_auto_gen_count: int = 0



async def _auto_generate_loop():
    """Bucle asíncrono que genera incidentes cada N segundos."""
    global _auto_gen_running, _auto_gen_count
    MAX_OPEN = 15  # Cap open incidents to prevent CPU overload
    while _auto_gen_running:
        try:
            db = SessionLocal()
            try:
                # Skip generation if too many open incidents
                open_count = db.query(IncidentSQL).filter(IncidentSQL.status.in_(["OPEN", "ASSIGNED"])).count()
                if open_count >= MAX_OPEN:
                    await asyncio.sleep(_auto_gen_interval)
                    db.close()
                    continue

                data = generate_random_incident()
                max_num = db.execute(
                    text("SELECT COALESCE(MAX(CAST(SUBSTRING(id FROM 5) AS INTEGER)), 0) FROM incidents")
                ).scalar() or 0
                inc_id = f"INC-{max_num + 1:03d}"

                inc = IncidentSQL(
                    id=inc_id,
                    lat=data["lat"],
                    lon=data["lon"],
                    severity=data["severity"],
                    incident_type=data["incident_type"],
                    description=data["description"],
                    address=data["address"],
                    city=data["city"],
                    province=data["province"],
                    affected_count=data["affected_count"],
                    status="OPEN",
                    created_at=datetime.utcnow(),
                )
                db.add(inc)
                db.commit()

                AuditRepo.log(
                    db=db,
                    action="CREATE",
                    resource="INCIDENT",
                    resource_id=inc.id,
                    details=f"[AUTO-GEN] Type: {inc.incident_type}, Severity: {inc.severity}, Desc: {inc.description}",
                )
                _auto_gen_count += 1
                logger.info("Auto-generated: %s — %s (sev %s) at %s", inc.id, inc.incident_type, inc.severity, inc.address)
            finally:
                db.close()
        except Exception as e:
            logger.error("Error in auto-generator: %s", e)

        # Intervalo variable: ±30% del base para más realismo
        jitter = random.uniform(0.7, 1.3)
        await asyncio.sleep(_auto_gen_interval * jitter)


@router.post("/reset")
def reset_system(db: Session = Depends(get_db)):
    """
    Limpia TODOS los incidentes, auditorías, merkle batches y resetea
    la flota de ambulancias a su estado inicial.
    """
    global _auto_gen_running, _auto_gen_task, _auto_gen_count

    # Detener auto-generador si está activo
    _auto_gen_running = False
    if _auto_gen_task and not _auto_gen_task.done():
        _auto_gen_task.cancel()
    _auto_gen_task = None
    _auto_gen_count = 0

    # Limpiar tablas en orden de dependencias (foreign keys)
    # PatientTracking → PatientCareReport → Incidents
    db.query(PatientTracking).delete()
    db.query(PatientCareReport).delete()
    deleted_incidents = db.query(IncidentSQL).delete()
    # Desvincular audit_logs de merkle_batches antes de borrar
    db.execute(text("UPDATE audit_logs SET merkle_batch_id = NULL WHERE merkle_batch_id IS NOT NULL"))
    deleted_audits = db.query(AuditLog).delete()
    deleted_merkle = db.query(MerkleBatch).delete()
    db.commit()

    # Resetear flota a estado original
    for entry in FLEET_SEED:
        veh = db.query(Vehicle).filter(Vehicle.id == entry["id"]).first()
        if veh:
            veh.status = "IDLE"
            veh.speed = 0.0
            veh.fuel = round(80 + 20 * random.random(), 1)
            veh.lat = entry["lat"]
            veh.lon = entry["lon"]
            veh.route_progress = 0.0
            veh.trust_score = 100
    db.commit()

    return {
        "ok": True,
        "deleted_incidents": deleted_incidents,
        "deleted_audits": deleted_audits,
        "deleted_merkle": deleted_merkle,
        "fleet_reset": True,
        "message": "Sistema reiniciado completamente",
    }


@router.post("/auto-generate/start")
async def start_auto_generate(interval: int = 30):
    """
    Inicia la generación automática de incidentes.
    
    Query params:
    - interval: segundos entre incidentes (default 30, min 10, max 300)
    """
    global _auto_gen_task, _auto_gen_running, _auto_gen_interval, _auto_gen_count

    interval = max(10, min(300, interval))
    _auto_gen_interval = interval

    if _auto_gen_running:
        return {"ok": True, "status": "already_running", "interval": _auto_gen_interval}

    _auto_gen_running = True
    _auto_gen_count = 0
    _auto_gen_task = asyncio.create_task(_auto_generate_loop())

    return {
        "ok": True,
        "status": "started",
        "interval": _auto_gen_interval,
        "message": f"Generando incidentes cada ~{_auto_gen_interval}s",
    }


@router.post("/auto-generate/stop")
async def stop_auto_generate():
    """Detiene la generación automática de incidentes."""
    global _auto_gen_task, _auto_gen_running

    was_running = _auto_gen_running
    _auto_gen_running = False
    if _auto_gen_task and not _auto_gen_task.done():
        _auto_gen_task.cancel()
    _auto_gen_task = None

    return {
        "ok": True,
        "status": "stopped",
        "was_running": was_running,
        "total_generated": _auto_gen_count,
    }


@router.get("/auto-generate/status")
def auto_generate_status():
    """Retorna el estado actual del generador automático."""
    return {
        "running": _auto_gen_running,
        "interval": _auto_gen_interval,
        "total_generated": _auto_gen_count,
    }





@router.post("/generate-one")
def generate_one(db: Session = Depends(get_db)):
    """Genera un solo incidente aleatorio (útil para pruebas manuales)."""
    data = generate_random_incident()
    max_num = db.execute(
        text("SELECT COALESCE(MAX(CAST(SUBSTRING(id FROM 5) AS INTEGER)), 0) FROM incidents")
    ).scalar() or 0
    inc_id = f"INC-{max_num + 1:03d}"

    inc = IncidentSQL(
        id=inc_id,
        lat=data["lat"],
        lon=data["lon"],
        severity=data["severity"],
        incident_type=data["incident_type"],
        description=data["description"],
        address=data["address"],
        city=data["city"],
        province=data["province"],
        affected_count=data["affected_count"],
        status="OPEN",
        created_at=datetime.utcnow(),
    )
    db.add(inc)
    db.commit()
    db.refresh(inc)

    AuditRepo.log(
        db=db,
        action="CREATE",
        resource="INCIDENT",
        resource_id=inc.id,
        details=f"[MANUAL-GEN] Type: {inc.incident_type}, Severity: {inc.severity}",
    )

    return {
        "ok": True,
        "incident": {
            "id": inc.id,
            "lat": inc.lat,
            "lon": inc.lon,
            "severity": inc.severity,
            "incident_type": inc.incident_type,
            "description": inc.description,
            "address": inc.address,
            "affected_count": inc.affected_count,
        },
    }


@router.get("/incident-types")
def list_incident_types():
    """Lista todos los tipos de incidentes disponibles con sus probabilidades."""
    return {
        "types": get_all_incident_types(),
        "total": len(INCIDENT_TYPES),
    }


@router.post("/speed")
def set_simulation_speed(multiplier: float = 1.0):
    """Ajusta el multiplicador de velocidad de los vehículos (0.5x – 20x)."""
    actual = set_speed_multiplier(multiplier)
    return {"ok": True, "speed_multiplier": actual}


@router.get("/speed")
def get_simulation_speed():
    """Devuelve el multiplicador de velocidad actual."""
    return {"speed_multiplier": get_speed_multiplier()}
