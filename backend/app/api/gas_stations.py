"""API de Gasolineras / Estaciones de Combustible para KAIROS CDS."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import json, math

from ..storage.db import get_db
from ..storage.models_sql import GasStation, Vehicle
from ..auth.dependencies import get_current_user, User, require_role

router = APIRouter(prefix="/api/gas-stations", tags=["gas-stations"])


# ── Schemas ───────────────────────────────────────────────────────────
class GasStationCreate(BaseModel):
    id: str
    name: str
    brand: Optional[str] = None
    address: Optional[str] = None
    lat: float
    lon: float
    fuel_types: Optional[List[str]] = None
    price_per_liter: float = 1.65
    is_open: bool = True
    open_24h: bool = False


class GasStationResponse(BaseModel):
    id: str
    name: str
    brand: Optional[str]
    address: Optional[str]
    lat: float
    lon: float
    fuel_types: Optional[List[str]]
    price_per_liter: float
    is_open: bool
    open_24h: bool

    class Config:
        from_attributes = True


# ── Endpoints ─────────────────────────────────────────────────────────
@router.get("/", response_model=List[GasStationResponse])
async def list_gas_stations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lista todas las gasolineras."""
    stations = db.query(GasStation).filter(GasStation.is_open == True).all()
    result = []
    for s in stations:
        ft = json.loads(s.fuel_types) if s.fuel_types else ["diesel", "gasolina95"]
        result.append(GasStationResponse(
            id=s.id, name=s.name, brand=s.brand, address=s.address,
            lat=s.lat, lon=s.lon, fuel_types=ft,
            price_per_liter=s.price_per_liter, is_open=s.is_open,
            open_24h=s.open_24h,
        ))
    return result


@router.post("/", response_model=GasStationResponse)
async def create_gas_station(
    data: GasStationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"])),
):
    """Crear una gasolinera (solo ADMIN)."""
    if db.query(GasStation).filter(GasStation.id == data.id).first():
        raise HTTPException(400, "Gas station ID already exists")

    gs = GasStation(
        id=data.id, name=data.name, brand=data.brand,
        address=data.address, lat=data.lat, lon=data.lon,
        fuel_types=json.dumps(data.fuel_types) if data.fuel_types else None,
        price_per_liter=data.price_per_liter, is_open=data.is_open,
        open_24h=data.open_24h,
    )
    db.add(gs)
    db.commit()
    db.refresh(gs)

    ft = json.loads(gs.fuel_types) if gs.fuel_types else ["diesel", "gasolina95"]
    return GasStationResponse(
        id=gs.id, name=gs.name, brand=gs.brand, address=gs.address,
        lat=gs.lat, lon=gs.lon, fuel_types=ft,
        price_per_liter=gs.price_per_liter, is_open=gs.is_open,
        open_24h=gs.open_24h,
    )


