"""DEA (Desfibriladores), GIS Layers, First Responders, Weather, Multi-Agency, SSM, Hospital Dashboard."""
import random
import math
import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from ..storage.db import get_db
from ..storage.models_sql import (
    DEALocation, FirstResponder, WeatherCondition, GISLayer,
    AgencyResource, Vehicle, IncidentSQL, Hospital, PatientTracking
)

router = APIRouter(prefix="/api/resources", tags=["resources"])


# ══════════════════════════════════════════════
# DEA Locations — Desfibriladores Externos
# ══════════════════════════════════════════════

DEA_SEED = [
    {"id": "DEA-001", "name": "Metro Sol", "lat": 40.4169, "lon": -3.7035, "address": "Puerta del Sol, s/n", "location_type": "TRANSPORT", "access_hours": "06:00-01:30"},
    {"id": "DEA-002", "name": "Centro Comercial Gran Vía", "lat": 40.4200, "lon": -3.7058, "address": "Gran Vía 32", "location_type": "PUBLIC", "access_hours": "10:00-22:00"},
    {"id": "DEA-003", "name": "Estación Atocha", "lat": 40.4065, "lon": -3.6893, "address": "Pza. Emperador Carlos V", "location_type": "TRANSPORT", "access_hours": "24h"},
    {"id": "DEA-004", "name": "Polideportivo La Latina", "lat": 40.4115, "lon": -3.7120, "address": "C/ Toledo 68", "location_type": "PUBLIC", "access_hours": "08:00-22:00"},
    {"id": "DEA-005", "name": "Centro Cultural Conde Duque", "lat": 40.4280, "lon": -3.7135, "address": "C/ Conde Duque 11", "location_type": "PUBLIC", "access_hours": "09:00-21:00"},
    {"id": "DEA-006", "name": "Estadio Santiago Bernabéu", "lat": 40.4530, "lon": -3.6883, "address": "Av. Concha Espina 1", "location_type": "PUBLIC", "access_hours": "Según evento"},
    {"id": "DEA-007", "name": "Metro Nuevos Ministerios", "lat": 40.4460, "lon": -3.6920, "address": "Paseo de la Castellana 67", "location_type": "TRANSPORT", "access_hours": "06:00-01:30"},
    {"id": "DEA-008", "name": "Hospital La Paz (Acceso exterior)", "lat": 40.4815, "lon": -3.6870, "address": "Paseo de la Castellana 261", "location_type": "PUBLIC", "access_hours": "24h"},
    {"id": "DEA-009", "name": "Parque del Retiro - Entrada Alcalá", "lat": 40.4195, "lon": -3.6835, "address": "Pza. Independencia", "location_type": "PUBLIC", "access_hours": "06:00-24:00"},
    {"id": "DEA-010", "name": "Aeropuerto T4", "lat": 40.4719, "lon": -3.5614, "address": "T4 Barajas", "location_type": "TRANSPORT", "access_hours": "24h"},
    {"id": "DEA-011", "name": "Mercado de San Miguel", "lat": 40.4154, "lon": -3.7092, "address": "Pza. San Miguel", "location_type": "PUBLIC", "access_hours": "10:00-24:00"},
    {"id": "DEA-012", "name": "Colegio SEK El Castillo", "lat": 40.3920, "lon": -3.7220, "address": "Castillo de Manzanares", "location_type": "PRIVATE", "access_hours": "08:00-17:00"},
]


@router.post("/dea/seed")
def seed_dea(db: Session = Depends(get_db)):
    created = 0
    for d in DEA_SEED:
        if not db.query(DEALocation).filter(DEALocation.id == d["id"]).first():
            db.add(DEALocation(**d))
            created += 1
    db.commit()
    return {"ok": True, "created": created}


@router.get("/dea")
def list_dea(db: Session = Depends(get_db)):
    deas = db.query(DEALocation).filter(DEALocation.is_available == True).all()
    return [
        {
            "id": d.id, "name": d.name, "lat": d.lat, "lon": d.lon,
            "address": d.address, "location_type": d.location_type,
            "access_hours": d.access_hours, "is_available": d.is_available,
        }
        for d in deas
    ]


