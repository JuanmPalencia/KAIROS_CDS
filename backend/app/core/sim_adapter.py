# app/core/sim_adapter.py
"""
Simulador realista de flota de ambulancias para España.

Comportamiento real:
- Cuando IDLE: la ambulancia está PARADA en su base. No se mueve.
  Puede hacer micro-ajustes muy esporádicos (~2% de ticks) para simular
  maniobras de parking, pero básicamente speed=0.
- Cuando EN_ROUTE: sigue la ruta OSRM hacia el incidente a velocidad
  realista (35-80 km/h según subtipo y vía).
- Cuando REFUELING: parada en gasolinera, llenando el depósito. Un
  depósito real de ambulancia (70-120L) tarda ~5-8 minutos en llenar.
- Consumo de combustible: ~15-25 L/100km en movimiento (pesadas, diésel).
  En ralentí (parada con motor encendido): ~1-2 L/hora.
- Va a repostar SOLO si está IDLE y combustible < 25%.
"""

import random
import json
import math
from sqlalchemy.orm import Session
from ..storage.models_sql import Vehicle, IncidentSQL, GasStation
from .routing import get_router

# ── Estado persistente entre ticks ────────────────────────────────────
_vehicle_speeds: dict[str, float] = {}        # vel. asignada por ruta
_refueling: dict[str, int] = {}               # vid → ticks restantes
_heading_to_gas: dict[str, str] = {}          # vid → gas_station_id (camino a repostar)
_speed_multiplier: float = 1.0                # multiplicador de velocidad global

# ── Constantes realistas ──────────────────────────────────────────────
LOW_FUEL_PCT = 25.0          # % para decidir ir a repostar
REFUEL_TICKS = 16            # ~8 seg a 500ms/tick (≈5 min simulados)
TICK_SECONDS = 0.5           # cada tick del simulador = 0.5s real

# Consumo medio diésel (L/100km) según subtipo
CONSUMPTION_L100KM = {
    "SVB":  18.0,   # Sprinter / Crafter
    "SVA":  22.0,   # UCIs móviles, más pesadas
    "VIR":  12.0,   # SUV más ligero
    "VAMM": 28.0,   # Camión ligero
    "SAMU": 14.0,   # SUV médico
}

# Consumo en ralentí (L/hora) con motor encendido
IDLE_CONSUMPTION_LH = 1.5

# Velocidades máximas típicas por subtipo (km/h en emergencia)
MAX_SPEED = {
    "SVB": 80, "SVA": 75, "VIR": 100, "VAMM": 60, "SAMU": 90,
}


def get_speed_multiplier() -> float:
    return _speed_multiplier


def set_speed_multiplier(mult: float) -> float:
    global _speed_multiplier
    _speed_multiplier = max(0.5, min(20.0, mult))
    return _speed_multiplier


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _consume_fuel_driving(v: Vehicle, km: float) -> None:
    """Resta combustible por km recorrido (% del depósito)."""
    subtype = getattr(v, "subtype", "SVB")
    tank = getattr(v, "tank_capacity", 80.0) or 80.0
    l_per_100km = CONSUMPTION_L100KM.get(subtype, 18.0)
    liters_used = (km * l_per_100km) / 100.0
    pct_used = (liters_used / tank) * 100.0
    v.fuel = max(0.0, round(v.fuel - pct_used, 3))


def _consume_fuel_idle(v: Vehicle) -> None:
    """Consumo mínimo por ralentí (motor encendido esporádicamente)."""
    # Solo un 30% de los ticks IDLE tiene el motor encendido
    if random.random() > 0.30:
        return
    tank = getattr(v, "tank_capacity", 80.0) or 80.0
    hours = TICK_SECONDS / 3600.0
    liters = IDLE_CONSUMPTION_LH * hours
    pct = (liters / tank) * 100.0
    v.fuel = max(0.0, round(v.fuel - pct, 4))


