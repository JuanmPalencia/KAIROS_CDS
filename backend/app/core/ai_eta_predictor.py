# app/core/ai_eta_predictor.py
"""
Predictor de ETA (Estimated Time of Arrival) mejorado usando ML.
Considera tráfico, hora del día, tipo de incidente y patrones históricos.
"""
import numpy as np
from typing import Optional, Dict, Any
from datetime import datetime
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
import joblib
import os
from sqlalchemy.orm import Session
from ..storage.models_sql import IncidentSQL, Vehicle


class ETAPredictor:
    """Predictor de ETA usando Gradient Boosting"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.model_path = "models/eta_predictor.joblib"
        self.scaler_path = "models/eta_scaler.joblib"
        
        self._load_model()
    
    def _load_model(self):
        """Carga modelo pre-entrenado si existe"""
        if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
            try:
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                self.is_trained = True
                print("✅ ETA predictor model loaded")
            except Exception as e:
                print(f"⚠️ Could not load ETA model: {e}")
    
    def _save_model(self):
        """Guarda modelo entrenado"""
        os.makedirs("models", exist_ok=True)
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.scaler, self.scaler_path)
        print("✅ ETA predictor model saved")
    
    def _extract_features(
        self,
        distance_km: float,
        vehicle_speed: float,
        severity: str,
        incident_type: str,
        hour: int,
        weekday: int,
        is_rush_hour: bool
    ) -> np.ndarray:
        """Extrae features para predicción"""
        severity_map = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
        
        # Features básicos
        features = [
            distance_km,
            vehicle_speed,
            severity_map.get(severity, 2),
            hour,
            weekday,
            1 if is_rush_hour else 0,
            1 if weekday >= 5 else 0,  # es_fin_de_semana
            1 if 22 <= hour or hour <= 6 else 0  # es_noche
        ]
        
        # One-hot encoding simplificado para tipo de incidente
        incident_types = ["CARDIAC_ARREST", "TRAFFIC_ACCIDENT", "RESPIRATORY", "STROKE", "TRAUMA"]
        for itype in incident_types:
            features.append(1 if incident_type == itype else 0)
        
        return np.array(features).reshape(1, -1)
    
    def train_with_historical_data(self, db: Session):
        """Entrena modelo con datos históricos"""
        # Obtener incidentes resueltos con tiempos
        resolved = db.query(IncidentSQL).filter(
            IncidentSQL.status == "RESOLVED",
            IncidentSQL.resolved_at.isnot(None),
            IncidentSQL.assigned_vehicle_id.isnot(None)
        ).all()
        
        if len(resolved) < 20:
            print(f"⚠️ Not enough data for ETA training ({len(resolved)} < 20)")
            return self._train_with_synthetic_data()
        
        X = []
        y = []
        
        for inc in resolved:
            # Obtener vehículo asignado (si aún existe)
            vehicle = db.query(Vehicle).filter(Vehicle.id == inc.assigned_vehicle_id).first()
            vehicle_speed = vehicle.speed if vehicle else 40.0  # Default
            
            # Calcular distancia aproximada (Haversine simplificado)
            # En producción, usar la distancia real de la ruta
            distance = self._haversine_distance(
                inc.lat, inc.lon,
                vehicle.lat if vehicle else 40.4168,
                vehicle.lon if vehicle else -3.7038
            )
            
            # Tiempo real de resolución
            actual_duration = (inc.resolved_at - inc.created_at).total_seconds() / 60
            
            hour = inc.created_at.hour
            weekday = inc.created_at.weekday()
            is_rush = 7 <= hour <= 9 or 17 <= hour <= 19
            
            features = self._extract_features(
                distance, vehicle_speed, inc.severity,
                inc.incident_type, hour, weekday, is_rush
            )
            
            X.append(features[0])
            y.append(actual_duration)
        
        X = np.array(X)
        y = np.array(y)
        
        # Entrenar
        X_scaled = self.scaler.fit_transform(X)
        self.model = GradientBoostingRegressor(n_estimators=100, random_state=42)
        self.model.fit(X_scaled, y)
        self.is_trained = True
        
        self._save_model()
        print(f"✅ ETA model trained with {len(resolved)} incidents")
    
    def _train_with_synthetic_data(self):
        """Genera datos sintéticos para entrenar (demo)"""
        print("🔄 Training ETA model with synthetic data...")
        
        np.random.seed(42)
        n_samples = 300
        
        X = []
        y = []
        
        for _ in range(n_samples):
            distance = np.random.uniform(0.5, 15)  # 0.5 a 15 km
            vehicle_speed = np.random.uniform(25, 70)  # 25-70 km/h
            severity = np.random.choice([1, 2, 3, 4])
            hour = np.random.randint(0, 24)
            weekday = np.random.randint(0, 7)
            is_rush = 1 if 7 <= hour <= 9 or 17 <= hour <= 19 else 0
            is_weekend = 1 if weekday >= 5 else 0
            is_night = 1 if 22 <= hour or hour <= 6 else 0
            
            # One-hot encoding para tipo
            incident_type_encoding = [0] * 5
            incident_type_encoding[np.random.randint(0, 5)] = 1
            
            features = [
                distance, vehicle_speed, severity, hour, weekday,
                is_rush, is_weekend, is_night
            ] + incident_type_encoding
            
            # ETA = distancia / velocidad + factores adicionales
            base_eta = (distance / vehicle_speed) * 60  # convertir a minutos
            
            # Ajustar por factores
            if is_rush:
                base_eta *= 1.4  # 40% más en hora pico
            if is_night:
                base_eta *= 0.85  # 15% más rápido de noche
            if severity >= 3:
                base_eta *= 0.9  # Más rápido en emergencias críticas
            
            # Agregar ruido
            eta = base_eta * np.random.uniform(0.85, 1.15)
            eta = max(3, eta)  # Mínimo 3 minutos
            
            X.append(features)
            y.append(eta)
        
        X = np.array(X)
        y = np.array(y)
        
        # Entrenar
        X_scaled = self.scaler.fit_transform(X)
        self.model = GradientBoostingRegressor(n_estimators=100, random_state=42)
        self.model.fit(X_scaled, y)
        self.is_trained = True
        
        self._save_model()
        print(f"✅ ETA model trained with {n_samples} synthetic samples")
    
    def predict_eta(
        self,
        vehicle: Vehicle,
        incident: IncidentSQL,
        route_distance_km: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Predice ETA mejorado para un vehículo yendo a un incidente.
        
        Returns:
            {
                "eta_minutes": float,
                "confidence": float,
                "factors": {...},
                "arrival_time": str
            }
        """
        if not self.is_trained:
            self._train_with_synthetic_data()
        
        # Calcular distancia si no se proporciona
        if route_distance_km is None:
            route_distance_km = self._haversine_distance(
                vehicle.lat, vehicle.lon,
                incident.lat, incident.lon
            )
        
        now = datetime.utcnow()
        hour = now.hour
        weekday = now.weekday()
        is_rush = 7 <= hour <= 9 or 17 <= hour <= 19
        
        # Extraer features
        features = self._extract_features(
            route_distance_km,
            vehicle.speed or 40.0,
            incident.severity,
            incident.type,
            hour,
            weekday,
            is_rush
        )
        
        # Predecir
        features_scaled = self.scaler.transform(features)
        predicted_eta = self.model.predict(features_scaled)[0]
        
        # Calcular confianza (basada en características del modelo)
        # En producción, usar predicciones de ensemble o intervalos de confianza
        confidence = 0.85 if route_distance_km < 10 else 0.70
        
        # Calcular hora de llegada estimada
        from datetime import timedelta
        arrival_time = now + timedelta(minutes=predicted_eta)
        
        return {
            "eta_minutes": round(predicted_eta, 1),
            "confidence": confidence,
            "factors": {
                "distance_km": round(route_distance_km, 2),
                "vehicle_speed": vehicle.speed or 40.0,
                "is_rush_hour": is_rush,
                "severity": incident.severity,
                "hour": hour
            },
            "arrival_time": arrival_time.isoformat(),
            "model_used": "GradientBoosting" if self.is_trained else "Fallback"
        }
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calcula distancia Haversine en km"""
        R = 6371  # Radio de la Tierra en km
        
        dlat = np.radians(lat2 - lat1)
        dlon = np.radians(lon2 - lon1)
        
        a = (np.sin(dlat / 2) ** 2 +
             np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) *
             np.sin(dlon / 2) ** 2)
        
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
        
        return R * c


# Singleton global
_eta_predictor = None

def get_eta_predictor() -> ETAPredictor:
    """Obtiene instancia singleton del predictor de ETA"""
    global _eta_predictor
    if _eta_predictor is None:
        _eta_predictor = ETAPredictor()
    return _eta_predictor
