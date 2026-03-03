# app/core/twin_engine.py
"""
Optimized Twin Engine — High-performance simulation loop.

Key optimizations:
- Hospital cache (no N+1 queries)
- Pre-built vehicle lookup dict
- Minimal DB queries per tick
- Lean route computation (Haversine direct, 6 waypoints)
- Batched commits
"""
import time
import asyncio
import json
import math
import random
import logging
from datetime import datetime
from ..config import TICK_MS
from ..storage.db import SessionLocal

logger = logging.getLogger(__name__)
from ..storage.repos.vehicles_repo import VehicleRepo
from ..storage.repos.incidents_repo import IncidentsRepo
from ..storage.models_sql import Hospital, PatientCareReport, PatientTracking
from .sim_adapter import MockSimAdapter
from .metrics import available_vehicles_count, incidents_resolved_total
from ..api.digital_twin import record_telemetry_tick


def _haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _dist2(a_lat, a_lon, b_lat, b_lon):
    return (a_lat - b_lat) ** 2 + (a_lon - b_lon) ** 2


def _build_direct_route(start_lat, start_lon, end_lat, end_lon, n_points=6):
    """Direct route with linear interpolation. 6 points = minimal data, smooth movement."""
    pts = []
    for i in range(n_points + 1):
        t = i / n_points
        pts.append([
            start_lat + (end_lat - start_lat) * t,
            start_lon + (end_lon - start_lon) * t,
        ])
    return pts


# ── PCR ID counter (avoids COUNT(*) query each time) ────────────────
_pcr_counter = 0
_pcr_counter_initialized = False


