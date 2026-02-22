# app/core/twin_engine.py
import time
import asyncio
import json
import math
import random
from datetime import datetime
from ..config import TICK_MS
from ..storage.db import SessionLocal
from ..storage.repos.vehicles_repo import VehicleRepo
from ..storage.repos.incidents_repo import IncidentsRepo
from ..storage.models_sql import Hospital, PatientCareReport, PatientTracking
from .sim_adapter import MockSimAdapter
from .metrics import available_vehicles_count, incidents_resolved_total
from .routing import get_router
from ..api.digital_twin import record_telemetry_tick


def _haversine_km(lat1, lon1, lat2, lon2):
    """Distancia en km entre dos coordenadas."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _build_fallback_route(start_lat, start_lon, end_lat, end_lon, n_points=30):
    """Genera una ruta sintética con pequeñas desviaciones para simular calles.

    No es una ruta real, pero mantiene continuidad geométrica y evita la línea
    recta que \"cruza edificios\".
    """
    pts = []
    for i in range(n_points + 1):
        t = i / n_points
        lat = start_lat + (end_lat - start_lat) * t
        lon = start_lon + (end_lon - start_lon) * t
        # Pequeña desviación perpendicular (simula giros de calle)
        if 0 < i < n_points:
            perp = math.sin(t * math.pi * 4) * 0.0004  # ondulación suave
            noise = random.uniform(-0.00008, 0.00008)
            dx = end_lat - start_lat
            dy = end_lon - start_lon
            mag = (dx ** 2 + dy ** 2) ** 0.5 or 1
            lat += (-dy / mag) * (perp + noise)
            lon += (dx / mag) * (perp + noise)
        pts.append([lat, lon])
    return pts


class TwinEngine:
    def __init__(self, ws_manager) -> None:
        self.ws = ws_manager
        self.sim = MockSimAdapter()
        self.running = False

    def _fleet_metrics(self, vehicles):
        active = len(vehicles)
        avg_fuel = round(sum(v.fuel for v in vehicles) / active, 2) if active else 0.0
        return {"active_vehicles": active, "avg_fuel": avg_fuel}

    @staticmethod
    def _dist2(a_lat, a_lon, b_lat, b_lon):
        return (a_lat - b_lat) ** 2 + (a_lon - b_lon) ** 2

    @staticmethod
    def _resolve_incident(db, inc, v):
        """Handle all resolution side effects: patient, hospital load, vehicle release."""
        vehicle_id = inc.assigned_vehicle_id
        inc.status = "RESOLVED"
        inc.route_phase = "COMPLETED"
        inc.resolved_at = datetime.utcnow()

        # Release vehicle (keep record of vehicle_id for patient)
        inc.assigned_vehicle_id = None
        v.status = "IDLE"
        v.speed = 0.0
        v.route_progress = 0.0

        # Decrement hospital load
        if inc.assigned_hospital_id:
            hosp = db.query(Hospital).get(inc.assigned_hospital_id)
            if hosp and hosp.current_load > 0:
                hosp.current_load = max(0, hosp.current_load - inc.affected_count)

        # Auto-create patient + tracking if not existing
        existing_pcr = db.query(PatientCareReport).filter(
            PatientCareReport.incident_id == inc.id
        ).first()
        if not existing_pcr:
            pcr_count = db.query(PatientCareReport).count()
            pcr_id = f"PCR-{pcr_count + 1:03d}"
            pcr = PatientCareReport(
                id=pcr_id,
                incident_id=inc.id,
                vehicle_id=vehicle_id,
                patient_name=f"Paciente {inc.type or 'Emergencia'}",
                chief_complaint=getattr(inc, 'description', None) or inc.type or "Emergencia",
                receiving_hospital_id=inc.assigned_hospital_id,
            )
            db.add(pcr)
            pt = PatientTracking(
                incident_id=inc.id,
                epcr_id=pcr_id,
                patient_name=pcr.patient_name,
                current_phase="AT_HOSPITAL_ER" if inc.assigned_hospital_id else "DISCHARGED",
                vehicle_id=vehicle_id,
                hospital_id=inc.assigned_hospital_id,
                admission_time=datetime.utcnow() if inc.assigned_hospital_id else None,
                discharge_time=datetime.utcnow() if not inc.assigned_hospital_id else None,
            )
            db.add(pt)

        incidents_resolved_total.inc()

    async def run(self) -> None:
        self.running = True

        # umbral de “llegada” (ajusta si quieres)
        ARRIVAL_DIST2 = 0.00005 ** 2

        while self.running:
            t0 = time.time()

            db = SessionLocal()
            try:
                vehicles = VehicleRepo.list_enabled(db)
                incidents = IncidentsRepo.list_open(db)

                # 1) ASIGNAR incidentes abiertos sin ambulancia
                for inc in incidents:
                    if inc.assigned_vehicle_id:
                        continue

                    # disponibles = IDLE
                    candidates = [v for v in vehicles if v.enabled and v.status == "IDLE"]
                    if not candidates:
                        continue

                    best = min(
                        candidates,
                        key=lambda v: self._dist2(v.lat, v.lon, inc.lat, inc.lon),
                    )

                    # Buscar hospital más cercano al incidente
                    all_hospitals = db.query(Hospital).filter(Hospital.available == True).all()
                    nearest_hosp = None
                    if all_hospitals:
                        nearest_hosp = min(
                            all_hospitals,
                            key=lambda h: self._dist2(h.lat, h.lon, inc.lat, inc.lon),
                        )

                    inc.assigned_vehicle_id = best.id
                    inc.assigned_hospital_id = nearest_hosp.id if nearest_hosp else None
                    inc.status = "ASSIGNED"
                    inc.route_phase = "TO_INCIDENT"
                    best.status = "EN_ROUTE"
                    best.speed = max(best.speed or 0.0, 1.0)
                    best.route_progress = 0.0

                    # Calcular ruta OSRM completa: ambulancia → incidente → hospital
                    try:
                        router = get_router()
                        waypoints_abc = []
                        total_km = 0.0
                        total_min = 0.0
                        incident_waypoint_idx = 0  # índice donde termina tramo A→B

                        # Tramo A → B (ambulancia → incidente)
                        leg_ab = router.get_route_sync(best.lat, best.lon, inc.lat, inc.lon)
                        if leg_ab and leg_ab.get("geometry") and len(leg_ab["geometry"]) >= 2:
                            waypoints_abc.extend(leg_ab["geometry"])
                            total_km += leg_ab["distance_km"]
                            total_min += leg_ab["duration_minutes"]
                        else:
                            waypoints_abc.extend(
                                _build_fallback_route(best.lat, best.lon, inc.lat, inc.lon)
                            )
                            total_km += _haversine_km(best.lat, best.lon, inc.lat, inc.lon)
                            total_min += total_km / 0.6

                        incident_waypoint_idx = len(waypoints_abc) - 1

                        # Tramo B → C (incidente → hospital)
                        if nearest_hosp:
                            leg_bc = router.get_route_sync(inc.lat, inc.lon, nearest_hosp.lat, nearest_hosp.lon)
                            if leg_bc and leg_bc.get("geometry") and len(leg_bc["geometry"]) >= 2:
                                # Saltar primer punto para no duplicar el punto del incidente
                                waypoints_abc.extend(leg_bc["geometry"][1:])
                                total_km += leg_bc["distance_km"]
                                total_min += leg_bc["duration_minutes"]
                            else:
                                fb = _build_fallback_route(inc.lat, inc.lon, nearest_hosp.lat, nearest_hosp.lon)
                                waypoints_abc.extend(fb[1:])
                                d = _haversine_km(inc.lat, inc.lon, nearest_hosp.lat, nearest_hosp.lon)
                                total_km += d
                                total_min += d / 0.6

                        # Simplificar para almacenamiento
                        simplified = router.simplify_route_for_storage(waypoints_abc, max_points=200)

                        # Recalcular incident_waypoint_idx tras simplificación
                        ratio = len(simplified) / max(len(waypoints_abc), 1)
                        incident_idx_simplified = max(1, int(incident_waypoint_idx * ratio))

                        inc.route_data = json.dumps({
                            "geometry": simplified,
                            "distance_km": round(total_km, 2),
                            "duration_minutes": round(total_min, 1),
                            "incident_waypoint_idx": incident_idx_simplified,
                            "hospital_id": nearest_hosp.id if nearest_hosp else None,
                        })

                    except Exception as e:
                        print(f"⚠️ OSRM routing failed: {e}, using fallback")
                        fb_ab = _build_fallback_route(best.lat, best.lon, inc.lat, inc.lon)
                        fb_bc = []
                        if nearest_hosp:
                            fb_bc = _build_fallback_route(inc.lat, inc.lon, nearest_hosp.lat, nearest_hosp.lon)[1:]
                        full_fb = fb_ab + fb_bc
                        inc.route_data = json.dumps({
                            "geometry": full_fb,
                            "distance_km": round(_haversine_km(best.lat, best.lon, inc.lat, inc.lon) +
                                                 (_haversine_km(inc.lat, inc.lon, nearest_hosp.lat, nearest_hosp.lon) if nearest_hosp else 0), 2),
                            "duration_minutes": 0,
                            "incident_waypoint_idx": len(fb_ab) - 1,
                            "hospital_id": nearest_hosp.id if nearest_hosp else None,
                        })

                db.commit()

                # 2) SIM: mover vehículos (hacia su incidente si están EN_ROUTE)
                self.sim.step(db, vehicles, incidents)

                # 3) RESOLVER: gestionar llegada a incidente y traslado a hospital
                for inc in incidents:
                    if inc.status != "ASSIGNED" or not inc.assigned_vehicle_id:
                        continue

                    v = next((x for x in vehicles if x.id == inc.assigned_vehicle_id), None)
                    if not v:
                        continue

                    phase = getattr(inc, 'route_phase', 'TO_INCIDENT') or 'TO_INCIDENT'

                    if phase == "TO_INCIDENT":
                        # Comprobar si llegó al incidente
                        # Calculamos el índice de progreso del incidente
                        try:
                            rd = json.loads(inc.route_data) if inc.route_data else {}
                            inc_idx = rd.get("incident_waypoint_idx", 0)
                            total_pts = len(rd.get("geometry", []))
                            inc_progress = inc_idx / max(total_pts - 1, 1) if total_pts > 1 else 1.0
                        except Exception:
                            inc_progress = 1.0

                        arrived_at_incident = (
                            v.route_progress >= inc_progress - 0.01
                            or self._dist2(v.lat, v.lon, inc.lat, inc.lon) <= ARRIVAL_DIST2
                        )

                        if arrived_at_incident:
                            if inc.assigned_hospital_id:
                                # Pasar a fase de traslado al hospital
                                inc.route_phase = "TO_HOSPITAL"
                                # No reseteamos route_progress, seguimos avanzando
                                # porque la ruta ya es A→B→C completa
                            else:
                                # Sin hospital, resolver directamente
                                self._resolve_incident(db, inc, v)

                    elif phase == "TO_HOSPITAL":
                        # Comprobar si llegó al hospital (progreso >= 95% o cerca del final)
                        arrived_at_hospital = v.route_progress >= 0.95

                        if not arrived_at_hospital and inc.assigned_hospital_id:
                            hosp = db.query(Hospital).get(inc.assigned_hospital_id)
                            if hosp and self._dist2(v.lat, v.lon, hosp.lat, hosp.lon) <= ARRIVAL_DIST2:
                                arrived_at_hospital = True

                        if arrived_at_hospital:
                            # Increment hospital load on arrival
                            if inc.assigned_hospital_id:
                                hosp = db.query(Hospital).get(inc.assigned_hospital_id)
                                if hosp:
                                    hosp.current_load = min(hosp.capacity, hosp.current_load + (inc.affected_count or 1))
                            self._resolve_incident(db, inc, v)

                db.commit()

                # Update metrics
                idle_vehicles = len([v for v in vehicles if v.status == "IDLE" and v.enabled])
                available_vehicles_count.set(idle_vehicles)

                # Record telemetry for Digital Twin
                try:
                    record_telemetry_tick(vehicles)
                except Exception:
                    pass  # telemetry is best-effort

                # 4) WS payload
                payload = {
                    "ts": time.time(),
                    "vehicles": [
                        {
                            "id": v.id,
                            "type": v.type,
                            "subtype": getattr(v, "subtype", "SVB"),
                            "status": v.status,
                            "lat": v.lat,
                            "lon": v.lon,
                            "speed": v.speed,
                            "fuel": v.fuel,
                            "tank_capacity": getattr(v, "tank_capacity", 80),
                            "trust_score": v.trust_score,
                            "enabled": v.enabled,
                            "sim_vehicle_ref": v.sim_vehicle_ref,
                            "route_progress": v.route_progress,
                        }
                        for v in vehicles
                    ],
                    "incidents": [
                        {
                            "id": i.id,
                            "lat": i.lat,
                            "lon": i.lon,
                            "severity": i.severity,
                            "status": i.status,
                            "assigned_vehicle_id": i.assigned_vehicle_id,
                            "assigned_hospital_id": i.assigned_hospital_id,
                            "route_data": i.route_data,
                            "route_phase": getattr(i, 'route_phase', 'TO_INCIDENT'),
                            "incident_type": i.incident_type,
                        }
                        for i in incidents
                    ],
                    "fleet_metrics": self._fleet_metrics(vehicles),
                    "alerts": [],
                }

            except Exception:
                db.rollback()
                raise
            finally:
                db.close()

            await self.ws.broadcast_json(payload)

            elapsed_ms = (time.time() - t0) * 1000
            await asyncio.sleep(max(0.0, (TICK_MS - elapsed_ms) / 1000))