class MockSimAdapter:
    """
    Simulador de movimiento realista para ambulancias españolas.

    - IDLE: parada en base, consumo mínimo de ralentí.
    - EN_ROUTE: sigue waypoints OSRM con velocidad realista.
    - REFUELING: parada en gasolinera, llenando depósito gradualmente.
    - Auto-repostaje: solo si IDLE + fuel < 25% + no tiene caso asignado.
    """

    def step(self, db: Session, vehicles: list[Vehicle],
             incidents: list[IncidentSQL]) -> None:
        gas_stations = (db.query(GasStation)
                        .filter(GasStation.is_open == True).all())

        for v in vehicles:
            if not v.enabled:
                continue

            # ① Repostando → continuar
            if v.id in _refueling:
                self._step_refueling(v)
                continue

            # ② En ruta → seguir destino
            if v.status == "EN_ROUTE":
                self._step_en_route(v, incidents)
                continue

            # ③ IDLE → verificar si necesita repostar
            #    SOLO va a repostar si NO tiene incidente asignado
            has_case = any(
                i.assigned_vehicle_id == v.id and i.status == "ASSIGNED"
                for i in incidents
            )
            if (not has_case
                    and v.fuel < LOW_FUEL_PCT
                    and gas_stations):
                self._step_go_refuel(v, gas_stations)
                continue

            # ④ IDLE normal → parada en base
            self._step_idle(v)

        db.commit()

    # ── EN_ROUTE ──────────────────────────────────────────────────────
    def _step_en_route(self, v: Vehicle,
                       incidents: list[IncidentSQL]) -> None:
        target = None
        for inc in incidents:
            if inc.assigned_vehicle_id == v.id and inc.status == "ASSIGNED":
                target = inc
                break
        if not target:
            return

        subtype = getattr(v, "subtype", "SVB")
        max_spd = MAX_SPEED.get(subtype, 80)
        if v.id not in _vehicle_speeds or v.route_progress < 0.01:
            _vehicle_speeds[v.id] = round(random.uniform(max_spd * 0.45,
                                                          max_spd * 0.85), 1)
        speed_kmh = _vehicle_speeds[v.id]

        # Apply global speed multiplier
        effective_speed = speed_kmh * _speed_multiplier

        # Intentar seguir ruta almacenada
        if target.route_data:
            try:
                route_info = json.loads(target.route_data)
                waypoints = route_info.get("geometry", [])
                distance_km = route_info.get("distance_km", 1.0) or 1.0

                if waypoints and len(waypoints) >= 2:
                    hours_per_tick = TICK_SECONDS / 3600.0
                    km_per_tick = effective_speed * hours_per_tick
                    progress_inc = km_per_tick / distance_km
                    v.route_progress = min(1.0, v.route_progress + progress_inc)

                    router = get_router()
                    lat, lon = router.calculate_progress_on_route(
                        waypoints, v.route_progress)
                    v.lat = lat
                    v.lon = lon
                    v.speed = effective_speed
                    _consume_fuel_driving(v, km_per_tick)
                    return
            except Exception as e:
                print(f"⚠️ Route following failed for {v.id}: {e}")

        # Fallback: línea recta
        step = 0.00025 * _speed_multiplier
        dlat = target.lat - v.lat
        dlon = target.lon - v.lon
        mag = (dlat ** 2 + dlon ** 2) ** 0.5
        if mag > 0:
            v.lat += (dlat / mag) * step
            v.lon += (dlon / mag) * step
        v.speed = effective_speed
        km_approx = step * 111
        _consume_fuel_driving(v, km_approx)

    # ── REFUELING ─────────────────────────────────────────────────────
    @staticmethod
    def _step_refueling(v: Vehicle) -> None:
        _refueling[v.id] -= 1
        fill_per_tick = 100.0 / REFUEL_TICKS
        v.fuel = min(100.0, round(v.fuel + fill_per_tick, 1))
        v.speed = 0.0

        if _refueling[v.id] <= 0:
            v.fuel = 100.0
            del _refueling[v.id]
            _heading_to_gas.pop(v.id, None)
            v.status = "IDLE"

    # ── IR A REPOSTAR (IDLE con fuel bajo, sin caso) ─────────────────
    @staticmethod
    def _step_go_refuel(v: Vehicle, gas_stations: list[GasStation]) -> None:
        nearest = None
        nearest_dist = float("inf")
        for gs in gas_stations:
            d = _haversine_km(v.lat, v.lon, gs.lat, gs.lon)
            if d < nearest_dist:
                nearest_dist = d
                nearest = gs

        if not nearest:
            return

        # Si ya está muy cerca (< 150m), empieza a repostar
        if nearest_dist < 0.15:
            _refueling[v.id] = REFUEL_TICKS
            v.status = "REFUELING"
            v.speed = 0.0
            _heading_to_gas[v.id] = nearest.id
            return

        # Moverse hacia gasolinera a velocidad urbana (20-40 km/h)
        speed_kmh = round(random.uniform(20, 40), 1)
        hours_per_tick = TICK_SECONDS / 3600.0
        km_per_tick = speed_kmh * hours_per_tick
        step_deg = km_per_tick / 111.0

        dlat = nearest.lat - v.lat
        dlon = nearest.lon - v.lon
        mag = (dlat ** 2 + dlon ** 2) ** 0.5
        if mag > 0:
            v.lat += (dlat / mag) * step_deg
            v.lon += (dlon / mag) * step_deg
        v.speed = speed_kmh
        _heading_to_gas[v.id] = nearest.id
        _consume_fuel_driving(v, km_per_tick)

    # ── IDLE NORMAL — ambulancia PARADA en base ──────────────────────
    @staticmethod
    def _step_idle(v: Vehicle) -> None:
        """
        Comportamiento realista: la ambulancia está aparcada en su base.
        No se mueve excepto micro-ajustes muy esporádicos (≈2% de ticks)
        que simulan maniobra de parking o recolocación en la base.
        """
        _vehicle_speeds.pop(v.id, None)
        _heading_to_gas.pop(v.id, None)

        # ~2% de probabilidad de micro-maniobra (1-3 metros)
        if random.random() < 0.02:
            v.lat += random.uniform(-0.000015, 0.000015)
            v.lon += random.uniform(-0.000015, 0.000015)

        v.speed = 0.0
        _consume_fuel_idle(v)
