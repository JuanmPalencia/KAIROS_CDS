import asyncio
import os
import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from starlette.websockets import WebSocketDisconnect
from starlette.middleware.base import BaseHTTPMiddleware

from .storage.db import engine, Base, get_db
from .realtime.ws import WSManager
from .core.twin_engine import TwinEngine
from .api.health import router as health_router
from .api.fleet import router as fleet_router
from .api.events import router as events_router
from .api.auth import router as auth_router
from .api.analytics import router as analytics_router
from .api.alerts import router as alerts_router
from .api.hospitals import router as hospitals_router
from .api.assignments import router as assignments_router
from .api.ai import router as ai_router
from .api.audit import router as audit_router
from .api.blockchain import router as blockchain_router
from .api.gas_stations import router as gas_stations_router
from .api.simulation import router as simulation_router
from .api.kpis import router as kpis_router
from .api.crews import router as crews_router
from .api.epcr import router as epcr_router
from .api.mci import router as mci_router
from .api.resources import router as resources_router
from .api.chat import router as chat_router
from .api.security import router as security_router
from .api.digital_twin import router as digital_twin_router
from .core.cybersecurity import SecurityMiddleware, SecurityHeadersMiddleware
from .core.metrics import (
    metrics_endpoint,
    http_requests_total,
    http_request_duration_seconds,
    database_connections_active
)

logger = logging.getLogger(__name__)


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting up...")
    try:
        Base.metadata.create_all(bind=engine)
        database_connections_active.set(1)
    except Exception as e:
        logger.warning(f"DB init skipped (test mode or DB offline): {e}")
    
    # Start twin engine
    engine_task = asyncio.create_task(twin_engine.run())
    logger.info("✅ TwinEngine started")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down...")
    twin_engine.running = False
    engine_task.cancel()
    database_connections_active.set(0)
    logger.info("✅ Shutdown complete")


app = FastAPI(
    title="KAIROS CDS - Digital Twin",
    version="1.0.0",
    description="Digital Twin for Emergency Fleet Management — KAIROS CDS",
    lifespan=lifespan
)


# Metrics middleware
class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        duration = time.time() - start_time
        http_requests_total.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        http_request_duration_seconds.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
        
        return response


app.add_middleware(MetricsMiddleware)

# Security middleware stack
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(SecurityMiddleware)

# CORS — MUST be last (outermost) so preflight OPTIONS are handled
# before any security middleware can block them
_cors_origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:3000",
]
# Add origins from CORS_ORIGINS env var (comma-separated)
import os as _os
_extra = _os.getenv("CORS_ORIGINS", "")
if _extra:
    _cors_origins.extend([o.strip() for o in _extra.split(",") if o.strip()])
logger.info(f"CORS allowed origins: {_cors_origins}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-CSRF-Token", "X-Request-ID"],
    expose_headers=["X-Request-ID", "Retry-After", "X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
)


ws_manager = WSManager()
twin_engine = TwinEngine(ws_manager)


