from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import json

from ..storage.db import get_db
from ..storage.models_sql import Hospital
from ..auth.dependencies import get_current_user, User, require_role

router = APIRouter(prefix="/api/hospitals", tags=["hospitals"])


class HospitalCreate(BaseModel):
    id: str
    name: str
    address: Optional[str] = None
    city: str = "Madrid"
    lat: float
    lon: float
    capacity: int = 100
    specialties: Optional[List[str]] = None
    emergency_level: int = 1


class HospitalResponse(BaseModel):
    id: str
    name: str
    address: Optional[str]
    city: str
    lat: float
    lon: float
    capacity: int
    current_load: int
    specialties: Optional[List[str]]
    emergency_level: int
    available: bool
    availability_percent: float

    class Config:
        from_attributes = True


@router.get("/", response_model=List[HospitalResponse])
async def list_hospitals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all hospitals"""
    hospitals = db.query(Hospital).filter(Hospital.available == True).all()
    result = []
    for h in hospitals:
        specialties = json.loads(h.specialties) if h.specialties else []
        availability_percent = round(((h.capacity - h.current_load) / h.capacity * 100), 1) if h.capacity > 0 else 0
        result.append(HospitalResponse(
            id=h.id,
            name=h.name,
            address=h.address,
            city=h.city,
            lat=h.lat,
            lon=h.lon,
            capacity=h.capacity,
            current_load=h.current_load,
            specialties=specialties,
            emergency_level=h.emergency_level,
            available=h.available,
            availability_percent=availability_percent
        ))
    return result


@router.post("/", response_model=HospitalResponse)
async def create_hospital(
    data: HospitalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    """Create a new hospital (Admin only)"""
    existing = db.query(Hospital).filter(Hospital.id == data.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Hospital ID already exists")
    
    specialties_json = json.dumps(data.specialties) if data.specialties else None
    
    hospital = Hospital(
        id=data.id,
        name=data.name,
        address=data.address,
        city=data.city,
        lat=data.lat,
        lon=data.lon,
        capacity=data.capacity,
        specialties=specialties_json,
        emergency_level=data.emergency_level
    )
    db.add(hospital)
    db.commit()
    db.refresh(hospital)
    
    specialties = json.loads(hospital.specialties) if hospital.specialties else []
    availability_percent = round(((hospital.capacity - hospital.current_load) / hospital.capacity * 100), 1)
    
    return HospitalResponse(
        id=hospital.id,
        name=hospital.name,
        address=hospital.address,
        city=hospital.city,
        lat=hospital.lat,
        lon=hospital.lon,
        capacity=hospital.capacity,
        current_load=hospital.current_load,
        specialties=specialties,
        emergency_level=hospital.emergency_level,
        available=hospital.available,
        availability_percent=availability_percent
    )


@router.post("/seed")
async def seed_hospitals(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    """Seed sample hospitals in Madrid"""
    hospitals_data = [
        {
            "id": "HOSP-001",
            "name": "Hospital Universitario La Paz",
            "address": "Paseo de la Castellana, 261",
            "lat": 40.4789,
            "lon": -3.6837,
            "capacity": 150,
            "specialties": ["CARDIO", "NEUROLOGICAL", "TRAUMA", "OBSTETRIC"],
            "emergency_level": 3
        },
        {
            "id": "HOSP-002",
            "name": "Hospital Clínico San Carlos",
            "address": "Calle del Profesor Martín Lagos, s/n",
            "lat": 40.4397,
            "lon": -3.7244,
            "capacity": 120,
            "specialties": ["RESPIRATORY", "BURN", "PEDIATRIC"],
            "emergency_level": 3
        },
        {
            "id": "HOSP-003",
            "name": "Hospital 12 de Octubre",
            "address": "Av. de Córdoba, s/n",
            "lat": 40.3759,
            "lon": -3.6894,
            "capacity": 180,
            "specialties": ["TRAUMA", "NEUROLOGICAL", "PEDIATRIC", "OBSTETRIC"],
            "emergency_level": 3
        },
        {
            "id": "HOSP-004",
            "name": "Hospital Gregorio Marañón",
            "address": "Calle del Dr. Esquerdo, 46",
            "lat": 40.4146,
            "lon": -3.6732,
            "capacity": 140,
            "specialties": ["CARDIO", "NEUROLOGICAL", "TRAUMA"],
            "emergency_level": 3
        },
        {
            "id": "HOSP-005",
            "name": "Hospital Ramón y Cajal",
            "address": "Ctra. de Colmenar Viejo, km 9100",
            "lat": 40.5020,
            "lon": -3.6682,
            "capacity": 110,
            "specialties": ["RESPIRATORY", "POISONING", "PSYCHIATRIC"],
            "emergency_level": 2
        }
    ]
    
    created = []
    for h_data in hospitals_data:
        existing = db.query(Hospital).filter(Hospital.id == h_data["id"]).first()
        if not existing:
            hospital = Hospital(
                id=h_data["id"],
                name=h_data["name"],
                address=h_data["address"],
                lat=h_data["lat"],
                lon=h_data["lon"],
                capacity=h_data["capacity"],
                specialties=json.dumps(h_data["specialties"]),
                emergency_level=h_data["emergency_level"]
            )
            db.add(hospital)
            created.append(h_data["id"])
    
    db.commit()
    return {"message": f"Created {len(created)} hospitals", "hospitals": created}
