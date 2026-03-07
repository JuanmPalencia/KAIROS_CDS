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
import traceback
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


# ── OSRM route cache (avoid repeated API calls for similar routes) ───
_osrm_cache: dict[str, tuple] = {}
_OSRM_CACHE_MAX = 200


def _osrm_cache_key(lat1, lon1, lat2, lon2, precision=4):
    """Cache key rounded to ~11m precision (4 decimals)."""
    return f"{round(lat1,precision)},{round(lon1,precision)}-{round(lat2,precision)},{round(lon2,precision)}"


def _osrm_route(start_lat, start_lon, end_lat, end_lon, max_points=250):
    """Fetch real road route from OSRM public API with retry + cache.
    Returns (list of [lat, lon], distance_km) or (None, None)."""
    import urllib.request

    # Check cache first
    cache_key = _osrm_cache_key(start_lat, start_lon, end_lat, end_lon)
    if cache_key in _osrm_cache:
        return _osrm_cache[cache_key]

    url = (
        f"http://router.project-osrm.org/route/v1/driving/"
        f"{start_lon},{start_lat};{end_lon},{end_lat}"
        f"?overview=full&geometries=geojson"
    )

    for attempt in range(2):  # 2 attempts
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "KAIROS-CDS/1.0"})
            timeout = 8 if attempt == 0 else 12  # OSRM from Docker takes 3-6s typically
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read())

            if data.get("code") != "Ok" or not data.get("routes"):
                logger.warning(f"[OSRM] No route found: {data.get('message', 'unknown')}")
                return None, None

            coords = data["routes"][0]["geometry"]["coordinates"]  # [lon, lat] pairs
            distance_m = data["routes"][0]["distance"]

            # Downsample only if very large (keep detail for Madrid streets)
            if len(coords) > max_points:
                step = len(coords) / max_points
                coords = [coords[int(i * step)] for i in range(max_points)] + [coords[-1]]

            # Convert [lon, lat] → [lat, lon]
            result = ([[c[1], c[0]] for c in coords], distance_m / 1000.0)

            # Cache result (evict if full)
            if len(_osrm_cache) >= _OSRM_CACHE_MAX:
                keys = list(_osrm_cache.keys())
                for k in keys[:len(keys) // 4]:
                    del _osrm_cache[k]
            _osrm_cache[cache_key] = result

            logger.info(f"[OSRM] Route OK: {len(result[0])} pts, {result[1]:.1f} km")
            return result

        except Exception as e:
            if attempt == 0:
                logger.warning(f"[OSRM] Attempt 1 failed ({e}), retrying...")
            else:
                logger.warning(f"[OSRM] Both attempts failed ({e}), using fallback")

    return None, None


def _build_street_route(start_lat, start_lon, end_lat, end_lon, n_points=20):
    """Fallback: simulate Madrid-style route with multiple turns.
    Uses 2-3 intermediate waypoints offset from the straight line
    to mimic real street navigation through a radial city layout."""
    pts = []
    dlat = end_lat - start_lat
    dlon = end_lon - start_lon

    # Create 2-3 intermediate waypoints with lateral offsets
    # simulating turns through Madrid's mix of radial/grid streets
    random.seed(int((start_lat + end_lat) * 10000))  # deterministic per route
    num_turns = 2 if abs(dlat) + abs(dlon) < 0.02 else 3  # fewer turns for short routes

    waypoints = [(start_lat, start_lon)]
    for i in range(1, num_turns + 1):
        t = i / (num_turns + 1)
        # Base position along straight line
        base_lat = start_lat + dlat * t
        base_lon = start_lon + dlon * t
        # Perpendicular offset (simulates going around blocks)
        perp_scale = 0.002 * (1 - abs(2 * t - 1))  # max offset at midpoint
        offset = random.uniform(-perp_scale, perp_scale)
        waypoints.append((
            base_lat + offset * (-dlon / max(abs(dlon) + abs(dlat), 0.0001)),
            base_lon + offset * (dlat / max(abs(dlon) + abs(dlat), 0.0001)),
        ))
    waypoints.append((end_lat, end_lon))

    # Interpolate smoothly between waypoints
    pts_per_segment = n_points // len(waypoints)
    for i in range(len(waypoints) - 1):
        lat1, lon1 = waypoints[i]
        lat2, lon2 = waypoints[i + 1]
        for j in range(pts_per_segment):
            t = j / pts_per_segment
            pts.append([lat1 + (lat2 - lat1) * t, lon1 + (lon2 - lon1) * t])
    pts.append([end_lat, end_lon])

    logger.info(f"[ROUTE-FALLBACK] Generated {len(pts)}-point fallback route")
    return pts


def _build_route(start_lat, start_lon, end_lat, end_lon):
    """Try OSRM first, fallback to street-like route. Returns (waypoints, distance_km)."""
    pts, dist_km = _osrm_route(start_lat, start_lon, end_lat, end_lon)
    if pts and len(pts) >= 2:
        return pts, dist_km
    # Fallback
    pts = _build_street_route(start_lat, start_lon, end_lat, end_lon)
    dist_km = _haversine_km(start_lat, start_lon, end_lat, end_lon) * 1.4  # ~40% longer for streets
    return pts, dist_km


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
            hosp = db.get(Hospital, inc.assigned_hospital_id)
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
        logger.info("[TWIN-ENGINE] Started (TICK_MS=%d)", TICK_MS)

        # On startup, resolve ALL stale incidents and reset vehicles
        _cleanup_db = SessionLocal()
        try:
            from ..storage.models_sql import IncidentSQL as _Inc, Vehicle as _Veh
            _stale = _cleanup_db.query(_Inc).filter(_Inc.status.in_(["OPEN", "ASSIGNED"])).all()
            if _stale:
                for _s in _stale:
                    _s.status = "RESOLVED"
                # Reset any non-IDLE vehicles back to IDLE
                _stuck_vehicles = _cleanup_db.query(_Veh).filter(_Veh.status != "IDLE").all()
                for _sv in _stuck_vehicles:
                    _sv.status = "IDLE"
                    _sv.speed = 0.0
                    _sv.route_progress = 0.0
                _cleanup_db.commit()
                logger.info("[TWIN-ENGINE] Cleaned %d stale incidents + %d stuck vehicles on startup",
                            len(_stale), len(_stuck_vehicles))
        except Exception as _e:
            logger.warning("[TWIN-ENGINE] Cleanup warning: %s", _e)
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

                    # Build road route (OSRM → fallback to street-like)
                    waypoints, dist_ab = _build_route(best.lat, best.lon, inc.lat, inc.lon)
                    total_km = dist_ab or _haversine_km(best.lat, best.lon, inc.lat, inc.lon)
                    incident_idx = len(waypoints) - 1

                    if nearest_hosp:
                        leg_bc, dist_bc = _build_route(inc.lat, inc.lon, nearest_hosp.lat, nearest_hosp.lon)
                        waypoints.extend(leg_bc[1:])
                        total_km += dist_bc or _haversine_km(inc.lat, inc.lon, nearest_hosp.lat, nearest_hosp.lon)

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
                            logger.info("[TWIN-ENGINE] %s arrived at %s", v.id, inc.id)

                    elif phase == "AT_INCIDENT":
                        _at_incident_ticks[inc.id] = _at_incident_ticks.get(inc.id, 0) + 1

                        if _at_incident_ticks[inc.id] >= 12:  # ~18s at 1.5s ticks (quick on-scene assessment)
                            del _at_incident_ticks[inc.id]
                            if inc.assigned_hospital_id:
                                inc.route_phase = "TO_HOSPITAL"
                                v.status = "EN_ROUTE"
                                v.speed = 1.0
                                logger.info("[TWIN-ENGINE] %s heading to hospital for %s", v.id, inc.id)
                            else:
                                self._resolve_incident(db, inc, v, self._hospital_dict, None)
                                logger.info("[TWIN-ENGINE] %s resolved (no hospital)", inc.id)

                    elif phase == "TO_HOSPITAL":
                        arrived = v.route_progress >= 0.95
                        if not arrived and inc.assigned_hospital_id:
                            hd = self._get_hospital(inc.assigned_hospital_id)
                            if hd and _dist2(v.lat, v.lon, hd["lat"], hd["lon"]) <= ARRIVAL_DIST2:
                                arrived = True

                        if arrived:
                            if inc.assigned_hospital_id:
                                hosp = db.get(Hospital, inc.assigned_hospital_id)
                                if hosp:
                                    hosp.current_load = min(hosp.capacity, hosp.current_load + (inc.affected_count or 1))
                            self._resolve_incident(db, inc, v, self._hospital_dict, None)
                            logger.info("[TWIN-ENGINE] %s RESOLVED (hospital=%s)", inc.id, inc.assigned_hospital_id)

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
                logger.error("[TWIN-ENGINE] ERROR: %s\n%s", e, traceback.format_exc())
                payload = {"ts": time.time(), "vehicles": [], "incidents": [], "fleet_metrics": {}, "alerts": []}
            finally:
                db.close()

            try:
                await self.ws.broadcast_json(payload)
            except Exception:
                pass  # WS broadcast is best-effort

            elapsed_ms = (time.time() - t0) * 1000
            await asyncio.sleep(max(0.0, (TICK_MS - elapsed_ms) / 1000))