@app.get("/")
def root():
    return {
        "service": "KAIROS CDS - Digital Twin",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return metrics_endpoint()


@app.get("/api/cities")
def get_cities(db: Session = Depends(get_db)):
    """Get distinct cities from incidents and hospitals."""
    from .storage.models_sql import IncidentSQL, Hospital
    inc_cities = db.query(IncidentSQL.city).filter(IncidentSQL.city.isnot(None)).distinct().all()
    hosp_cities = db.query(Hospital.city).filter(Hospital.city.isnot(None)).distinct().all()
    all_cities = sorted(set(c[0] for c in inc_cities + hosp_cities if c[0]))
    return {"cities": all_cities}


# ── /api/live cache (avoid 7 DB queries per poll per user) ──────────
_live_cache = {"data": None, "ts": 0, "city": None}
_LIVE_CACHE_TTL = 2.0  # seconds


@app.get("/api/live")
def get_live_data(city: str = None, db: Session = Depends(get_db)):
    """Get current live data with 2s in-memory cache."""
    from .storage.models_sql import Vehicle, IncidentSQL, GasStation, WeatherCondition, DEALocation, AgencyResource, Hospital
    import json as _json

    # Return cached if fresh
    now = time.time()
    if _live_cache["data"] and (now - _live_cache["ts"]) < _LIVE_CACHE_TTL and _live_cache["city"] == city:
        return _live_cache["data"]

    try:
        vehicles = db.query(Vehicle).all()
        inc_query = db.query(IncidentSQL).filter(IncidentSQL.status != "RESOLVED")
        if city:
            inc_query = inc_query.filter(IncidentSQL.city == city)
        incidents = inc_query.all()

        # Single pass for vehicle metrics + progress map
        vehicle_progress_map = {}
        active = 0
        total_fuel = 0.0
        enabled_count = 0
        for v in vehicles:
            vehicle_progress_map[v.id] = v.route_progress
            if v.enabled:
                enabled_count += 1
                total_fuel += v.fuel
                if v.status != "IDLE":
                    active += 1

        avg_fuel = total_fuel / enabled_count if enabled_count else 0

        # Batch remaining queries (3 queries instead of 5)
        gas_stations = db.query(GasStation).filter(GasStation.is_open == True).all()
        hospitals = db.query(Hospital).filter(Hospital.available == True).all()
        weather = db.query(WeatherCondition).order_by(WeatherCondition.timestamp.desc()).first()

        # Lightweight counts
        dispatched_agencies = db.query(AgencyResource).filter(
            AgencyResource.status.in_(["DISPATCHED", "ON_SCENE"])
        ).count()
        dea_count = db.query(DEALocation).filter(DEALocation.is_available == True).count()

        weather_data = None
        if weather:
            weather_data = {
                "condition": weather.condition,
                "temperature_c": weather.temperature_c,
                "eta_multiplier": weather.eta_multiplier,
                "alert_level": weather.alert_level,
                "description": weather.description,
            }

        payload = {
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
                    "tank_capacity": getattr(v, "tank_capacity", 80.0),
                    "trust_score": v.trust_score,
                    "enabled": v.enabled,
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
                    "incident_type": i.incident_type,
                    "route_data": i.route_data,
                    "description": i.description,
                    "address": i.address,
                    "city": i.city,
                    "affected_count": i.affected_count,
                    "route_phase": getattr(i, 'route_phase', None),
                    "route_progress": vehicle_progress_map.get(i.assigned_vehicle_id, 0.0) if i.assigned_vehicle_id else 0.0,
                    "created_at": i.created_at.isoformat() if i.created_at else None,
                }
                for i in incidents
            ],
            "fleet_metrics": {
                "active_vehicles": active,
                "avg_fuel": round(avg_fuel, 1),
                "dispatched_agencies": dispatched_agencies,
                "dea_available": dea_count,
            },
            "gas_stations": [
                {
                    "id": gs.id,
                    "name": gs.name,
                    "brand": gs.brand,
                    "lat": gs.lat,
                    "lon": gs.lon,
                    "price_per_liter": gs.price_per_liter,
                    "is_open": gs.is_open,
                    "open_24h": gs.open_24h,
                    "fuel_types": _json.loads(gs.fuel_types) if gs.fuel_types else ["diesel"],
                }
                for gs in gas_stations
            ],
            "hospitals": [
                {
                    "id": h.id,
                    "name": h.name,
                    "lat": h.lat,
                    "lon": h.lon,
                    "capacity": h.capacity,
                    "current_load": h.current_load,
                    "availability_pct": round((1 - h.current_load / h.capacity) * 100, 1) if h.capacity else 100,
                    "emergency_level": h.emergency_level,
                    "specialties": _json.loads(h.specialties) if h.specialties else [],
                }
                for h in hospitals
            ],
            "weather": weather_data,
        }

        # Update cache
        _live_cache["data"] = payload
        _live_cache["ts"] = now
        _live_cache["city"] = city

        return payload
    except Exception as e:
        logger.error(f"ERROR in /api/live: {e}", exc_info=True)
        return {"error": str(e), "vehicles": [], "incidents": [], "fleet_metrics": {"active_vehicles": 0, "avg_fuel": 0}}


@app.websocket("/ws/live")
async def ws_live(ws: WebSocket):
    logger.debug("WS: incoming connection")
    await ws_manager.connect(ws)
    logger.debug("WS: accepted")
    try:
        # Mantener vivo sin exigir mensajes del cliente
        while True:
            await asyncio.sleep(30)
    except WebSocketDisconnect:
        logger.debug("WS: disconnect")
    except Exception as e:
        logger.warning("WS: error %r", e)
    finally:
        ws_manager.disconnect(ws)
        logger.debug("WS: cleaned up")


# Routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(fleet_router)
app.include_router(events_router)
app.include_router(analytics_router)
app.include_router(alerts_router)
app.include_router(hospitals_router)
app.include_router(assignments_router)
app.include_router(ai_router)
app.include_router(audit_router)
app.include_router(blockchain_router)
app.include_router(gas_stations_router)
app.include_router(simulation_router)
app.include_router(kpis_router)
app.include_router(crews_router)
app.include_router(epcr_router)
app.include_router(mci_router)
app.include_router(resources_router)
app.include_router(chat_router)
app.include_router(security_router)
app.include_router(digital_twin_router)

