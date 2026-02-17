# app/core/ai_anomaly_detector.py
"""
Detector de anomalías en tiempo real usando algoritmos de ML.
Identifica comportamientos inusuales en la flota y operaciones.
"""
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sklearn.ensemble import IsolationForest
from sqlalchemy.orm import Session
from ..storage.models_sql import Vehicle, IncidentSQL


class AnomalyDetector:
    """Detector de anomalías usando Isolation Forest"""
    
    def __init__(self):
        self.vehicle_model = IsolationForest(contamination=0.1, random_state=42)
        self.incident_model = IsolationForest(contamination=0.15, random_state=42)
        self.is_trained = False
        self.baseline_metrics = {}
    
    def _extract_vehicle_features(self, vehicle: Vehicle) -> np.ndarray:
        """Extrae features de un vehículo"""
        return np.array([
            vehicle.speed or 0.0,
            vehicle.fuel or 0.0,
            vehicle.trust_score or 100,
            1 if vehicle.status == "EN_ROUTE" else 0,
            vehicle.route_progress or 0.0
        ])
    
    def _extract_incident_features(self, incident: IncidentSQL, duration_minutes: float) -> np.ndarray:
        """Extrae features de un incidente"""
        severity_map = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
        return np.array([
            severity_map.get(incident.severity, 2),
            incident.affected_count,
            duration_minutes,
            1 if incident.status == "RESOLVED" else 0
        ])
    
    def train_baseline(self, db: Session):
        """Entrena modelos con datos normales para establecer baseline"""
        # Entrenar con vehículos
        vehicles = db.query(Vehicle).filter(Vehicle.enabled == True).all()
        
        if len(vehicles) >= 3:
            X_vehicles = np.array([self._extract_vehicle_features(v) for v in vehicles])
            self.vehicle_model.fit(X_vehicles)
        
        # Entrenar con incidentes resueltos
        resolved_incidents = db.query(IncidentSQL).filter(
            IncidentSQL.status == "RESOLVED",
            IncidentSQL.resolved_at.isnot(None)
        ).all()
        
        if len(resolved_incidents) >= 5:
            X_incidents = []
            for inc in resolved_incidents:
                duration = (inc.resolved_at - inc.created_at).total_seconds() / 60
                X_incidents.append(self._extract_incident_features(inc, duration))
            
            X_incidents = np.array(X_incidents)
            self.incident_model.fit(X_incidents)
        
        self.is_trained = True
        print(f"✅ Anomaly detector trained with {len(vehicles)} vehicles and {len(resolved_incidents)} incidents")
    
    def detect_vehicle_anomalies(
        self,
        vehicles: List[Vehicle],
        db: Optional[Session] = None
    ) -> List[Dict[str, Any]]:
        """
        Detecta anomalías en vehículos.
        
        Returns:
            Lista de anomalías: [{"vehicle_id": str, "anomaly_type": str, "severity": str, "details": str}]
        """
        anomalies = []
        
        for vehicle in vehicles:
            if not vehicle.enabled:
                continue
            
            # 1. Combustible crítico
            if vehicle.fuel < 15:
                anomalies.append({
                    "vehicle_id": vehicle.id,
                    "anomaly_type": "LOW_FUEL",
                    "severity": "HIGH" if vehicle.fuel < 10 else "MEDIUM",
                    "details": f"Combustible bajo: {vehicle.fuel}%",
                    "value": vehicle.fuel,
                    "recommended_action": "Enviar a reabastecimiento inmediatamente" if vehicle.fuel < 10 else "Programar reabastecimiento"
                })
            
            # 2. Velocidad anormal (demasiado alta o demasiado baja cuando está EN_ROUTE)
            if vehicle.status == "EN_ROUTE":
                if vehicle.speed > 120:  # Muy rápido
                    anomalies.append({
                        "vehicle_id": vehicle.id,
                        "anomaly_type": "EXCESSIVE_SPEED",
                        "severity": "HIGH",
                        "details": f"Velocidad excesiva: {vehicle.speed} km/h",
                        "value": vehicle.speed,
                        "recommended_action": "Contactar con conductor, posible emergencia o error de sensor"
                    })
                elif vehicle.speed < 5 and vehicle.route_progress < 0.9:  # Muy lento y no ha llegado
                    anomalies.append({
                        "vehicle_id": vehicle.id,
                        "anomaly_type": "STALLED",
                        "severity": "MEDIUM",
                        "details": f"Vehículo detenido en ruta: {vehicle.speed} km/h",
                        "value": vehicle.speed,
                        "recommended_action": "Verificar estado del vehículo, posible avería"
                    })
            
            # 3. Trust score en caída
            if vehicle.trust_score < 70:
                anomalies.append({
                    "vehicle_id": vehicle.id,
                    "anomaly_type": "LOW_TRUST_SCORE",
                    "severity": "MEDIUM",
                    "details": f"Score de confiabilidad bajo: {vehicle.trust_score}/100",
                    "value": vehicle.trust_score,
                    "recommended_action": "Revisar historial de mantenimiento y performance"
                })
            
            # 4. Progreso de ruta estancado
            if vehicle.status == "EN_ROUTE" and vehicle.route_progress > 0:
                # Si está en ruta pero no ha progresado (esto requeriría tracking histórico)
                # Por ahora, solo detectamos si está al inicio y ha pasado tiempo
                pass  # Requiere historial temporal
        
        # 5. Usar Isolation Forest si está entrenado
        if self.is_trained and vehicles:
            try:
                X = np.array([self._extract_vehicle_features(v) for v in vehicles])
                predictions = self.vehicle_model.predict(X)
                
                for i, pred in enumerate(predictions):
                    if pred == -1:  # -1 indica anomalía
                        vehicle = vehicles[i]
                        # Solo agregar si no hay ya una anomalía específica detectada
                        if not any(a["vehicle_id"] == vehicle.id for a in anomalies):
                            anomalies.append({
                                "vehicle_id": vehicle.id,
                                "anomaly_type": "PATTERN_ANOMALY",
                                "severity": "LOW",
                                "details": "Patrón de comportamiento inusual detectado por ML",
                                "value": None,
                                "recommended_action": "Monitorear de cerca"
                            })
            except Exception as e:
                print(f"⚠️ ML anomaly detection failed: {e}")
        
        return anomalies
    
    def detect_incident_anomalies(
        self,
        incidents: List[IncidentSQL]
    ) -> List[Dict[str, Any]]:
        """
        Detecta anomalías en incidentes.
        
        Returns:
            Lista de anomalías en incidentes
        """
        anomalies = []
        now = datetime.utcnow()
        
        for incident in incidents:
            if incident.status not in ["ASSIGNED", "RESOLVED"]:
                continue
            
            # 1. Tiempo de resolución excesivo
            if incident.status == "ASSIGNED" and incident.assigned_vehicle_id:
                duration_minutes = (now - incident.created_at).total_seconds() / 60
                
                # Umbral basado en severidad
                threshold_map = {
                    "CRITICAL": 10,
                    "HIGH": 20,
                    "MEDIUM": 40,
                    "LOW": 60
                }
                threshold = threshold_map.get(incident.severity, 30)
                
                if duration_minutes > threshold:
                    anomalies.append({
                        "incident_id": incident.id,
                        "anomaly_type": "DELAYED_RESOLUTION",
                        "severity": "HIGH" if incident.severity in ["CRITICAL", "HIGH"] else "MEDIUM",
                        "details": f"Tiempo de resolución excesivo: {int(duration_minutes)} min (esperado: <{threshold} min)",
                        "value": int(duration_minutes),
                        "recommended_action": "Verificar estado de la ambulancia, considerar enviar refuerzo"
                    })
            
            # 2. Múltiples personas afectadas sin escalación
            if incident.affected_count >= 5 and incident.severity not in ["HIGH", "CRITICAL"]:
                anomalies.append({
                    "incident_id": incident.id,
                    "anomaly_type": "UNDERESTIMATED_SEVERITY",
                    "severity": "MEDIUM",
                    "details": f"{incident.affected_count} personas afectadas pero severidad={incident.severity}",
                    "value": incident.affected_count,
                    "recommended_action": "Considerar elevar severidad y enviar recursos adicionales"
                })
        
        return anomalies
    
    def get_system_health_score(self, db: Session) -> Dict[str, Any]:
        """
        Calcula un score general de salud del sistema.
        
        Returns:
            {
                "overall_score": 0-100,
                "vehicle_health": 0-100,
                "incident_health": 0-100,
                "anomaly_count": int,
                "status": "HEALTHY" | "WARNING" | "CRITICAL"
            }
        """
        vehicles = db.query(Vehicle).filter(Vehicle.enabled == True).all()
        open_incidents = db.query(IncidentSQL).filter(
            IncidentSQL.status.in_(["OPEN", "ASSIGNED"])
        ).all()
        
        vehicle_anomalies = self.detect_vehicle_anomalies(vehicles)
        incident_anomalies = self.detect_incident_anomalies(open_incidents)
        
        total_anomalies = len(vehicle_anomalies) + len(incident_anomalies)
        
        # Score de vehículos (basado en fuel promedio y trust score)
        if vehicles:
            avg_fuel = sum(v.fuel or 0 for v in vehicles) / len(vehicles)
            avg_trust = sum(v.trust_score or 100 for v in vehicles) / len(vehicles)
            vehicle_health = (avg_fuel + avg_trust) / 2
        else:
            vehicle_health = 100
        
        # Score de incidentes (menos incidentes abiertos es mejor)
        max_incidents = max(len(vehicles) * 2, 10)  # Usar flota como referencia
        incident_ratio = len(open_incidents) / max_incidents
        incident_health = max(0, 100 - (incident_ratio * 100))
        
        # Score general
        overall_score = (vehicle_health * 0.6 + incident_health * 0.4)
        
        # Penalizar por anomalías
        overall_score = max(0, overall_score - (total_anomalies * 5))
        
        # Determinar status
        if overall_score >= 80:
            status = "HEALTHY"
        elif overall_score >= 60:
            status = "WARNING"
        else:
            status = "CRITICAL"
        
        return {
            "overall_score": round(overall_score, 1),
            "vehicle_health": round(vehicle_health, 1),
            "incident_health": round(incident_health, 1),
            "anomaly_count": total_anomalies,
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }


# Singleton global
_anomaly_detector = None

def get_anomaly_detector() -> AnomalyDetector:
    """Obtiene instancia singleton del detector"""
    global _anomaly_detector
    if _anomaly_detector is None:
        _anomaly_detector = AnomalyDetector()
    return _anomaly_detector
