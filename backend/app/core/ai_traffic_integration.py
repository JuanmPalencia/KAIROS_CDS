# app/core/ai_traffic_integration.py
"""
Integración de datos de tráfico real para mejorar rutas.
Puede usar Google Maps Traffic API, TomTom, o HERE Maps.
"""
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
import httpx


class TrafficIntegration:
    """Integración con APIs de tráfico en tiempo real"""
    
    def __init__(self, api_key: Optional[str] = None, provider: str = "google"):
        """
        Args:
            api_key: API key del proveedor (Google/TomTom/HERE)
            provider: "google" | "tomtom" | "here" | "mock"
        """
        self.api_key = api_key or os.getenv("TRAFFIC_API_KEY", "")
        self.provider = provider
        self.enabled = bool(self.api_key and self.api_key != "") or provider == "mock"
        self.base_urls = {
            "google": "https://maps.googleapis.com/maps/api/directions/json",
            "tomtom": "https://api.tomtom.com/routing/1/calculateRoute",
            "here": "https://router.hereapi.com/v8/routes"
        }
        
        if self.enabled:
            print(f"✅ Traffic Integration enabled ({provider})")
        else:
            print(f"⚠️ Traffic Integration disabled (no API key)")
    
    async def get_traffic_aware_route(
        self,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float,
        departure_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Obtiene ruta optimizada considerando tráfico en tiempo real.
        
        Returns:
            {
                "distance_km": float,
                "duration_minutes": float,
                "duration_in_traffic": float,
                "traffic_delay_minutes": float,
                "traffic_level": "LOW" | "MODERATE" | "HIGH" | "HEAVY",
                "alternative_routes": [...],
                "waypoints": [...],
                "traffic_incidents": [...]
            }
        """
        if not self.enabled:
            return self._mock_traffic_response(start_lat, start_lon, end_lat, end_lon)
        
        if self.provider == "mock":
            return self._mock_traffic_response(start_lat, start_lon, end_lat, end_lon)
        
        try:
            if self.provider == "google":
                return await self._get_google_traffic_route(
                    start_lat, start_lon, end_lat, end_lon, departure_time
                )
            elif self.provider == "tomtom":
                return await self._get_tomtom_traffic_route(
                    start_lat, start_lon, end_lat, end_lon
                )
            else:
                return self._mock_traffic_response(start_lat, start_lon, end_lat, end_lon)
        
        except Exception as e:
            print(f"⚠️ Traffic API error: {e}")
            return self._mock_traffic_response(start_lat, start_lon, end_lat, end_lon)
    
    async def _get_google_traffic_route(
        self,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float,
        departure_time: Optional[datetime]
    ) -> Dict[str, Any]:
        """Obtiene ruta de Google Maps con tráfico"""
        url = self.base_urls["google"]
        
        params = {
            "origin": f"{start_lat},{start_lon}",
            "destination": f"{end_lat},{end_lon}",
            "mode": "driving",
            "departure_time": "now",  # o timestamp futuro
            "traffic_model": "best_guess",  # best_guess, pessimistic, optimistic
            "alternatives": "true",
            "key": self.api_key
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=5.0)
            response.raise_for_status()
            data = response.json()
        
        if data["status"] != "OK" or not data.get("routes"):
            raise Exception(f"Google API error: {data.get('status')}")
        
        main_route = data["routes"][0]
        leg = main_route["legs"][0]
        
        duration_normal = leg["duration"]["value"] / 60  # segundos a minutos
        duration_traffic = leg.get("duration_in_traffic", {}).get("value", duration_normal) / 60
        traffic_delay = duration_traffic - duration_normal
        
        # Determinar nivel de tráfico
        if traffic_delay < 5:
            traffic_level = "LOW"
        elif traffic_delay < 15:
            traffic_level = "MODERATE"
        elif traffic_delay < 30:
            traffic_level = "HIGH"
        else:
            traffic_level = "HEAVY"
        
        return {
            "distance_km": leg["distance"]["value"] / 1000,
            "duration_minutes": duration_normal,
            "duration_in_traffic": duration_traffic,
            "traffic_delay_minutes": traffic_delay,
            "traffic_level": traffic_level,
            "alternative_routes": len(data["routes"]) - 1,
            "provider": "google",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _get_tomtom_traffic_route(
        self,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float
    ) -> Dict[str, Any]:
        """Obtiene ruta de TomTom con tráfico"""
        # Implementación similar para TomTom
        url = f"{self.base_urls['tomtom']}/{start_lat},{start_lon}:{end_lat},{end_lon}/json"
        
        params = {
            "key": self.api_key,
            "traffic": "true",
            "routeType": "fastest"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=5.0)
            response.raise_for_status()
            data = response.json()
        
        route = data["routes"][0]
        summary = route["summary"]
        
        duration_normal = summary["travelTimeInSeconds"] / 60
        duration_traffic = summary["trafficDelayInSeconds"] / 60
        
        return {
            "distance_km": summary["lengthInMeters"] / 1000,
            "duration_minutes": duration_normal,
            "duration_in_traffic": duration_normal + duration_traffic,
            "traffic_delay_minutes": duration_traffic,
            "traffic_level": "MODERATE",  # TomTom no proporciona nivel directamente
            "provider": "tomtom",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _mock_traffic_response(
        self,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float
    ) -> Dict[str, Any]:
        """Genera respuesta mock con tráfico simulado"""
        import math
        
        # Calcular distancia Haversine básica
        R = 6371
        dlat = math.radians(end_lat - start_lat)
        dlon = math.radians(end_lon - start_lon)
        
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(start_lat)) * math.cos(math.radians(end_lat)) *
             math.sin(dlon / 2) ** 2)
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance_km = R * c
        
        # Simular tráfico basado en hora del día
        hour = datetime.utcnow().hour
        
        if 7 <= hour <= 9 or 17 <= hour <= 19:  # Hora pico
            traffic_multiplier = 1.5
            traffic_level = "HIGH"
        elif 22 <= hour or hour <= 6:  # Noche
            traffic_multiplier = 0.8
            traffic_level = "LOW"
        else:
            traffic_multiplier = 1.0
            traffic_level = "MODERATE"
        
        base_duration = (distance_km / 40) * 60  # 40 km/h promedio
        duration_with_traffic = base_duration * traffic_multiplier
        traffic_delay = duration_with_traffic - base_duration
        
        return {
            "distance_km": round(distance_km, 2),
            "duration_minutes": round(base_duration, 1),
            "duration_in_traffic": round(duration_with_traffic, 1),
            "traffic_delay_minutes": round(traffic_delay, 1),
            "traffic_level": traffic_level,
            "alternative_routes": 0,
            "provider": "mock",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def should_recalculate_route(
        self,
        current_traffic_level: str,
        initial_traffic_level: str,
        time_elapsed_minutes: float
    ) -> bool:
        """
        Determina si se debe recalcular la ruta debido a cambios en el tráfico.
        
        Returns:
            True si se recomienda recalcular
        """
        # Recalcular si el tráfico empeoró significativamente
        traffic_levels = {"LOW": 1, "MODERATE": 2, "HIGH": 3, "HEAVY": 4}
        
        current_level = traffic_levels.get(current_traffic_level, 2)
        initial_level = traffic_levels.get(initial_traffic_level, 2)
        
        # Si el tráfico subió 2+ niveles, recalcular
        if current_level - initial_level >= 2:
            return True
        
        # Si ha pasado mucho tiempo (>30 min), recalcular
        if time_elapsed_minutes > 30:
            return True
        
        return False


# Singleton global
_traffic_integration = None

def get_traffic_integration() -> TrafficIntegration:
    """Obtiene instancia singleton de integración de tráfico"""
    global _traffic_integration
    if _traffic_integration is None:
        _traffic_integration = TrafficIntegration(provider="mock")  # Default: mock
    return _traffic_integration
