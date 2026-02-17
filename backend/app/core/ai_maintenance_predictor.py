# app/core/ai_maintenance_predictor.py
"""
Sistema de mantenimiento predictivo para vehículos.
Predice cuándo un vehículo necesitará mantenimiento basado en patrones de uso.
"""
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..storage.models_sql import Vehicle, IncidentSQL


class MaintenancePredictor:
    """Predictor de mantenimiento preventivo"""
    
    def __init__(self):
        # Umbrales para diferentes niveles de mantenimiento
        self.maintenance_thresholds = {
            "ROUTINE": {
                "simulated_km": 1000,
                "missions_completed": 50,
                "fuel_consumption_rate": 0.8
            },
            "PREVENTIVE": {
                "simulated_km": 2500,
                "missions_completed": 100,
                "fuel_consumption_rate": 1.2
            },
            "URGENT": {
                "simulated_km": 5000,
                "missions_completed": 200,
                "fuel_consumption_rate": 1.5,
                "trust_score_threshold": 60
            }
        }
    
    def _calculate_simulated_km(
        self,
        vehicle: Vehicle,
        db: Session,
        days_back: int = 30
    ) -> float:
        """Calcula kilómetros simulados basado en historial"""
        # En un sistema real, esto vendría de la base de datos
        # Por ahora, estimamos basado en misiones completadas
        
        since_date = datetime.utcnow() - timedelta(days=days_back)
        
        completed_missions = db.query(IncidentSQL).filter(
            IncidentSQL.assigned_vehicle_id == vehicle.id,
            IncidentSQL.status == "RESOLVED",
            IncidentSQL.resolved_at >= since_date
        ).count()
        
       # Estimar ~5km por misión en promedio
        estimated_km = completed_missions * 5
        
        return estimated_km
    
    def _calculate_fuel_efficiency(self, vehicle: Vehicle) -> float:
        """Calcula eficiencia de combustible (consumo por km simulado)"""
        # En sistema real, tracking histórico de fuel vs km
        # Por ahora, estimación basada en trust_score
        
        base_efficiency = 0.1  # 0.1 litros/km
        
        # Vehículos con menor trust_score son menos eficientes
        efficiency_factor = (vehicle.trust_score or 100) / 100
        
        return base_efficiency / efficiency_factor
    
    def predict_maintenance_need(
        self,
        vehicle: Vehicle,
        db: Session
    ) -> Dict[str, Any]:
        """
        Predice necesidades de mantenimiento para un vehículo.
        
        Returns:
            {
                "vehicle_id": str,
                "maintenance_level": "NONE" | "ROUTINE" | "PREVENTIVE" | "URGENT",
                "priority": int (1-5),
                "reasons": List[str],
                "estimated_days_until_maintenance": int,
                "recommended_actions": List[str],
                "metrics": {...}
            }
        """
        simulated_km = self._calculate_simulated_km(vehicle, db)
        
        # Contar misiones completadas (últimos 30 días)
        since_date = datetime.utcnow() - timedelta(days=30)
        missions_completed = db.query(IncidentSQL).filter(
            IncidentSQL.assigned_vehicle_id == vehicle.id,
            IncidentSQL.status == "RESOLVED",
            IncidentSQL.resolved_at >= since_date
        ).count()
        
        fuel_efficiency = self._calculate_fuel_efficiency(vehicle)
        trust_score = vehicle.trust_score or 100
        
        # Determinar nivel de mantenimiento necesario
        reasons = []
        maintenance_level = "NONE"
        priority = 1
        recommended_actions = []
        
        # Check URGENT
        if (simulated_km >= self.maintenance_thresholds["URGENT"]["simulated_km"] or
            missions_completed >= self.maintenance_thresholds["URGENT"]["missions_completed"] or
            trust_score <= self.maintenance_thresholds["URGENT"]["trust_score_threshold"]):
            
            maintenance_level = "URGENT"
            priority = 5
            
            if simulated_km >= self.maintenance_thresholds["URGENT"]["simulated_km"]:
                reasons.append(f"Kilometraje alto: {simulated_km} km")
                recommended_actions.append("Inspección completa del motor y transmisión")
            
            if missions_completed >= self.maintenance_thresholds["URGENT"]["missions_completed"]:
                reasons.append(f"Muchas misiones: {missions_completed} en 30 días")
                recommended_actions.append("Revisión exhaustiva de sistemas críticos")
            
            if trust_score <= 60:
                reasons.append(f"Trust score crítico: {trust_score}/100")
                recommended_actions.append("Diagnóstico completo, posible retirada temporal")
        
        # Check PREVENTIVE
        elif (simulated_km >= self.maintenance_thresholds["PREVENTIVE"]["simulated_km"] or
              missions_completed >= self.maintenance_thresholds["PREVENTIVE"]["missions_completed"]):
            
            maintenance_level = "PREVENTIVE"
            priority = 3
            
            if simulated_km >= self.maintenance_thresholds["PREVENTIVE"]["simulated_km"]:
                reasons.append(f"Kilometraje moderado-alto: {simulated_km} km")
                recommended_actions.append("Cambio de aceite y filtros")
            
            if missions_completed >= self.maintenance_thresholds["PREVENTIVE"]["missions_completed"]:
                reasons.append(f"Uso intensivo: {missions_completed} misiones")
                recommended_actions.append("Revisión de frenos y suspensión")
            
            recommended_actions.append("Inspección de neumáticos")
        
        # Check ROUTINE
        elif (simulated_km >= self.maintenance_thresholds["ROUTINE"]["simulated_km"] or
              missions_completed >= self.maintenance_thresholds["ROUTINE"]["missions_completed"]):
            
            maintenance_level = "ROUTINE"
            priority = 2
            reasons.append(f"Mantenimiento preventivo rutinario")
            recommended_actions = [
                "Revisión general de fluidos",
                "Inspección visual de componentes",
                "Limpieza y desinfección"
            ]
        
        # Eficiencia de combustible
        if fuel_efficiency > 0.15:
            reasons.append(f"Baja eficiencia de combustible")
            recommended_actions.append("Revisar sistema de inyección y filtros")
        
        # Estimar días hasta mantenimiento necesario
        if maintenance_level == "URGENT":
            days_until = 0
        elif maintenance_level == "PREVENTIVE":
            days_until = 7
        elif maintenance_level == "ROUTINE":
            days_until = 14
        else:
            days_until = 30
        
        # Si no hay razones, el vehículo está bien
        if not reasons:
            reasons.append("Vehículo en condiciones óptimas")
            recommended_actions.append("Continuar operación normal")
        
        return {
            "vehicle_id": vehicle.id,
            "maintenance_level": maintenance_level,
            "priority": priority,
            "reasons": reasons,
            "estimated_days_until_maintenance": days_until,
            "recommended_actions": recommended_actions,
            "metrics": {
                "simulated_km_last_30_days": round(simulated_km, 1),
                "missions_completed_last_30_days": missions_completed,
                "fuel_efficiency_l_per_km": round(fuel_efficiency, 3),
                "trust_score": trust_score,
                "fuel_level": vehicle.fuel or 0
            },
            "next_maintenance_date": (datetime.utcnow() + timedelta(days=days_until)).strftime("%Y-%m-%d")
        }
    
    def get_fleet_maintenance_schedule(
        self,
        db: Session
    ) -> Dict[str, Any]:
        """
        Genera un schedule de mantenimiento para toda la flota.
        
        Returns:
            {
                "total_vehicles": int,
                "vehicles_by_status": {...},
                "urgent_maintenance": [...],
                "upcoming_maintenance": [...],
                "fleet_health_score": float
            }
        """
        vehicles = db.query(Vehicle).filter(Vehicle.enabled == True).all()
        
        vehicles_by_status = {
            "NONE": [],
            "ROUTINE": [],
            "PREVENTIVE": [],
            "URGENT": []
        }
        
        urgent_maintenance = []
        upcoming_maintenance = []
        total_priority = 0
        
        for vehicle in vehicles:
            prediction = self.predict_maintenance_need(vehicle, db)
            
            level = prediction["maintenance_level"]
            vehicles_by_status[level].append(vehicle.id)
            
            if level == "URGENT":
                urgent_maintenance.append(prediction)
            elif level in ["PREVENTIVE", "ROUTINE"]:
                upcoming_maintenance.append(prediction)
            
            total_priority += prediction["priority"]
        
        # Calcular score de salud de la flota (invertido de prioridades)
        max_priority = len(vehicles) * 5
        fleet_health_score = 100 - ((total_priority / max_priority) * 100) if max_priority > 0 else 100
        
        # Ordenar por prioridad
        urgent_maintenance.sort(key=lambda x: x["priority"], reverse=True)
        upcoming_maintenance.sort(key=lambda x: x["priority"], reverse=True)
        
        return {
            "total_vehicles": len(vehicles),
            "vehicles_by_status": {
                level: len(vlist) for level, vlist in vehicles_by_status.items()
            },
            "urgent_maintenance": urgent_maintenance,
            "upcoming_maintenance": upcoming_maintenance[:10],  # Top 10
            "fleet_health_score": round(fleet_health_score, 1),
            "timestamp": datetime.utcnow().isoformat()
        }


# Singleton global
_maintenance_predictor = None

def get_maintenance_predictor() -> MaintenancePredictor:
    """Obtiene instancia singleton del predictor de mantenimiento"""
    global _maintenance_predictor
    if _maintenance_predictor is None:
        _maintenance_predictor = MaintenancePredictor()
    return _maintenance_predictor
