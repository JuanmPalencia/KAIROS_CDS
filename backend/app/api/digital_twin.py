# app/api/digital_twin.py
"""
Digital Twin API — telemetría en tiempo real, detección de anomalías,
mantenimiento predictivo y simulación de escenarios "what-if".
"""

import math
import random
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..auth.dependencies import get_current_user
from ..storage.db import get_db
from ..storage.models_sql import Vehicle, IncidentSQL, Hospital
from ..core.sim_adapter import get_speed_multiplier, MAX_SPEED, CONSUMPTION_L100KM

router = APIRouter(prefix="/digital-twin", tags=["digital-twin"])

# ── In-memory telemetry history (ring buffer per vehicle) ─────────────
_telemetry_history: Dict[str, list] = {}  # vid → [{ts, speed, fuel, lat, lon, …}]
MAX_HISTORY = 120  # ~60 seconds at 500ms ticks


def record_telemetry_tick(vehicles: list):
    """Called from twin_engine each tick to store telemetry snapshots."""
    ts = time.time()
    for v in vehicles:
        vid = v.id if hasattr(v, "id") else v.get("id", "?")
        entry = {
            "ts": ts,
            "speed": v.speed if hasattr(v, "speed") else v.get("speed", 0),
            "fuel": v.fuel if hasattr(v, "fuel") else v.get("fuel", 100),
            "lat": v.lat if hasattr(v, "lat") else v.get("lat", 0),
            "lon": v.lon if hasattr(v, "lon") else v.get("lon", 0),
            "status": v.status if hasattr(v, "status") else v.get("status", "IDLE"),
            "trust_score": (v.trust_score if hasattr(v, "trust_score") else v.get("trust_score", 100)),
            "route_progress": (v.route_progress if hasattr(v, "route_progress") else v.get("route_progress", 0)),
        }
        buf = _telemetry_history.setdefault(vid, [])
        buf.append(entry)
        if len(buf) > MAX_HISTORY:
            buf.pop(0)


# ── Anomaly detection helpers ─────────────────────────────────────────

def _detect_anomalies(v: Vehicle, history: list) -> List[Dict[str, Any]]:
    """Rule-based + statistical anomaly detection for a single vehicle."""
    anomalies: list = []
    subtype = getattr(v, "subtype", "SVB")
    max_spd = MAX_SPEED.get(subtype, 80)

    # 1. Over-speed
    if v.speed and v.speed > max_spd * 1.15:
        anomalies.append({
            "type": "OVER_SPEED",
            "severity": "HIGH",
            "message": f"Velocidad ({v.speed:.0f} km/h) supera el límite de {max_spd} km/h para {subtype}",
            "value": round(v.speed, 1),
            "threshold": max_spd,
        })

    # 2. Critical fuel
    if v.fuel is not None and v.fuel < 10:
        anomalies.append({
            "type": "CRITICAL_FUEL",
            "severity": "CRITICAL",
            "message": f"Combustible crítico: {v.fuel:.1f}%",
            "value": round(v.fuel, 1),
            "threshold": 10,
        })
    elif v.fuel is not None and v.fuel < 20:
        anomalies.append({
            "type": "LOW_FUEL",
            "severity": "MEDIUM",
            "message": f"Combustible bajo: {v.fuel:.1f}%",
            "value": round(v.fuel, 1),
            "threshold": 20,
        })

    # 3. Rapid fuel drop (last 20 ticks ≈ 10s)
    if len(history) >= 20:
        fuel_20_ago = history[-20]["fuel"]
        drop = fuel_20_ago - (v.fuel or 0)
        if drop > 3:  # >3% in 10s is suspicious
            anomalies.append({
                "type": "RAPID_FUEL_DROP",
                "severity": "HIGH",
                "message": f"Caída rápida de combustible: -{drop:.1f}% en últimos 10s",
                "value": round(drop, 1),
                "threshold": 3.0,
            })

    # 4. Trust score degradation
    if v.trust_score is not None and v.trust_score < 60:
        anomalies.append({
            "type": "LOW_TRUST",
            "severity": "HIGH",
            "message": f"Trust score bajo: {v.trust_score}",
            "value": v.trust_score,
            "threshold": 60,
        })

    # 5. Stalled vehicle (EN_ROUTE but speed=0 for many ticks)
    if v.status == "EN_ROUTE" and len(history) >= 10:
        recent_speeds = [h["speed"] for h in history[-10:]]
        if all(s == 0 or s is None for s in recent_speeds):
            anomalies.append({
                "type": "STALLED",
                "severity": "MEDIUM",
                "message": "Vehículo en ruta pero detenido durante los últimos ticks",
                "value": 0,
                "threshold": 1,
            })

    # 6. Position jitter (IDLE vehicle that moved significantly)
    if v.status == "IDLE" and len(history) >= 5:
        first = history[-5]
        dist = _haversine_m(first["lat"], first["lon"], v.lat, v.lon)
        if dist > 100:  # >100m for an IDLE vehicle
            anomalies.append({
                "type": "POSITION_DRIFT",
                "severity": "LOW",
                "message": f"Desplazamiento inesperado de {dist:.0f}m estando IDLE",
                "value": round(dist, 0),
                "threshold": 100,
            })

    return anomalies


