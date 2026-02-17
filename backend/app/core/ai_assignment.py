"""
AI Assignment Engine - Simulates intelligent hospital assignment
Based on multiple factors: distance, specialties, capacity, severity
"""
import math
import json
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session

from ..storage.models_sql import Hospital, IncidentSQL, Vehicle


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in km using Haversine formula"""
    R = 6371  # Earth radius in km
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = (math.sin(dlat / 2) ** 2 + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


def score_hospital_for_incident(
    hospital: Hospital,
    incident: IncidentSQL,
    incident_lat: float,
    incident_lon: float
) -> Tuple[float, str]:
    """
    Score a hospital for an incident (0-100)
    Returns (score, reasoning)
    """
    factors = []
    total_score = 0
    
    # 1. Distance factor (40% weight) - closer is better
    distance = calculate_distance(incident_lat, incident_lon, hospital.lat, hospital.lon)
    if distance < 3:
        distance_score = 40
        factors.append(f"Muy cercano ({distance:.1f}km)")
    elif distance < 7:
        distance_score = 30
        factors.append(f"Cercano ({distance:.1f}km)")
    elif distance < 15:
        distance_score = 20
        factors.append(f"Distancia moderada ({distance:.1f}km)")
    else:
        distance_score = 10
        factors.append(f"Lejos ({distance:.1f}km)")
    total_score += distance_score
    
    # 2. Specialty match (30% weight)
    specialties = json.loads(hospital.specialties) if hospital.specialties else []
    if incident.incident_type in specialties:
        specialty_score = 30
        factors.append(f"Especialidad en {incident.incident_type}")
    elif hospital.emergency_level >= 3:
        specialty_score = 20
        factors.append("Hospital de nivel avanzado")
    else:
        specialty_score = 10
        factors.append("Sin especialidad específica")
    total_score += specialty_score
    
    # 3. Capacity available (20% weight)
    availability = (hospital.capacity - hospital.current_load) / hospital.capacity if hospital.capacity > 0 else 0
    if availability > 0.7:
        capacity_score = 20
        factors.append(f"Alta disponibilidad ({int(availability*100)}%)")
    elif availability > 0.4:
        capacity_score = 15
        factors.append(f"Disponibilidad media ({int(availability*100)}%)")
    elif availability > 0.1:
        capacity_score = 8
        factors.append(f"Baja disponibilidad ({int(availability*100)}%)")
    else:
        capacity_score = 2
        factors.append("Casi lleno")
    total_score += capacity_score
    
    # 4. Emergency level match (10% weight)
    if incident.severity >= 4 and hospital.emergency_level >= 3:
        emergency_score = 10
        factors.append("Centro de trauma nivel III")
    elif incident.severity >= 3 and hospital.emergency_level >= 2:
        emergency_score = 8
        factors.append("Nivel de emergencia adecuado")
    else:
        emergency_score = 5
        factors.append("Nivel básico")
    total_score += emergency_score
    
    reasoning = " | ".join(factors)
    confidence = total_score / 100
    
    return confidence, reasoning


def suggest_hospital_assignment(
    db: Session,
    incident: IncidentSQL
) -> Optional[Dict]:
    """
    AI suggests the best hospital for an incident
    Returns dict with hospital_id, confidence, and reasoning
    """
    # Get all available hospitals
    hospitals = db.query(Hospital).filter(Hospital.available == True).all()
    
    if not hospitals:
        return None
    
    # Score each hospital
    scored_hospitals = []
    for hospital in hospitals:
        confidence, reasoning = score_hospital_for_incident(
            hospital, incident, incident.lat, incident.lon
        )
        scored_hospitals.append({
            "hospital": hospital,
            "confidence": confidence,
            "reasoning": reasoning
        })
    
    # Sort by confidence (highest first)
    scored_hospitals.sort(key=lambda x: x["confidence"], reverse=True)
    
    # Return top recommendation
    best = scored_hospitals[0]
    
    return {
        "hospital_id": best["hospital"].id,
        "hospital_name": best["hospital"].name,
        "confidence": round(best["confidence"], 2),
        "reasoning": best["reasoning"],
        "alternatives": [
            {
                "hospital_id": alt["hospital"].id,
                "hospital_name": alt["hospital"].name,
                "confidence": round(alt["confidence"], 2)
            }
            for alt in scored_hospitals[1:3]  # Top 2 alternatives
        ]
    }


def suggest_vehicle_assignment(
    db: Session,
    incident: IncidentSQL,
    available_vehicles: List[Vehicle]
) -> Optional[Dict]:
    """
    AI suggests the best vehicle for an incident
    Returns dict with vehicle_id, eta, and reasoning
    """
    if not available_vehicles:
        return None
    
    # Score each vehicle
    scored_vehicles = []
    for vehicle in available_vehicles:
        distance = calculate_distance(incident.lat, incident.lon, vehicle.lat, vehicle.lon)
        
        # Estimate time (assuming avg speed 40 km/h in city)
        eta_minutes = (distance / 40) * 60
        
        # Score factors
        score = 0
        factors = []
        
        # Distance/ETA (50% weight)
        if eta_minutes < 5:
            score += 50
            factors.append(f"Muy cercano (ETA {int(eta_minutes)}min)")
        elif eta_minutes < 10:
            score += 40
            factors.append(f"Cercano (ETA {int(eta_minutes)}min)")
        elif eta_minutes < 15:
            score += 30
            factors.append(f"Distancia moderada (ETA {int(eta_minutes)}min)")
        else:
            score += 20
            factors.append(f"Lejos (ETA {int(eta_minutes)}min)")
        
        # Fuel level (25% weight)
        if vehicle.fuel > 70:
            score += 25
            factors.append(f"Combustible alto ({int(vehicle.fuel)}%)")
        elif vehicle.fuel > 40:
            score += 20
            factors.append(f"Combustible medio ({int(vehicle.fuel)}%)")
        else:
            score += 10
            factors.append(f"Combustible bajo ({int(vehicle.fuel)}%)")
        
        # Trust score (25% weight)
        if vehicle.trust_score > 85:
            score += 25
            factors.append(f"Confiabilidad alta ({vehicle.trust_score})")
        elif vehicle.trust_score > 70:
            score += 20
            factors.append(f"Confiabilidad buena ({vehicle.trust_score})")
        else:
            score += 15
            factors.append(f"Confiabilidad aceptable ({vehicle.trust_score})")
        
        scored_vehicles.append({
            "vehicle": vehicle,
            "score": score,
            "eta_minutes": eta_minutes,
            "distance_km": distance,
            "reasoning": " | ".join(factors)
        })
    
    # Sort by score
    scored_vehicles.sort(key=lambda x: x["score"], reverse=True)
    
    best = scored_vehicles[0]
    
    return {
        "vehicle_id": best["vehicle"].id,
        "eta_minutes": round(best["eta_minutes"], 1),
        "distance_km": round(best["distance_km"], 2),
        "confidence": round(best["score"] / 100, 2),
        "reasoning": best["reasoning"]
    }