@router.get("/dea/nearest")
def nearest_dea(lat: float, lon: float, db: Session = Depends(get_db)):
    """Encontrar DEA más cercanos a una coordenada."""
    deas = db.query(DEALocation).filter(DEALocation.is_available == True).all()
    if not deas:
        return []

    def dist(d):
        return math.sqrt((d.lat - lat) ** 2 + (d.lon - lon) ** 2)

    sorted_deas = sorted(deas, key=dist)[:5]
    return [
        {
            "id": d.id, "name": d.name, "lat": d.lat, "lon": d.lon,
            "address": d.address, "distance_approx_km": round(dist(d) * 111, 2),
            "access_hours": d.access_hours,
        }
        for d in sorted_deas
    ]


# ══════════════════════════════════════════════
# First Responders — Voluntarios SVB/DEA
# ══════════════════════════════════════════════

FIRST_RESPONDER_SEED = [
    {"id": "FR-001", "name": "Marta del Río", "phone": "+34 600 100 001", "certification": "SVB_DEA", "lat": 40.4178, "lon": -3.7040},
    {"id": "FR-002", "name": "Pablo Jiménez", "phone": "+34 600 100 002", "certification": "SVB_DEA", "lat": 40.4250, "lon": -3.7100},
    {"id": "FR-003", "name": "Carmen Vega", "phone": "+34 600 100 003", "certification": "DESA", "lat": 40.4350, "lon": -3.6950},
    {"id": "FR-004", "name": "Raúl Soto", "phone": "+34 600 100 004", "certification": "RCP", "lat": 40.4090, "lon": -3.6880},
    {"id": "FR-005", "name": "Isabel Campos", "phone": "+34 600 100 005", "certification": "SVB_DEA", "lat": 40.4450, "lon": -3.6920},
    {"id": "FR-006", "name": "David Blanco", "phone": "+34 600 100 006", "certification": "SVB_DEA", "lat": 40.4600, "lon": -3.7000},
]


@router.post("/first-responders/seed")
def seed_first_responders(db: Session = Depends(get_db)):
    created = 0
    for fr in FIRST_RESPONDER_SEED:
        if not db.query(FirstResponder).filter(FirstResponder.id == fr["id"]).first():
            db.add(FirstResponder(**fr))
            created += 1
    db.commit()
    return {"ok": True, "created": created}


@router.get("/first-responders")
def list_first_responders(db: Session = Depends(get_db)):
    frs = db.query(FirstResponder).filter(FirstResponder.is_available == True).all()
    return [
        {"id": f.id, "name": f.name, "certification": f.certification,
         "lat": f.lat, "lon": f.lon, "alerts_responded": f.alerts_responded}
        for f in frs
    ]


@router.get("/first-responders/alert")
def alert_nearby_responders(lat: float, lon: float, radius_km: float = 1.0,
                             db: Session = Depends(get_db)):
    """Alertar a first responders cercanos a un incidente cardíaco."""
    frs = db.query(FirstResponder).filter(FirstResponder.is_available == True).all()
    nearby = []
    for f in frs:
        if f.lat and f.lon:
            d = math.sqrt((f.lat - lat) ** 2 + (f.lon - lon) ** 2) * 111
            if d <= radius_km:
                nearby.append({
                    "id": f.id, "name": f.name, "phone": f.phone,
                    "certification": f.certification,
                    "distance_km": round(d, 2),
                    "eta_minutes": round(d / 5 * 60, 0),  # ~5 km/h walking
                })
    return {"alerted": len(nearby), "responders": sorted(nearby, key=lambda x: x["distance_km"])}


# ══════════════════════════════════════════════
# Weather Conditions — Tiempo real via Open-Meteo (gratis, sin API key)
# ══════════════════════════════════════════════