def _haversine_m(lat1, lon1, lat2, lon2):
    R = 6_371_000
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ── Predictive maintenance ────────────────────────────────────────────

def _predict_maintenance(v: Vehicle, history: list) -> Dict[str, Any]:
    """Simple predictive maintenance based on telemetry patterns."""
    subtype = getattr(v, "subtype", "SVB")
    tank = getattr(v, "tank_capacity", 80.0) or 80.0

    # Simulated km (based on history speed integration)
    total_km = 0
    for h in history:
        spd = h.get("speed", 0) or 0
        total_km += (spd * 0.5 / 3600)  # speed km/h * 0.5s tick / 3600

    # Fuel consumption rate (L/100km equivalent)
    fuel_start = history[0]["fuel"] if history else v.fuel
    fuel_used_pct = max(0, (fuel_start or 100) - (v.fuel or 100))
    fuel_used_L = fuel_used_pct * tank / 100
    consumption_rate = (fuel_used_L / total_km * 100) if total_km > 0.01 else CONSUMPTION_L100KM.get(subtype, 18)

    expected = CONSUMPTION_L100KM.get(subtype, 18)
    efficiency = min(100, max(0, round(100 - abs(consumption_rate - expected) / expected * 50)))

    # Brake/engine wear estimation (based on speed variance)
    speeds = [h.get("speed", 0) or 0 for h in history]
    speed_variance = _variance(speeds) if len(speeds) > 2 else 0

    # Health score composite
    health_score = round(min(100, max(0,
        v.trust_score * 0.4
        + (100 - min(100, speed_variance * 0.5)) * 0.2
        + efficiency * 0.2
        + min(100, v.fuel or 0) * 0.2
    )))

    # Next maintenance prediction
    if health_score > 80:
        maintenance_status = "OK"
        next_maintenance = "Sin mantenimiento urgente"
        maintenance_urgency = "LOW"
    elif health_score > 50:
        maintenance_status = "PREVENTIVE"
        next_maintenance = "Mantenimiento preventivo recomendado"
        maintenance_urgency = "MEDIUM"
    else:
        maintenance_status = "URGENT"
        next_maintenance = "Mantenimiento urgente requerido"
        maintenance_urgency = "HIGH"

    return {
        "health_score": health_score,
        "efficiency_pct": efficiency,
        "consumption_rate_L100km": round(consumption_rate, 1),
        "expected_consumption": expected,
        "speed_variance": round(speed_variance, 1),
        "maintenance_status": maintenance_status,
        "maintenance_urgency": maintenance_urgency,
        "next_maintenance": next_maintenance,
        "estimated_range_km": round((v.fuel or 0) * tank / 100 / (expected / 100), 1) if expected > 0 else 0,
    }


