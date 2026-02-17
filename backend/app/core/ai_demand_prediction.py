# app/core/ai_demand_prediction.py
"""
Predicción de demanda de incidentes usando Machine Learning.
Predice hotspots (zonas calientes) basado en patrones históricos.
"""
import numpy as np
from datetime import datetime, timedelta
from typing import List, Optional
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib
import os
from sqlalchemy.orm import Session
from ..storage.models_sql import IncidentSQL


class DemandPredictor:
    """Predictor de demanda de incidentes basado en Machine Learning"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.model_path = "models/demand_predictor.joblib"
        self.scaler_path = "models/demand_scaler.joblib"
        
        # Intentar cargar modelo existente
        self._load_model()
    
    def _load_model(self):
        """Carga modelo pre-entrenado si existe"""
        if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
            try:
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                self.is_trained = True
                print("✅ Demand predictor model loaded")
            except Exception as e:
                print(f"⚠️ Could not load demand model: {e}")
    
    def _save_model(self):
        """Guarda modelo entrenado"""
        os.makedirs("models", exist_ok=True)
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.scaler, self.scaler_path)
        print("✅ Demand predictor model saved")
    
    def _extract_features(self, dt: datetime, lat: float, lon: float) -> np.ndarray:
        """Extrae features temporales y geográficos"""
        features = [
            dt.hour,  # 0-23
            dt.weekday(),  # 0-6 (lunes-domingo)
            dt.month,  # 1-12
            dt.day,  # 1-31
            1 if dt.weekday() >= 5 else 0,  # es_fin_de_semana
            1 if 22 <= dt.hour or dt.hour <= 6 else 0,  # es_noche
            1 if 7 <= dt.hour <= 9 or 17 <= dt.hour <= 19 else 0,  # hora_pico
            lat,
            lon
        ]
        return np.array(features).reshape(1, -1)
    
    def train_with_historical_data(self, db: Session, min_incidents: int = 50):
        """Entrena modelo con datos históricos de la base de datos"""
        # Obtener todos los incidentes históricos
        incidents = db.query(IncidentSQL).all()
        
        if len(incidents) < min_incidents:
            print(f"⚠️ Not enough data for training ({len(incidents)} < {min_incidents})")
            # Generar datos sintéticos para demostración
            return self._train_with_synthetic_data()
        
        # Preparar dataset
        X = []
        y = []
        
        for inc in incidents:
            features = self._extract_features(inc.created_at, inc.lat, inc.lon)
            X.append(features[0])
            # Severidad como target (1-4)
            severity_map = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
            y.append(severity_map.get(inc.severity, 2))
        
        X = np.array(X)
        y = np.array(y)
        
        # Entrenar modelo
        X_scaled = self.scaler.fit_transform(X)
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.model.fit(X_scaled, y)
        self.is_trained = True
        
        self._save_model()
        print(f"✅ Model trained with {len(incidents)} incidents")
    
    def _train_with_synthetic_data(self):
        """Genera datos sintéticos para entrenar el modelo (demo)"""
        print("🔄 Training with synthetic data...")
        
        np.random.seed(42)
        n_samples = 500
        
        # Generar features sintéticos
        X = []
        y = []
        
        # Madrid centro: más incidentes en hora pico y noches de fin de semana
        for _ in range(n_samples):
            hour = np.random.randint(0, 24)
            weekday = np.random.randint(0, 7)
            month = np.random.randint(1, 13)
            day = np.random.randint(1, 29)
            lat = 40.4168 + np.random.uniform(-0.05, 0.05)
            lon = -3.7038 + np.random.uniform(-0.05, 0.05)
            
            is_weekend = 1 if weekday >= 5 else 0
            is_night = 1 if 22 <= hour or hour <= 6 else 0
            is_rush_hour = 1 if 7 <= hour <= 9 or 17 <= hour <= 19 else 0
            
            features = [hour, weekday, month, day, is_weekend, is_night, is_rush_hour, lat, lon]
            
            # Severidad más alta en noches de fin de semana y hora pico
            base_severity = 1.5
            if is_weekend and is_night:
                base_severity += 1.5
            if is_rush_hour:
                base_severity += 0.8
            if 40.41 < lat < 40.425 and -3.71 < lon < -3.695:  # Centro de Madrid
                base_severity += 0.5
            
            severity = np.clip(base_severity + np.random.normal(0, 0.5), 1, 4)
            
            X.append(features)
            y.append(severity)
        
        X = np.array(X)
        y = np.array(y)
        
        # Entrenar
        X_scaled = self.scaler.fit_transform(X)
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.model.fit(X_scaled, y)
        self.is_trained = True
        
        self._save_model()
        print(f"✅ Model trained with {n_samples} synthetic samples")
    
    def predict_hotspots(
        self,
        target_datetime: Optional[datetime] = None,
        grid_size: int = 10
    ) -> List[dict]:
        """
        Predice hotspots (zonas de alta demanda) para un momento específico.
        
        Args:
            target_datetime: Momento para predecir (default: ahora)
            grid_size: Número de puntos en la cuadrícula (grid_size x grid_size)
        
        Returns:
            Lista de hotspots: [{"lat": float, "lon": float, "severity": float, "probability": float}]
        """
        if not self.is_trained:
            print("⚠️ Model not trained yet, training with synthetic data...")
            self._train_with_synthetic_data()
        
        if target_datetime is None:
            target_datetime = datetime.utcnow()
        
        # Crear grid sobre Madrid
        madrid_lat_range = (40.35, 40.50)
        madrid_lon_range = (-3.75, -3.65)
        
        lats = np.linspace(madrid_lat_range[0], madrid_lat_range[1], grid_size)
        lons = np.linspace(madrid_lon_range[0], madrid_lon_range[1], grid_size)
        
        hotspots = []
        
        for lat in lats:
            for lon in lons:
                features = self._extract_features(target_datetime, lat, lon)
                features_scaled = self.scaler.transform(features)
                predicted_severity = self.model.predict(features_scaled)[0]
                
                # Solo incluir si la severidad predicha es significativa
                if predicted_severity > 1.8:
                    hotspots.append({
                        "lat": round(lat, 4),
                        "lon": round(lon, 4),
                        "severity": round(predicted_severity, 2),
                        "probability": round(min(predicted_severity / 4.0, 1.0), 2),
                        "timestamp": target_datetime.isoformat()
                    })
        
        # Ordenar por severidad descendente
        hotspots.sort(key=lambda x: x["severity"], reverse=True)
        
        return hotspots[:20]  # Top 20 hotspots
    
    def predict_demand_for_hour(self, hour: int, weekday: int) -> float:
        """Predice demanda agregada para una hora y día específicos"""
        if not self.is_trained:
            self._train_with_synthetic_data()
        
        # Promediar predicciones sobre toda la ciudad
        total_severity = 0
        n_points = 25
        
        madrid_lat_range = (40.35, 40.50)
        madrid_lon_range = (-3.75, -3.65)
        
        lats = np.linspace(madrid_lat_range[0], madrid_lat_range[1], 5)
        lons = np.linspace(madrid_lon_range[0], madrid_lon_range[1], 5)
        
        for lat in lats:
            for lon in lons:
                dt = datetime.now().replace(hour=hour, minute=0, second=0)
                dt = dt + timedelta(days=(weekday - dt.weekday()))
                features = self._extract_features(dt, lat, lon)
                features_scaled = self.scaler.transform(features)
                severity = self.model.predict(features_scaled)[0]
                total_severity += severity
        
        return round(total_severity / n_points, 2)


# Singleton global
_demand_predictor = None

def get_demand_predictor() -> DemandPredictor:
    """Obtiene instancia singleton del predictor"""
    global _demand_predictor
    if _demand_predictor is None:
        _demand_predictor = DemandPredictor()
    return _demand_predictor
