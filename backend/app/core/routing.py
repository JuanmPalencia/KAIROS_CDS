"""
Real routing using OpenStreetMap data via OSRM
Calculates actual road routes for ambulances
"""
import httpx
import json
from typing import List, Dict, Optional, Tuple
import asyncio


class OSRMRouter:
    """OpenStreetMap Routing Machine client"""
    
    def __init__(self, base_url: str = "http://router.project-osrm.org"):
        """
        Initialize OSRM router
        
        Args:
            base_url: OSRM server URL (default: public demo server)
        """
        self.base_url = base_url
        self.timeout = 10.0
    
    async def get_route(
        self,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float,
        alternatives: bool = False
    ) -> Optional[Dict]:
        """
        Get route between two points following real roads
        
        Args:
            start_lat: Starting latitude
            start_lon: Starting longitude
            end_lat: Destination latitude
            end_lon: Destination longitude
            alternatives: Whether to return alternative routes
        
        Returns:
            Dict with route data:
            {
                "distance_km": float,
                "duration_minutes": float,
                "geometry": List[Tuple[float, float]],  # List of (lat, lon)
                "steps": List[Dict]  # Turn-by-turn instructions
            }
        """
        try:
            # OSRM uses lon,lat format (not lat,lon)
            url = f"{self.base_url}/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}"
            
            params = {
                "overview": "full",  # Get full geometry
                "geometries": "geojson",  # GeoJSON format
                "steps": "true",  # Turn-by-turn instructions
                "alternatives": "true" if alternatives else "false"
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                
                if response.status_code != 200:
                    print(f"OSRM error: {response.status_code}")
                    return None
                
                data = response.json()
                
                if data.get("code") != "Ok" or not data.get("routes"):
                    print(f"OSRM no route found: {data.get('message')}")
                    return None
                
                route = data["routes"][0]
                
                # Extract geometry (list of [lon, lat] pairs)
                geometry_coords = route["geometry"]["coordinates"]
                # Convert to (lat, lon) tuples
                waypoints = [(lat, lon) for lon, lat in geometry_coords]
                
                # Extract turn-by-turn steps
                steps = []
                if "legs" in route:
                    for leg in route["legs"]:
                        for step in leg.get("steps", []):
                            steps.append({
                                "instruction": step.get("maneuver", {}).get("instruction", ""),
                                "distance_m": step.get("distance", 0),
                                "duration_s": step.get("duration", 0),
                                "location": step.get("maneuver", {}).get("location", [0, 0])
                            })
                
                return {
                    "distance_km": route["distance"] / 1000,  # meters to km
                    "duration_minutes": route["duration"] / 60,  # seconds to minutes
                    "geometry": waypoints,
                    "steps": steps,
                    "bbox": data.get("waypoints", [{}])[0].get("location", [start_lon, start_lat])
                }
        
        except Exception as e:
            print(f"Error getting route from OSRM: {e}")
            return None
    
    def get_route_sync(
        self,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float
    ) -> Optional[Dict]:
        """Synchronous route fetch using httpx sync client (safe inside async loops)"""
        try:
            url = f"{self.base_url}/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}"
            params = {
                "overview": "full",
                "geometries": "geojson",
                "steps": "false",
                "alternatives": "false"
            }
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, params=params)
                if response.status_code != 200:
                    return None
                data = response.json()
                if data.get("code") != "Ok" or not data.get("routes"):
                    return None
                route = data["routes"][0]
                geometry_coords = route["geometry"]["coordinates"]
                waypoints = [(lat, lon) for lon, lat in geometry_coords]
                return {
                    "distance_km": route["distance"] / 1000,
                    "duration_minutes": route["duration"] / 60,
                    "geometry": waypoints,
                    "steps": []
                }
        except Exception as e:
            print(f"OSRM sync error: {e}")
            return None

    @staticmethod
    def calculate_progress_on_route(
        waypoints: List[Tuple[float, float]],
        progress: float
    ) -> Tuple[float, float]:
        """Calculate current position along a route based on progress (0-1)"""
        return calculate_progress_on_route(waypoints, progress)

    @staticmethod
    def simplify_route_for_storage(
        waypoints: List[Tuple[float, float]],
        max_points: int = 50
    ) -> List[Tuple[float, float]]:
        """Simplify route by keeping only N evenly spaced waypoints"""
        return simplify_route_for_storage(waypoints, max_points)


def calculate_progress_on_route(
    waypoints: List[Tuple[float, float]],
    progress: float
) -> Tuple[float, float]:
    """
    Calculate current position along a route based on progress (0-1)
    
    Args:
        waypoints: List of (lat, lon) tuples defining the route
        progress: Float between 0 and 1 (0=start, 1=end)
    
    Returns:
        Tuple of (lat, lon) for current position
    """
    if not waypoints or len(waypoints) < 2:
        return waypoints[0] if waypoints else (0, 0)
    
    if progress <= 0:
        return waypoints[0]
    if progress >= 1:
        return waypoints[-1]
    
    # Calculate total route length
    total_distance = 0
    segment_distances = []
    
    for i in range(len(waypoints) - 1):
        lat1, lon1 = waypoints[i]
        lat2, lon2 = waypoints[i + 1]
        
        # Simple distance (could use Haversine for accuracy)
        dist = ((lat2 - lat1) ** 2 + (lon2 - lon1) ** 2) ** 0.5
        segment_distances.append(dist)
        total_distance += dist
    
    # Find position along route
    target_distance = progress * total_distance
    accumulated_distance = 0
    
    for i, seg_dist in enumerate(segment_distances):
        if accumulated_distance + seg_dist >= target_distance:
            # Position is in this segment
            segment_progress = (target_distance - accumulated_distance) / seg_dist if seg_dist > 0 else 0
            
            lat1, lon1 = waypoints[i]
            lat2, lon2 = waypoints[i + 1]
            
            # Interpolate position
            current_lat = lat1 + (lat2 - lat1) * segment_progress
            current_lon = lon1 + (lon2 - lon1) * segment_progress
            
            return (current_lat, current_lon)
        
        accumulated_distance += seg_dist
    
    # Fallback to last waypoint
    return waypoints[-1]


def simplify_route_for_storage(waypoints: List[Tuple[float, float]], max_points: int = 50) -> List[Tuple[float, float]]:
    """
    Simplify route by keeping only N evenly spaced waypoints
    Useful for database storage to reduce size
    
    Args:
        waypoints: Original waypoints list
        max_points: Maximum number of points to keep
    
    Returns:
        Simplified waypoints list
    """
    if len(waypoints) <= max_points:
        return waypoints
    
    # Keep first, last, and evenly spaced points
    step = len(waypoints) / (max_points - 1)
    indices = [int(i * step) for i in range(max_points - 1)]
    indices.append(len(waypoints) - 1)  # Always include last point
    
    return [waypoints[i] for i in indices]


# Global router instance
_router = None

def get_router() -> OSRMRouter:
    """Get or create global OSRM router instance"""
    global _router
    if _router is None:
        _router = OSRMRouter()
    return _router