def _variance(data):
    if len(data) < 2:
        return 0
    mean = sum(data) / len(data)
    return sum((x - mean) ** 2 for x in data) / len(data)


# ── What-If scenario simulator ───────────────────────────────────────

class WhatIfRequest(BaseModel):
    scenario: str  # "vehicle_breakdown", "fuel_shortage", "mass_casualty", "road_closure"
    vehicle_id: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


class WhatIfResult(BaseModel):
    scenario: str
    description: str
    impact: Dict[str, Any]
    recommendations: List[str]
    affected_vehicles: List[str]
    affected_incidents: List[str]
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL


# ── API Endpoints ─────────────────────────────────────────────────────

@router.get("/telemetry/{vehicle_id}")
def get_vehicle_telemetry(
    vehicle_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Full digital-twin telemetry for a single vehicle."""
    v = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not v:
        raise HTTPException(404, "Vehicle not found")

    history = _telemetry_history.get(vehicle_id, [])
    anomalies = _detect_anomalies(v, history)
    maintenance = _predict_maintenance(v, history)
    subtype = getattr(v, "subtype", "SVB")

    # Build telemetry sparkline data (last 60 entries)
    spark = history[-60:]

    return {
        "vehicle_id": v.id,
        "subtype": subtype,
        "status": v.status,
        "position": {"lat": v.lat, "lon": v.lon},
        "speed": v.speed,
        "fuel_pct": round(v.fuel, 1),
        "fuel_liters": round((v.fuel or 0) * (v.tank_capacity or 80) / 100, 1),
        "tank_capacity": v.tank_capacity or 80,
        "trust_score": v.trust_score,
        "route_progress": v.route_progress,
        "anomalies": anomalies,
        "maintenance": maintenance,
        "speed_multiplier": get_speed_multiplier(),
        "telemetry_sparkline": {
            "timestamps": [s["ts"] for s in spark],
            "speeds": [s["speed"] for s in spark],
            "fuels": [s["fuel"] for s in spark],
            "trust_scores": [s["trust_score"] for s in spark],
        },
        "twin_metadata": {
            "model": f"DigitalTwin<{subtype}>",
            "tick_rate_ms": 500,
            "history_depth": len(history),
            "max_speed_kmh": MAX_SPEED.get(subtype, 80),
            "consumption_l100km": CONSUMPTION_L100KM.get(subtype, 18),
        },
    }


@router.get("/fleet-health")
def get_fleet_health(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Aggregate digital-twin health overview for entire fleet."""
    vehicles = db.query(Vehicle).filter(Vehicle.enabled == True).all()
    fleet = []
    total_health = 0
    anomaly_count = 0

    for v in vehicles:
        history = _telemetry_history.get(v.id, [])
        anomalies = _detect_anomalies(v, history)
        maintenance = _predict_maintenance(v, history)
        total_health += maintenance["health_score"]
        anomaly_count += len(anomalies)
        fleet.append({
            "vehicle_id": v.id,
            "subtype": getattr(v, "subtype", "SVB"),
            "status": v.status,
            "health_score": maintenance["health_score"],
            "anomaly_count": len(anomalies),
            "maintenance_urgency": maintenance["maintenance_urgency"],
            "fuel_pct": round(v.fuel, 1),
            "speed": v.speed,
        })

    avg_health = round(total_health / len(vehicles)) if vehicles else 0

    return {
        "fleet_size": len(vehicles),
        "avg_health_score": avg_health,
        "total_anomalies": anomaly_count,
        "vehicles": sorted(fleet, key=lambda x: x["health_score"]),
        "inter_twin_links": _build_inter_twin_links(vehicles),
    }


def _build_inter_twin_links(vehicles: list) -> List[Dict]:
    """Conceptual inter-twin communication links.
    Shows which twins share context (same zone, same incident corridor)."""
    links = []
    en_route = [v for v in vehicles if v.status == "EN_ROUTE"]
    for i, a in enumerate(en_route):
        for b in en_route[i + 1:]:
            dist = _haversine_m(a.lat, a.lon, b.lat, b.lon)
            if dist < 2000:  # within 2km
                links.append({
                    "from": a.id,
                    "to": b.id,
                    "distance_m": round(dist),
                    "link_type": "PROXIMITY",
                    "message": f"Vehículos a {dist:.0f}m — coordinación potencial",
                })
    return links


@router.post("/what-if", response_model=WhatIfResult)
def simulate_what_if(
    req: WhatIfRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Simulate a what-if scenario and return impact analysis."""
    vehicles = db.query(Vehicle).filter(Vehicle.enabled == True).all()
    incidents = db.query(IncidentSQL).filter(IncidentSQL.status.in_(["OPEN", "ASSIGNED"])).all()
    params = req.parameters or {}

    if req.scenario == "vehicle_breakdown":
        return _whatif_vehicle_breakdown(req.vehicle_id, vehicles, incidents, db)
    elif req.scenario == "fuel_shortage":
        return _whatif_fuel_shortage(vehicles, incidents, params)
    elif req.scenario == "mass_casualty":
        return _whatif_mass_casualty(vehicles, incidents, params)
    elif req.scenario == "road_closure":
        return _whatif_road_closure(vehicles, incidents, params)
    else:
        raise HTTPException(400, f"Escenario desconocido: {req.scenario}")


def _whatif_vehicle_breakdown(vid: Optional[str], vehicles, incidents, db):
    if vid:
        target = next((v for v in vehicles if v.id == vid), None)
    else:
        en_route = [v for v in vehicles if v.status == "EN_ROUTE"]
        target = en_route[0] if en_route else vehicles[0] if vehicles else None

    if not target:
        raise HTTPException(404, "No vehicle found for scenario")

    # Find incidents assigned to this vehicle
    affected_incs = [i for i in incidents if i.assigned_vehicle_id == target.id]
    idle_count = len([v for v in vehicles if v.status == "IDLE"])
    reassignable = idle_count > 0

    risk = "LOW" if idle_count >= 3 else "MEDIUM" if idle_count >= 1 else "CRITICAL"

    recs = []
    if reassignable:
        recs.append(f"Reasignar {len(affected_incs)} incidente(s) a una de las {idle_count} ambulancias disponibles")
    else:
        recs.append("⚠️ No hay ambulancias disponibles — se requiere activación de reserva")
    recs.append(f"Enviar equipo de mantenimiento a posición ({target.lat:.4f}, {target.lon:.4f})")
    if target.fuel and target.fuel < 30:
        recs.append("Verificar si la avería está relacionada con el bajo nivel de combustible")

    return WhatIfResult(
        scenario="vehicle_breakdown",
        description=f"Simulación: avería de {target.id} ({getattr(target, 'subtype', 'SVB')})",
        impact={
            "vehicles_lost": 1,
            "incidents_affected": len(affected_incs),
            "idle_remaining": idle_count,
            "coverage_reduction_pct": round(100 / max(len(vehicles), 1), 1),
            "reassignment_possible": reassignable,
        },
        recommendations=recs,
        affected_vehicles=[target.id],
        affected_incidents=[i.id for i in affected_incs],
        risk_level=risk,
    )


def _whatif_fuel_shortage(vehicles, incidents, params):
    threshold = params.get("threshold_pct", 30)
    affected = [v for v in vehicles if (v.fuel or 100) < threshold]
    en_route_affected = [v for v in affected if v.status == "EN_ROUTE"]

    risk = "LOW" if len(affected) <= 1 else "MEDIUM" if len(affected) <= 3 else "HIGH" if len(affected) <= 5 else "CRITICAL"
    affected_inc_ids = []
    for v in en_route_affected:
        for i in incidents:
            if i.assigned_vehicle_id == v.id:
                affected_inc_ids.append(i.id)

    recs = [
        f"{len(affected)} vehículos con combustible < {threshold}%",
        f"{len(en_route_affected)} están en ruta — riesgo de no completar misión",
    ]
    if en_route_affected:
        recs.append("Preparar repostaje de emergencia o reasignación inmediata")
    recs.append("Revisar política de repostaje preventivo (umbral actual: 25%)")

    return WhatIfResult(
        scenario="fuel_shortage",
        description=f"Simulación: escasez de combustible (umbral {threshold}%)",
        impact={
            "vehicles_affected": len(affected),
            "en_route_at_risk": len(en_route_affected),
            "incidents_at_risk": len(affected_inc_ids),
            "fleet_pct_affected": round(len(affected) / max(len(vehicles), 1) * 100, 1),
        },
        recommendations=recs,
        affected_vehicles=[v.id for v in affected],
        affected_incidents=affected_inc_ids,
        risk_level=risk,
    )


def _whatif_mass_casualty(vehicles, incidents, params):
    extra_incidents = params.get("extra_incidents", 10)
    idle = [v for v in vehicles if v.status == "IDLE"]
    capacity_gap = max(0, extra_incidents - len(idle))

    risk = "LOW" if capacity_gap == 0 else "MEDIUM" if capacity_gap <= 3 else "HIGH" if capacity_gap <= 5 else "CRITICAL"

    recs = [
        f"Capacidad actual: {len(idle)} ambulancias disponibles vs {extra_incidents} incidentes adicionales",
    ]
    if capacity_gap > 0:
        recs.append(f"Déficit de {capacity_gap} unidades — activar protocolo de emergencia masiva")
        recs.append("Coordinar con servicios inter-agencia (Bomberos, Policía, SAMUR)")
        recs.append("Priorizar por severidad — triaje avanzado")
    else:
        recs.append("Capacidad suficiente — monitorizar evolución")

    return WhatIfResult(
        scenario="mass_casualty",
        description=f"Simulación: incidente masivo con {extra_incidents} víctimas adicionales",
        impact={
            "extra_incidents": extra_incidents,
            "idle_available": len(idle),
            "capacity_gap": capacity_gap,
            "overload_pct": round(capacity_gap / max(len(vehicles), 1) * 100, 1),
        },
        recommendations=recs,
        affected_vehicles=[v.id for v in idle],
        affected_incidents=[],
        risk_level=risk,
    )


def _whatif_road_closure(vehicles, incidents, params):
    lat = params.get("lat", 40.42)
    lon = params.get("lon", -3.70)
    radius_m = params.get("radius_m", 1000)

    affected_v = [v for v in vehicles if _haversine_m(v.lat, v.lon, lat, lon) < radius_m]
    affected_i = [i for i in incidents if _haversine_m(i.lat, i.lon, lat, lon) < radius_m]

    en_route_affected = [v for v in affected_v if v.status == "EN_ROUTE"]
    risk = "LOW" if not en_route_affected else "MEDIUM" if len(en_route_affected) <= 2 else "HIGH"

    recs = [
        f"Corte vial en ({lat:.4f}, {lon:.4f}) — radio {radius_m}m",
        f"{len(affected_v)} vehículos afectados, {len(en_route_affected)} en ruta",
    ]
    if en_route_affected:
        recs.append("Recalcular rutas OSRM excluyendo zona bloqueada")
        recs.append("Informar a conductores por canal de dispatch")
    if affected_i:
        recs.append(f"{len(affected_i)} incidentes en zona — posible retraso en respuesta")

    return WhatIfResult(
        scenario="road_closure",
        description=f"Simulación: corte vial en ({lat:.4f}, {lon:.4f})",
        impact={
            "vehicles_in_zone": len(affected_v),
            "en_route_disrupted": len(en_route_affected),
            "incidents_in_zone": len(affected_i),
            "radius_m": radius_m,
        },
        recommendations=recs,
        affected_vehicles=[v.id for v in affected_v],
        affected_incidents=[i.id for i in affected_i],
        risk_level=risk,
    )
