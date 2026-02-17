from pydantic import BaseModel
from typing import Optional, List

class VehicleDTO(BaseModel):
    id: str
    type: str
    status: str
    lat: float
    lon: float
    speed: float
    fuel: float
    trust_score: int
    enabled: bool
    sim_vehicle_ref: Optional[str] = None

class FleetMetricsDTO(BaseModel):
    active_vehicles: int
    avg_fuel: float

class LivePayloadDTO(BaseModel):
    ts: float
    vehicles: List[VehicleDTO]
    fleet_metrics: FleetMetricsDTO
    alerts: list = []