# WMO Weather interpretation codes → condition name + alert level + ETA multiplier
WMO_MAP = {
    0:  ("CLEAR",      "GREEN",  1.0),
    1:  ("CLEAR",      "GREEN",  1.0),
    2:  ("CLOUD",      "GREEN",  1.0),
    3:  ("CLOUD",      "GREEN",  1.0),
    45: ("FOG",        "ORANGE", 1.6),
    48: ("FOG",        "ORANGE", 1.6),
    51: ("RAIN",       "GREEN",  1.1),
    53: ("RAIN",       "YELLOW", 1.25),
    55: ("RAIN",       "YELLOW", 1.25),
    56: ("RAIN",       "YELLOW", 1.3),
    57: ("RAIN",       "ORANGE", 1.4),
    61: ("RAIN",       "YELLOW", 1.25),
    63: ("HEAVY_RAIN", "ORANGE", 1.5),
    65: ("HEAVY_RAIN", "RED",    1.7),
    66: ("RAIN",       "ORANGE", 1.5),
    67: ("HEAVY_RAIN", "RED",    1.7),
    71: ("SNOW",       "YELLOW", 1.5),
    73: ("SNOW",       "ORANGE", 1.8),
    75: ("SNOW",       "RED",    2.0),
    77: ("SNOW",       "ORANGE", 1.6),
    80: ("RAIN",       "YELLOW", 1.25),
    81: ("HEAVY_RAIN", "ORANGE", 1.5),
    82: ("HEAVY_RAIN", "RED",    1.7),
    85: ("SNOW",       "ORANGE", 1.8),
    86: ("SNOW",       "RED",    2.0),
    95: ("STORM",      "RED",    1.8),
    96: ("STORM",      "RED",    1.9),
    99: ("STORM",      "RED",    2.0),
}

CONDITION_DESC = {
    "CLEAR":      "Cielo despejado",
    "CLOUD":      "Parcialmente nublado",
    "FOG":        "Niebla — Visibilidad reducida",
    "RAIN":       "Lluvia",
    "HEAVY_RAIN": "Lluvia intensa",
    "SNOW":       "Nevada",
    "STORM":      "Tormenta",
    "HEAT":       "Ola de calor",
}