class TwinEngine:
    def __init__(self, ws_manager) -> None:
        self.ws = ws_manager
        self.sim = MockSimAdapter()
        self.running = False
        # Hospital cache (refreshed every N ticks)
        self._hospital_cache = []
        self._hospital_dict = {}
        self._hospital_cache_tick = 0
        self._HOSPITAL_CACHE_TTL = 10  # refresh every 10 ticks (~15s)

    def _refresh_hospitals(self, db):
        """Load hospitals as plain dicts (avoids detached ORM session issues)."""
        hospitals = db.query(Hospital).filter(Hospital.available == True).all()
        self._hospital_cache = []
        self._hospital_dict = {}
        for h in hospitals:
            hd = {"id": h.id, "lat": h.lat, "lon": h.lon, "capacity": h.capacity,
                  "current_load": h.current_load}
            self._hospital_cache.append(hd)
            self._hospital_dict[h.id] = hd
        self._hospital_cache_tick = 0

    def _get_hospital(self, hosp_id):
        """O(1) hospital lookup from cache."""
        return self._hospital_dict.get(hosp_id)

    def _find_nearest_hospital(self, lat, lon):
        if not self._hospital_cache:
            return None
        best = min(self._hospital_cache, key=lambda h: _dist2(h["lat"], h["lon"], lat, lon))
        # Return an object-like wrapper for compatibility
        class HospRef:
            def __init__(self, d):
                self.id = d["id"]
                self.lat = d["lat"]
                self.lon = d["lon"]
        return HospRef(best)

    @staticmethod
    def _resolve_incident(db, inc, v, hospital_dict, pcr_counter_ref):
        """Resolve incident — uses DB for hospital load (needs persistence)."""
        vehicle_id = inc.assigned_vehicle_id
        inc.status = "RESOLVED"
        inc.route_phase = "COMPLETED"
        inc.resolved_at = datetime.utcnow()

        inc.assigned_vehicle_id = None
        v.status = "IDLE"
        v.speed = 0.0
        v.route_progress = 0.0

        # Hospital load update via DB (needs real persistence)
        if inc.assigned_hospital_id:
            hosp = db.query(Hospital).get(inc.assigned_hospital_id)
            if hosp and hosp.current_load > 0:
                hosp.current_load = max(0, hosp.current_load - (inc.affected_count or 1))

        # Create patient record using counter (no COUNT query)
        global _pcr_counter, _pcr_counter_initialized
        if not _pcr_counter_initialized:
            _pcr_counter = db.query(PatientCareReport).count()
            _pcr_counter_initialized = True

        existing = db.query(PatientCareReport).filter(
            PatientCareReport.incident_id == inc.id
        ).first()
        if not existing:
            _pcr_counter += 1
            pcr_id = f"PCR-{_pcr_counter:03d}"
            pcr = PatientCareReport(
                id=pcr_id,
                incident_id=inc.id,
                vehicle_id=vehicle_id,
                patient_name=f"Paciente {inc.incident_type or 'Emergencia'}",
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
        ARRIVAL_DIST2 = 0.0003 ** 2  # ~33m arrival threshold (was 5m — too tight)
        _at_incident_ticks = {}  # incident_id → tick counter (persists across DB sessions)
        print(f"[TWIN-ENGINE] Started (TICK_MS={TICK_MS})", flush=True)

        # On startup, resolve stale incidents to avoid CPU overload
        _cleanup_db = SessionLocal()
        try:
            from app.storage.models_sql import Incident as _Inc
            _stale = _cleanup_db.query(_Inc).filter(_Inc.status.in_(["OPEN", "ASSIGNED"])).all()
            if len(_stale) > 10:
                for _s in _stale[10:]:
                    _s.status = "RESOLVED"
                _cleanup_db.commit()
                print(f"[TWIN-ENGINE] Cleaned {len(_stale) - 10} stale incidents on startup", flush=True)
        except Exception as _e:
            print(f"[TWIN-ENGINE] Cleanup warning: {_e}", flush=True)
        finally:
            _cleanup_db.close()

        while self.running:
            t0 = time.time()

            db = SessionLocal()
            try:
                vehicles = VehicleRepo.list_enabled(db)
                incidents = IncidentsRepo.list_open(db)

                # Pre-build vehicle lookup dict (O(1) lookups instead of O(n) scans)
                vehicle_map = {v.id: v for v in vehicles}

                # Refresh hospital cache periodically
                self._hospital_cache_tick += 1
                if self._hospital_cache_tick >= self._HOSPITAL_CACHE_TTL or not self._hospital_cache:
                    self._refresh_hospitals(db)

                # ── 1) ASSIGN unassigned OPEN incidents ─────────────────
                idle_count = 0
                for inc in incidents:
                    if inc.assigned_vehicle_id or inc.status != "OPEN":
                        continue

                    candidates = [v for v in vehicles if v.enabled and v.status == "IDLE"]
                    if not candidates:
                        continue

                    best = min(candidates, key=lambda v: _dist2(v.lat, v.lon, inc.lat, inc.lon))
                    nearest_hosp = self._find_nearest_hospital(inc.lat, inc.lon)

                    inc.assigned_vehicle_id = best.id
                    inc.assigned_hospital_id = nearest_hosp.id if nearest_hosp else None
                    inc.status = "ASSIGNED"
                    inc.route_phase = "TO_INCIDENT"
                    best.status = "EN_ROUTE"
                    best.speed = 1.0
                    best.route_progress = 0.0

                    # Build direct route (6+6 = 12 points max)
                    waypoints = _build_direct_route(best.lat, best.lon, inc.lat, inc.lon)
                    dist_ab = _haversine_km(best.lat, best.lon, inc.lat, inc.lon)
                    total_km = dist_ab
                    incident_idx = len(waypoints) - 1

                    if nearest_hosp:
                        leg_bc = _build_direct_route(inc.lat, inc.lon, nearest_hosp.lat, nearest_hosp.lon)
                        waypoints.extend(leg_bc[1:])
                        total_km += _haversine_km(inc.lat, inc.lon, nearest_hosp.lat, nearest_hosp.lon)

                    inc.route_data = json.dumps({
                        "geometry": waypoints,
                        "distance_km": round(total_km, 2),
                        "duration_minutes": round(total_km / 0.8, 1),
                        "incident_waypoint_idx": incident_idx,
                        "hospital_id": nearest_hosp.id if nearest_hosp else None,
                    })

                db.commit()

                # ── 2) MOVE vehicles ────────────────────────────────────
                self.sim.step(db, vehicles, incidents)

                # ── 3) RESOLVE arrivals ─────────────────────────────────
                for inc in incidents:
                    if inc.status != "ASSIGNED" or not inc.assigned_vehicle_id:
                        continue

                    v = vehicle_map.get(inc.assigned_vehicle_id)
                    if not v:
                        continue

                    phase = getattr(inc, 'route_phase', 'TO_INCIDENT') or 'TO_INCIDENT'

                    if phase == "TO_INCIDENT":
                        try:
                            rd = json.loads(inc.route_data) if inc.route_data else {}
                            inc_idx = rd.get("incident_waypoint_idx", 0)
                            total_pts = len(rd.get("geometry", []))
                            inc_progress = inc_idx / max(total_pts - 1, 1) if total_pts > 1 else 1.0
                        except Exception:
                            inc_progress = 1.0

                        arrived = (
                            v.route_progress >= inc_progress - 0.02
                            or _dist2(v.lat, v.lon, inc.lat, inc.lon) <= ARRIVAL_DIST2
                        )
                        if arrived:
                            inc.route_phase = "AT_INCIDENT"
                            _at_incident_ticks[inc.id] = 0
                            v.speed = 0.0
                            print(f"[TWIN-ENGINE] {v.id} arrived at {inc.id}", flush=True)

                    elif phase == "AT_INCIDENT":
                        _at_incident_ticks[inc.id] = _at_incident_ticks.get(inc.id, 0) + 1

                        if _at_incident_ticks[inc.id] >= 5:  # ~7.5s at 1.5s ticks
                            del _at_incident_ticks[inc.id]
                            if inc.assigned_hospital_id:
                                inc.route_phase = "TO_HOSPITAL"
                                v.status = "EN_ROUTE"
                                v.speed = 1.0
                                print(f"[TWIN-ENGINE] {v.id} heading to hospital for {inc.id}", flush=True)
                            else:
                                self._resolve_incident(db, inc, v, self._hospital_dict, None)
                                print(f"[TWIN-ENGINE] {inc.id} resolved (no hospital)", flush=True)

                    elif phase == "TO_HOSPITAL":
                        arrived = v.route_progress >= 0.95
                        if not arrived and inc.assigned_hospital_id:
                            hd = self._get_hospital(inc.assigned_hospital_id)
                            if hd and _dist2(v.lat, v.lon, hd["lat"], hd["lon"]) <= ARRIVAL_DIST2:
                                arrived = True

                        if arrived:
                            if inc.assigned_hospital_id:
                                hosp = db.query(Hospital).get(inc.assigned_hospital_id)
                                if hosp:
                                    hosp.current_load = min(hosp.capacity, hosp.current_load + (inc.affected_count or 1))
                            self._resolve_incident(db, inc, v, self._hospital_dict, None)
                            print(f"[TWIN-ENGINE] {inc.id} RESOLVED (hospital={inc.assigned_hospital_id})", flush=True)

                db.commit()

                # Count idle vehicles (computed inline, no extra iteration)
                idle_count = sum(1 for v in vehicles if v.status == "IDLE" and v.enabled)
                available_vehicles_count.set(idle_count)

                # Telemetry (best-effort)
                try:
                    record_telemetry_tick(vehicles)
                except Exception:
                    pass

                # ── 4) WebSocket broadcast ──────────────────────────────
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
                    "fleet_metrics": {
                        "active_vehicles": len(vehicles) - idle_count,
                        "avg_fuel": round(sum(v.fuel for v in vehicles) / max(len(vehicles), 1), 2),
                    },
                    "alerts": [],
                }

            except Exception as e:
                db.rollback()
                import traceback
                print(f"[TWIN-ENGINE] ERROR: {e}", flush=True)
                traceback.print_exc()
                payload = {"ts": time.time(), "vehicles": [], "incidents": [], "fleet_metrics": {}, "alerts": []}
            finally:
                db.close()

            try:
                await self.ws.broadcast_json(payload)
            except Exception:
                pass  # WS broadcast is best-effort

            elapsed_ms = (time.time() - t0) * 1000
            await asyncio.sleep(max(0.0, (TICK_MS - elapsed_ms) / 1000))
