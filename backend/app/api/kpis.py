"""KPIs operativos en tiempo real — tiempos de respuesta, compliance, utilización."""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from ..storage.db import get_db
from ..storage.models_sql import IncidentSQL, Vehicle, KPISnapshot

router = APIRouter(prefix="/api/kpis", tags=["kpis"])


def _compute_response_times(db: Session, hours: int = 24, city: str = None):
    """Calcula tiempos de respuesta de incidentes resueltos en las últimas N horas."""
    since = datetime.utcnow() - timedelta(hours=hours)
    q = db.query(IncidentSQL).filter(
        IncidentSQL.status == "RESOLVED",
        IncidentSQL.resolved_at != None,
        IncidentSQL.created_at >= since,
    )
    if city:
        q = q.filter(IncidentSQL.city == city)
    resolved = q.all()

    if not resolved:
        return {
            "count": 0,
            "avg_response_sec": 0,
            "avg_total_sec": 0,
            "under_8min_pct": 0,
            "under_15min_pct": 0,
            "fastest_sec": 0,
            "slowest_sec": 0,
        }

    times = []
    for inc in resolved:
        if inc.created_at and inc.resolved_at:
            delta = (inc.resolved_at - inc.created_at).total_seconds()
            times.append(delta)

    if not times:
        return {"count": 0, "avg_response_sec": 0, "avg_total_sec": 0,
                "under_8min_pct": 0, "under_15min_pct": 0, "fastest_sec": 0, "slowest_sec": 0}

    avg_sec = sum(times) / len(times)
    under_8 = len([t for t in times if t < 480]) / len(times) * 100
    under_15 = len([t for t in times if t < 900]) / len(times) * 100

    return {
        "count": len(times),
        "avg_response_sec": round(avg_sec, 1),
        "avg_total_sec": round(avg_sec, 1),
        "under_8min_pct": round(under_8, 1),
        "under_15min_pct": round(under_15, 1),
        "fastest_sec": round(min(times), 1),
        "slowest_sec": round(max(times), 1),
    }


@router.get("/realtime")
def get_realtime_kpis(city: Optional[str] = Query(None), db: Session = Depends(get_db)):
    """KPIs en tiempo real: métricas operativas actuales."""
    vehicles = db.query(Vehicle).filter(Vehicle.enabled == True).all()
    q_open = db.query(IncidentSQL).filter(IncidentSQL.status.in_(["OPEN", "ASSIGNED"]))
    q_resolved = db.query(IncidentSQL).filter(
        IncidentSQL.status == "RESOLVED",
        IncidentSQL.resolved_at >= datetime.utcnow() - timedelta(hours=24)
    )
    q_total = db.query(IncidentSQL).filter(
        IncidentSQL.created_at >= datetime.utcnow() - timedelta(hours=24)
    )
    if city:
        q_open = q_open.filter(IncidentSQL.city == city)
        q_resolved = q_resolved.filter(IncidentSQL.city == city)
        q_total = q_total.filter(IncidentSQL.city == city)
    incidents_open = q_open.count()
    incidents_resolved_24h = q_resolved.count()
    incidents_total_24h = q_total.count()

    idle = len([v for v in vehicles if v.status == "IDLE"])
    en_route = len([v for v in vehicles if v.status == "EN_ROUTE"])
    refueling = len([v for v in vehicles if v.status == "REFUELING"])
    total = len(vehicles)
    utilization = ((total - idle) / total * 100) if total > 0 else 0

    avg_fuel = sum(v.fuel for v in vehicles) / total if total else 0

    response_times = _compute_response_times(db, hours=24, city=city)

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "fleet": {
            "total": total,
            "idle": idle,
            "en_route": en_route,
            "refueling": refueling,
            "utilization_pct": round(utilization, 1),
            "avg_fuel_pct": round(avg_fuel, 1),
        },
        "incidents": {
            "open": incidents_open,
            "resolved_24h": incidents_resolved_24h,
            "total_24h": incidents_total_24h,
        },
        "response_times": response_times,
        "compliance": {
            "samur_8min": response_times["under_8min_pct"],
            "urban_15min": response_times["under_15min_pct"],
            "target_8min": 75.0,  # Objetivo SAMUR: 75% bajo 8 min
            "target_15min": 95.0,
        }
    }


@router.get("/history")
def get_kpi_history(hours: int = 24, db: Session = Depends(get_db)):
    """Historial de snapshots de KPI."""
    since = datetime.utcnow() - timedelta(hours=hours)
    snapshots = db.query(KPISnapshot).filter(
        KPISnapshot.timestamp >= since
    ).order_by(KPISnapshot.timestamp).all()

    return [
        {
            "timestamp": s.timestamp.isoformat(),
            "avg_response_time_sec": s.avg_response_time_sec,
            "response_under_8min_pct": s.response_under_8min_pct,
            "incidents_total": s.incidents_total,
            "incidents_resolved": s.incidents_resolved,
            "fleet_utilization_pct": s.fleet_utilization_pct,
            "avg_fuel_pct": s.avg_fuel_pct,
        }
        for s in snapshots
    ]


@router.post("/snapshot")
def take_kpi_snapshot(db: Session = Depends(get_db)):
    """Guardar un snapshot de KPIs actual (llamado periódicamente)."""
    rt = _compute_response_times(db, hours=1)
    vehicles = db.query(Vehicle).filter(Vehicle.enabled == True).all()
    total = len(vehicles)
    idle = len([v for v in vehicles if v.status == "IDLE"])
    active = total - idle
    utilization = (active / total * 100) if total > 0 else 0
    avg_fuel = sum(v.fuel for v in vehicles) / total if total else 0

    incidents_open = db.query(IncidentSQL).filter(IncidentSQL.status.in_(["OPEN", "ASSIGNED"])).count()
    incidents_resolved = db.query(IncidentSQL).filter(IncidentSQL.status == "RESOLVED").count()
    incidents_total = db.query(IncidentSQL).count()

    snap = KPISnapshot(
        avg_response_time_sec=rt["avg_response_sec"],
        response_under_8min_pct=rt["under_8min_pct"],
        response_under_15min_pct=rt["under_15min_pct"],
        incidents_total=incidents_total,
        incidents_resolved=incidents_resolved,
        incidents_open=incidents_open,
        vehicles_active=active,
        vehicles_idle=idle,
        fleet_utilization_pct=round(utilization, 1),
        avg_fuel_pct=round(avg_fuel, 1),
    )
    db.add(snap)
    db.commit()
    return {"ok": True, "snapshot_id": snap.id}


@router.get("/by-vehicle")
def get_kpis_by_vehicle(city: Optional[str] = Query(None), db: Session = Depends(get_db)):
    """KPIs desglosados por vehículo."""
    vehicles = db.query(Vehicle).filter(Vehicle.enabled == True).all()
    result = []
    for v in vehicles:
        q_v = db.query(IncidentSQL).filter(
            IncidentSQL.assigned_vehicle_id == v.id,
            IncidentSQL.status == "RESOLVED",
            IncidentSQL.resolved_at != None,
        )
        if city:
            q_v = q_v.filter(IncidentSQL.city == city)
        resolved = q_v.all()
        times = []
        for inc in resolved:
            if inc.created_at and inc.resolved_at:
                times.append((inc.resolved_at - inc.created_at).total_seconds())
        result.append({
            "vehicle_id": v.id,
            "subtype": v.subtype,
            "total_incidents": len(resolved),
            "avg_time_sec": round(sum(times) / len(times), 1) if times else 0,
            "fuel_pct": round(v.fuel, 1),
            "status": v.status,
        })
    return result