@router.get("/weather/current")
async def get_current_weather(
    lat: float = Query(40.4168, description="Latitud"),
    lon: float = Query(-3.7038, description="Longitud"),
):
    """Obtener clima real para las coordenadas dadas via Open-Meteo."""
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,"
        f"weather_code,wind_speed_10m,wind_gusts_10m"
        f"&timezone=auto"
    )
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()

        cur = data.get("current", {})
        wmo_code = cur.get("weather_code", 0)
        temp = cur.get("temperature_2m", 0)
        humidity = cur.get("relative_humidity_2m", 0)
        wind = cur.get("wind_speed_10m", 0)
        gusts = cur.get("wind_gusts_10m", 0)
        apparent = cur.get("apparent_temperature", temp)

        cond, alert, mult = WMO_MAP.get(wmo_code, ("CLOUD", "GREEN", 1.0))

        # Heat detection: >38°C
        if temp >= 38 and cond == "CLEAR":
            cond, alert, mult = "HEAT", "ORANGE", 1.1

        desc = CONDITION_DESC.get(cond, cond)
        if alert != "GREEN":
            desc += f" — ETAs x{mult:.1f}"

        return {
            "condition": cond,
            "temperature_c": round(temp, 1),
            "apparent_temperature_c": round(apparent, 1),
            "humidity_pct": humidity,
            "wind_speed_kmh": round(wind, 1),
            "wind_gusts_kmh": round(gusts, 1),
            "eta_multiplier": mult,
            "alert_level": alert,
            "description": desc,
            "wmo_code": wmo_code,
            "coordinates": {"lat": lat, "lon": lon},
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        # Fallback: devolver datos estáticos si Open-Meteo falla
        return {
            "condition": "CLOUD",
            "temperature_c": 18,
            "apparent_temperature_c": 18,
            "humidity_pct": 50,
            "wind_speed_kmh": 10,
            "wind_gusts_kmh": 15,
            "eta_multiplier": 1.0,
            "alert_level": "GREEN",
            "description": f"Sin datos meteorológicos ({str(e)[:60]})",
            "wmo_code": 2,
            "coordinates": {"lat": lat, "lon": lon},
            "timestamp": datetime.utcnow().isoformat(),
        }


@router.post("/weather/simulate")
def simulate_weather(condition: Optional[str] = None, db: Session = Depends(get_db)):
    """Simular un cambio de tiempo manual (para pruebas)."""
    WEATHER_CONDITIONS = [
        {"condition": "CLEAR", "temp": 22, "humidity": 40, "wind": 10, "visibility": 15, "multiplier": 1.0, "alert": "GREEN", "desc": "Cielo despejado"},
        {"condition": "CLOUD", "temp": 18, "humidity": 55, "wind": 15, "visibility": 12, "multiplier": 1.0, "alert": "GREEN", "desc": "Parcialmente nublado"},
        {"condition": "RAIN", "temp": 14, "humidity": 80, "wind": 20, "visibility": 8, "multiplier": 1.25, "alert": "YELLOW", "desc": "Lluvia moderada"},
        {"condition": "STORM", "temp": 10, "humidity": 95, "wind": 55, "visibility": 2, "multiplier": 1.8, "alert": "RED", "desc": "Tormenta severa"},
        {"condition": "FOG", "temp": 8, "humidity": 98, "wind": 5, "visibility": 0.5, "multiplier": 1.6, "alert": "ORANGE", "desc": "Niebla densa"},
        {"condition": "SNOW", "temp": -1, "humidity": 70, "wind": 15, "visibility": 3, "multiplier": 2.0, "alert": "RED", "desc": "Nevada"},
        {"condition": "HEAT", "temp": 42, "humidity": 15, "wind": 5, "visibility": 14, "multiplier": 1.1, "alert": "ORANGE", "desc": "Ola de calor"},
    ]
    if condition:
        wc = next((w for w in WEATHER_CONDITIONS if w["condition"] == condition.upper()), None)
        if not wc:
            raise HTTPException(400, f"Unknown condition. Use: {[w['condition'] for w in WEATHER_CONDITIONS]}")
    else:
        wc = random.choice(WEATHER_CONDITIONS)

    weather = WeatherCondition(
        condition=wc["condition"],
        temperature_c=wc["temp"] + random.uniform(-2, 2),
        humidity_pct=wc["humidity"],
        wind_speed_kmh=wc["wind"] + random.uniform(-5, 5),
        visibility_km=wc["visibility"],
        eta_multiplier=wc["multiplier"],
        alert_level=wc["alert"],
        description=wc["desc"],
    )
    db.add(weather)
    db.commit()
    return {"ok": True, "weather": wc["condition"], "eta_multiplier": wc["multiplier"], "alert": wc["alert"]}


# ══════════════════════════════════════════════
# GIS Layers — Puntos de interés
# ══════════════════════════════════════════════

GIS_SEED = [
    # Colegios
    {"id": "GIS-SCH-001", "name": "CEIP Antonio Machado", "layer_type": "SCHOOL", "lat": 40.4205, "lon": -3.7110, "address": "C/ Corredera Baja 47", "risk_level": 2},
    {"id": "GIS-SCH-002", "name": "IES San Isidro", "layer_type": "SCHOOL", "lat": 40.4130, "lon": -3.7080, "address": "C/ Toledo 39", "risk_level": 2},
    {"id": "GIS-SCH-003", "name": "Colegio Santa María", "layer_type": "SCHOOL", "lat": 40.4350, "lon": -3.6895, "address": "C/ Castelló 56", "risk_level": 2},
    # Residencias de mayores
    {"id": "GIS-NH-001", "name": "Residencia DomusVi Arturo Soria", "layer_type": "NURSING_HOME", "lat": 40.4520, "lon": -3.6450, "address": "C/ Arturo Soria 287", "risk_level": 3},
    {"id": "GIS-NH-002", "name": "Residencia Orpea Madrid", "layer_type": "NURSING_HOME", "lat": 40.4380, "lon": -3.7200, "address": "C/ Princesa 25", "risk_level": 3},
    {"id": "GIS-NH-003", "name": "Centro de Mayores Puerta de Hierro", "layer_type": "NURSING_HOME", "lat": 40.4600, "lon": -3.7250, "address": "Av. Puerta de Hierro", "risk_level": 3},
    # Industria HAZMAT
    {"id": "GIS-HAZ-001", "name": "Planta Química Arganda", "layer_type": "HAZMAT", "lat": 40.3080, "lon": -3.4600, "address": "Polígono Industrial Arganda", "risk_level": 5},
    {"id": "GIS-HAZ-002", "name": "Depósito GLP Villaverde", "layer_type": "HAZMAT", "lat": 40.3500, "lon": -3.6950, "address": "Polígono Villaverde", "risk_level": 4},
    # Estaciones de metro con alta afluencia
    {"id": "GIS-MET-001", "name": "Metro Sol (Alta afluencia)", "layer_type": "METRO", "lat": 40.4168, "lon": -3.7038, "risk_level": 2},
    {"id": "GIS-MET-002", "name": "Metro Atocha Renfe", "layer_type": "METRO", "lat": 40.4065, "lon": -3.6893, "risk_level": 2},
    # Comisarías / Bomberos para multi-agencia
    {"id": "GIS-POL-001", "name": "Comisaría Centro (Policía Nacional)", "layer_type": "POLICE", "lat": 40.4180, "lon": -3.7065, "address": "C/Leganitos 19"},
    {"id": "GIS-POL-002", "name": "Policía Municipal Centro", "layer_type": "POLICE", "lat": 40.4155, "lon": -3.7095, "address": "Pza. Mayor"},
    {"id": "GIS-FIRE-001", "name": "Parque de Bomberos nº1 (Imperial)", "layer_type": "FIRE", "lat": 40.4098, "lon": -3.7145, "address": "Pza. Puerta Cerrada"},
    {"id": "GIS-FIRE-002", "name": "Parque de Bomberos nº3 (Salamanca)", "layer_type": "FIRE", "lat": 40.4320, "lon": -3.6780, "address": "C/ O'Donnell 50"},
]


@router.post("/gis/seed")
def seed_gis(db: Session = Depends(get_db)):
    created = 0
    for g in GIS_SEED:
        if not db.query(GISLayer).filter(GISLayer.id == g["id"]).first():
            db.add(GISLayer(**g))
            created += 1
    db.commit()
    return {"ok": True, "created": created}


@router.get("/gis")
def list_gis(layer_type: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(GISLayer).filter(GISLayer.is_active == True)
    if layer_type:
        q = q.filter(GISLayer.layer_type == layer_type.upper())
    layers = q.all()
    return [
        {
            "id": g.id, "name": g.name, "layer_type": g.layer_type,
            "lat": g.lat, "lon": g.lon, "address": g.address,
            "risk_level": g.risk_level,
        }
        for g in layers
    ]


# ══════════════════════════════════════════════
# Multi-Agency Resources — Bomberos, Policía
# ══════════════════════════════════════════════

AGENCY_SEED = [
    {"id": "BOM-001", "agency": "BOMBEROS", "unit_name": "BUP-1 Imperial", "unit_type": "BUP", "lat": 40.4098, "lon": -3.7145, "contact_radio": "TETRA Ch.1"},
    {"id": "BOM-002", "agency": "BOMBEROS", "unit_name": "BUP-3 Salamanca", "unit_type": "BUP", "lat": 40.4320, "lon": -3.6780, "contact_radio": "TETRA Ch.1"},
    {"id": "BOM-003", "agency": "BOMBEROS", "unit_name": "Autoescala AE-1", "unit_type": "AUTOESCALA", "lat": 40.4098, "lon": -3.7145, "contact_radio": "TETRA Ch.2"},
    {"id": "POL-001", "agency": "POLICIA_NACIONAL", "unit_name": "Patrulla Z-Centro-1", "unit_type": "PATRULLA", "lat": 40.4180, "lon": -3.7065, "contact_radio": "TETRA Ch.5"},
    {"id": "POL-002", "agency": "POLICIA_NACIONAL", "unit_name": "Patrulla Z-Centro-2", "unit_type": "PATRULLA", "lat": 40.4155, "lon": -3.7095, "contact_radio": "TETRA Ch.5"},
    {"id": "POL-003", "agency": "POLICIA_MUNICIPAL", "unit_name": "PM Tráfico Centro", "unit_type": "TRAFICO", "lat": 40.4200, "lon": -3.7050, "contact_radio": "TETRA Ch.7"},
    {"id": "PC-001", "agency": "PROTECCION_CIVIL", "unit_name": "Unidad Logística PC-1", "unit_type": "LOGISTICA", "lat": 40.4250, "lon": -3.7100, "contact_radio": "TETRA Ch.9"},
]


@router.post("/agencies/seed")
def seed_agencies(db: Session = Depends(get_db)):
    created = 0
    for a in AGENCY_SEED:
        if not db.query(AgencyResource).filter(AgencyResource.id == a["id"]).first():
            db.add(AgencyResource(**a))
            created += 1
    db.commit()
    return {"ok": True, "created": created}


@router.get("/agencies")
def list_agencies(agency: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(AgencyResource)
    if agency:
        q = q.filter(AgencyResource.agency == agency.upper())
    resources = q.all()
    return [
        {
            "id": r.id, "agency": r.agency, "unit_name": r.unit_name,
            "unit_type": r.unit_type, "status": r.status,
            "lat": r.lat, "lon": r.lon,
            "assigned_incident_id": r.assigned_incident_id,
            "contact_radio": r.contact_radio,
        }
        for r in resources
    ]


@router.post("/agencies/{resource_id}/dispatch")
def dispatch_agency_resource(resource_id: str, incident_id: str, db: Session = Depends(get_db)):
    """Despachar un recurso de otra agencia a un incidente."""
    res = db.query(AgencyResource).filter(AgencyResource.id == resource_id).first()
    if not res:
        raise HTTPException(404, "Resource not found")
    res.status = "DISPATCHED"
    res.assigned_incident_id = incident_id
    db.commit()
    return {"ok": True, "resource": resource_id, "incident": incident_id}


# ══════════════════════════════════════════════
# SSM — System Status Management (Reposicionamiento predictivo)
# ══════════════════════════════════════════════

SSM_ZONES = [
    {"zone_id": "SSM-01", "name": "Centro / Sol", "lat": 40.4168, "lon": -3.7038, "demand_weight": 0.20, "recommended_units": 2},
    {"zone_id": "SSM-02", "name": "Salamanca / Retiro", "lat": 40.4230, "lon": -3.6830, "demand_weight": 0.15, "recommended_units": 1},
    {"zone_id": "SSM-03", "name": "Chamberí / Moncloa", "lat": 40.4350, "lon": -3.7150, "demand_weight": 0.12, "recommended_units": 1},
    {"zone_id": "SSM-04", "name": "Tetuán / Castellana Norte", "lat": 40.4600, "lon": -3.6920, "demand_weight": 0.13, "recommended_units": 1},
    {"zone_id": "SSM-05", "name": "Arganzuela / Usera", "lat": 40.3950, "lon": -3.7000, "demand_weight": 0.10, "recommended_units": 1},
    {"zone_id": "SSM-06", "name": "Latina / Carabanchel", "lat": 40.3850, "lon": -3.7350, "demand_weight": 0.10, "recommended_units": 1},
    {"zone_id": "SSM-07", "name": "Ciudad Lineal / San Blas", "lat": 40.4400, "lon": -3.6500, "demand_weight": 0.10, "recommended_units": 1},
    {"zone_id": "SSM-08", "name": "Hortaleza / Barajas", "lat": 40.4700, "lon": -3.6300, "demand_weight": 0.10, "recommended_units": 1},
]


@router.get("/ssm/zones")
def get_ssm_zones(db: Session = Depends(get_db)):
    """Obtener zonas SSM con cobertura actual."""
    vehicles = db.query(Vehicle).filter(Vehicle.enabled == True, Vehicle.status == "IDLE").all()
    zones_with_coverage = []
    for z in SSM_ZONES:
        # Contar vehículos IDLE en radio de 2km de cada zona
        nearby = 0
        for v in vehicles:
            dist_km = math.sqrt((v.lat - z["lat"]) ** 2 + (v.lon - z["lon"]) ** 2) * 111
            if dist_km <= 2.0:
                nearby += 1

        zones_with_coverage.append({
            **z,
            "current_units": nearby,
            "coverage_status": "OK" if nearby >= z["recommended_units"] else "DEFICIT",
            "deficit": max(0, z["recommended_units"] - nearby),
        })

    return {
        "zones": zones_with_coverage,
        "total_deficit": sum(z["deficit"] for z in zones_with_coverage),
    }


# ══════════════════════════════════════════════
# Hospital Dashboard — Vista de hospital
# ══════════════════════════════════════════════

@router.get("/hospital-dashboard/{hospital_id}")
def hospital_dashboard(hospital_id: str, db: Session = Depends(get_db)):
    """Dashboard para un hospital: ambulancias en camino + pacientes."""
    hospital = db.query(Hospital).filter(Hospital.id == hospital_id).first()
    if not hospital:
        raise HTTPException(404, "Hospital not found")

    # Ambulancias en camino a este hospital
    incoming = db.query(IncidentSQL).filter(
        IncidentSQL.assigned_hospital_id == hospital_id,
        IncidentSQL.status.in_(["ASSIGNED", "EN_ROUTE"]),
        IncidentSQL.route_phase == "TO_HOSPITAL",
    ).all()

    incoming_ambulances = []
    for inc in incoming:
        v = db.query(Vehicle).filter(Vehicle.id == inc.assigned_vehicle_id).first() if inc.assigned_vehicle_id else None
        incoming_ambulances.append({
            "incident_id": inc.id,
            "incident_type": inc.incident_type,
            "severity": inc.severity,
            "vehicle_id": inc.assigned_vehicle_id,
            "vehicle_subtype": v.subtype if v else None,
            "eta_progress": v.route_progress if v else None,
            "affected_count": inc.affected_count,
        })

    # Pacientes en este hospital
    patients = db.query(PatientTracking).filter(
        PatientTracking.hospital_id == hospital_id,
        PatientTracking.current_phase.in_(["AT_HOSPITAL_ER", "ADMITTED"]),
    ).all()

    return {
        "hospital": {
            "id": hospital.id,
            "name": hospital.name,
            "capacity": hospital.capacity,
            "current_load": hospital.current_load,
            "occupancy_pct": round(hospital.current_load / hospital.capacity * 100, 1) if hospital.capacity > 0 else 0,
            "specialties": hospital.specialties,
            "emergency_level": hospital.emergency_level,
        },
        "incoming_ambulances": incoming_ambulances,
        "patients_in_er": [
            {
                "id": pt.id,
                "patient_name": pt.patient_name,
                "phase": pt.current_phase,
                "bed": pt.hospital_bed,
                "admission_time": pt.admission_time.isoformat() if pt.admission_time else None,
            }
            for pt in patients
        ],
    }


@router.get("/hospital-dashboard")
def all_hospitals_dashboard(db: Session = Depends(get_db)):
    """Dashboard general de todos los hospitales."""
    hospitals = db.query(Hospital).filter(Hospital.available == True).all()
    result = []
    for h in hospitals:
        incoming_count = db.query(IncidentSQL).filter(
            IncidentSQL.assigned_hospital_id == h.id,
            IncidentSQL.status.in_(["ASSIGNED", "EN_ROUTE"]),
        ).count()
        result.append({
            "id": h.id,
            "name": h.name,
            "lat": h.lat,
            "lon": h.lon,
            "capacity": h.capacity,
            "current_load": h.current_load,
            "occupancy_pct": round(h.current_load / h.capacity * 100, 1) if h.capacity > 0 else 0,
            "incoming_ambulances": incoming_count,
            "emergency_level": h.emergency_level,
            "specialties": h.specialties,
        })
    return result


# ══════════════════════════════════════════════
# Seed ALL resources in one call
# ══════════════════════════════════════════════

@router.post("/seed-all")
def seed_all_resources(db: Session = Depends(get_db)):
    """Seed DEAs, First Responders, GIS layers, Agencies, Weather."""
    results = {}
    # DEA
    c = 0
    for d in DEA_SEED:
        if not db.query(DEALocation).filter(DEALocation.id == d["id"]).first():
            db.add(DEALocation(**d))
            c += 1
    results["dea"] = c

    # First Responders
    c = 0
    for fr in FIRST_RESPONDER_SEED:
        if not db.query(FirstResponder).filter(FirstResponder.id == fr["id"]).first():
            db.add(FirstResponder(**fr))
            c += 1
    results["first_responders"] = c

    # GIS
    c = 0
    for g in GIS_SEED:
        if not db.query(GISLayer).filter(GISLayer.id == g["id"]).first():
            db.add(GISLayer(**g))
            c += 1
    results["gis_layers"] = c

    # Agencies
    c = 0
    for a in AGENCY_SEED:
        if not db.query(AgencyResource).filter(AgencyResource.id == a["id"]).first():
            db.add(AgencyResource(**a))
            c += 1
    results["agencies"] = c

    # Weather (set default CLEAR)
    if not db.query(WeatherCondition).first():
        db.add(WeatherCondition(
            condition="CLEAR", temperature_c=20, humidity_pct=40,
            wind_speed_kmh=10, visibility_km=15,
            eta_multiplier=1.0, alert_level="GREEN", description="Cielo despejado (seed)",
        ))
        results["weather"] = 1
    else:
        results["weather"] = 0

    db.commit()
    return {"ok": True, "seeded": results}