@router.post("/seed")
async def seed_gas_stations(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"])),
):
    """Poblar gasolineras reales de Madrid."""
    stations = [
        {"id": "GAS-001", "name": "Repsol Paseo de la Castellana",     "brand": "Repsol",  "address": "Paseo de la Castellana 200, Madrid",      "lat": 40.4620, "lon": -3.6883, "open_24h": True,  "price": 1.59},
        {"id": "GAS-002", "name": "Cepsa Avenida de América",          "brand": "Cepsa",   "address": "Av. de América 37, Madrid",               "lat": 40.4364, "lon": -3.6704, "open_24h": True,  "price": 1.62},
        {"id": "GAS-003", "name": "BP Gran Vía de Hortaleza",          "brand": "BP",      "address": "Gran Vía de Hortaleza 65, Madrid",        "lat": 40.4725, "lon": -3.6550, "open_24h": False, "price": 1.68},
        {"id": "GAS-004", "name": "Galp Avenida de la Albufera",       "brand": "Galp",    "address": "Av. de la Albufera 100, Madrid",          "lat": 40.3920, "lon": -3.6590, "open_24h": False, "price": 1.55},
        {"id": "GAS-005", "name": "Shell Calle de Alcalá",             "brand": "Shell",   "address": "Calle de Alcalá 500, Madrid",             "lat": 40.4350, "lon": -3.6100, "open_24h": True,  "price": 1.72},
        {"id": "GAS-006", "name": "Repsol Avenida del Mediterráneo",   "brand": "Repsol",  "address": "Av. del Mediterráneo 15, Madrid",         "lat": 40.4060, "lon": -3.6720, "open_24h": True,  "price": 1.58},
        {"id": "GAS-007", "name": "Cepsa Calle de Bravo Murillo",      "brand": "Cepsa",   "address": "Calle de Bravo Murillo 300, Madrid",      "lat": 40.4580, "lon": -3.6980, "open_24h": False, "price": 1.63},
        {"id": "GAS-008", "name": "Petroprix Carabanchel",             "brand": "Petroprix", "address": "Calle de Antonio Leyva 32, Madrid",     "lat": 40.3870, "lon": -3.7310, "open_24h": False, "price": 1.49},
    ]

    created = []
    for s in stations:
        existing = db.query(GasStation).filter(GasStation.id == s["id"]).first()
        gs = GasStation(
            id=s["id"], name=s["name"], brand=s["brand"],
            address=s["address"], lat=s["lat"], lon=s["lon"],
            fuel_types=json.dumps(["diesel", "gasolina95", "gasolina98"]),
            price_per_liter=s["price"], is_open=True, open_24h=s["open_24h"],
        )
        db.merge(gs)
        created.append(s["id"])

    db.commit()
    return {"ok": True, "created": created, "count": len(created)}


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distancia Haversine en km."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@router.post("/refuel/{vehicle_id}")
async def refuel_vehicle(
    vehicle_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"])),
):
    """Repostar un vehículo en la gasolinera más cercana.

    El vehículo debe:
    - Estar en estado IDLE
    - Estar a menos de 2 km de una gasolinera abierta
    """
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(404, "Vehicle not found")

    if vehicle.status != "IDLE":
        raise HTTPException(400, "Vehicle must be IDLE to refuel")

    # Buscar la gasolinera más cercana abierta
    stations = db.query(GasStation).filter(GasStation.is_open == True).all()
    if not stations:
        raise HTTPException(404, "No open gas stations available")

    best = None
    best_dist = float("inf")
    for s in stations:
        d = _haversine_km(vehicle.lat, vehicle.lon, s.lat, s.lon)
        if d < best_dist:
            best_dist = d
            best = s

    MAX_REFUEL_DISTANCE_KM = 2.0
    if best_dist > MAX_REFUEL_DISTANCE_KM:
        raise HTTPException(
            400,
            f"Nearest station '{best.name}' is {best_dist:.1f} km away (max {MAX_REFUEL_DISTANCE_KM} km). "
            f"Move the vehicle closer first.",
        )

    # Calcular recarga
    old_fuel = vehicle.fuel
    liters_needed = (100.0 - old_fuel)  # Lo que falta para llenar
    cost = liters_needed * best.price_per_liter

    vehicle.fuel = 100.0
    db.commit()

    return {
        "vehicle_id": vehicle.id,
        "station_id": best.id,
        "station_name": best.name,
        "old_fuel": round(old_fuel, 1),
        "new_fuel": 100.0,
        "liters_refueled": round(liters_needed, 1),
        "cost_euros": round(cost, 2),
        "distance_km": round(best_dist, 2),
    }


@router.get("/nearest/{vehicle_id}")
async def nearest_station(
    vehicle_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Obtener la gasolinera más cercana a un vehículo."""
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(404, "Vehicle not found")

    stations = db.query(GasStation).filter(GasStation.is_open == True).all()
    if not stations:
        return {"nearest": None}

    ranked = []
    for s in stations:
        d = _haversine_km(vehicle.lat, vehicle.lon, s.lat, s.lon)
        ft = json.loads(s.fuel_types) if s.fuel_types else ["diesel"]
        ranked.append({
            "id": s.id, "name": s.name, "brand": s.brand,
            "lat": s.lat, "lon": s.lon,
            "distance_km": round(d, 2),
            "price_per_liter": s.price_per_liter,
            "open_24h": s.open_24h,
        })

    ranked.sort(key=lambda x: x["distance_km"])
    return {"vehicle_id": vehicle.id, "stations": ranked[:5]}
