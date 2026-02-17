from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Optional

from ..storage.db import get_db
from ..storage.models_sql import IncidentSQL, Vehicle
from ..auth.dependencies import get_current_user, User

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/dashboard")
async def get_dashboard_metrics(
    days: int = Query(7, ge=1, le=90),
    city: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get dashboard analytics for the last N days"""
    since = datetime.utcnow() - timedelta(days=days)
    
    # Base incident query with optional city filter
    base_q = db.query(IncidentSQL).filter(IncidentSQL.created_at >= since)
    if city:
        base_q = base_q.filter(IncidentSQL.city == city)
    
    # Total incidents
    total_incidents = base_q.count()
    
    # Average response time (in minutes)
    resolved = base_q.filter(
        IncidentSQL.status == "RESOLVED",
        IncidentSQL.resolved_at.isnot(None),
    ).all()
    
    avg_response_time = 0
    if resolved:
        times = [(inc.resolved_at - inc.created_at).total_seconds() / 60 for inc in resolved]
        avg_response_time = round(sum(times) / len(times), 2)
    
    # Resolution rate
    resolution_rate = round((len(resolved) / total_incidents * 100), 2) if total_incidents > 0 else 0
    
    # Active vehicles
    active_vehicles = db.query(Vehicle).filter(Vehicle.enabled == True).count()
    
    # Fleet utilization
    in_use = db.query(Vehicle).filter(
        Vehicle.enabled == True,
        Vehicle.status == "EN_ROUTE"
    ).count()
    fleet_utilization = round((in_use / active_vehicles * 100), 2) if active_vehicles > 0 else 0
    
    # Incidents by type
    type_q = db.query(
        IncidentSQL.incident_type,
        func.count(IncidentSQL.id).label("count")
    ).filter(IncidentSQL.created_at >= since)
    if city:
        type_q = type_q.filter(IncidentSQL.city == city)
    incidents_by_type = type_q.group_by(IncidentSQL.incident_type).all()
    
    # Incidents by severity
    sev_q = db.query(
        IncidentSQL.severity,
        func.count(IncidentSQL.id).label("count")
    ).filter(IncidentSQL.created_at >= since)
    if city:
        sev_q = sev_q.filter(IncidentSQL.city == city)
    incidents_by_severity = sev_q.group_by(IncidentSQL.severity).order_by(IncidentSQL.severity).all()
    
    # Hourly distribution (last 24 hours)
    last_24h = datetime.utcnow() - timedelta(hours=24)
    hourly_incidents = []
    for i in range(24):
        hour_start = last_24h + timedelta(hours=i)
        hour_end = hour_start + timedelta(hours=1)
        hour_q = db.query(IncidentSQL).filter(
            IncidentSQL.created_at >= hour_start,
            IncidentSQL.created_at < hour_end
        )
        if city:
            hour_q = hour_q.filter(IncidentSQL.city == city)
        count = hour_q.count()
        hourly_incidents.append({
            "hour": hour_start.strftime("%H:00"),
            "count": count
        })
    
    return {
        "period_days": days,
        "summary": {
            "total_incidents": total_incidents,
            "avg_response_time_min": avg_response_time,
            "resolution_rate": resolution_rate,
            "active_vehicles": active_vehicles,
            "fleet_utilization": fleet_utilization
        },
        "incidents_by_type": [
            {"type": t, "count": c} for t, c in incidents_by_type
        ],
        "incidents_by_severity": [
            {"severity": s, "count": c} for s, c in incidents_by_severity
        ],
        "hourly_distribution": hourly_incidents
    }


@router.get("/response-times")
async def get_response_times(
    days: int = Query(7, ge=1, le=90),
    city: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get response time distribution over time"""
    since = datetime.utcnow() - timedelta(days=days)
    
    rt_q = db.query(IncidentSQL).filter(
        IncidentSQL.status == "RESOLVED",
        IncidentSQL.resolved_at.isnot(None),
        IncidentSQL.created_at >= since
    )
    if city:
        rt_q = rt_q.filter(IncidentSQL.city == city)
    resolved = rt_q.order_by(IncidentSQL.created_at).all()
    
    data = []
    for inc in resolved:
        response_time = (inc.resolved_at - inc.created_at).total_seconds() / 60
        data.append({
            "incident_id": inc.id,
            "created_at": inc.created_at.isoformat(),
            "response_time_min": round(response_time, 2),
            "severity": inc.severity,
            "type": inc.incident_type
        })
    
    return {
        "period_days": days,
        "count": len(data),
        "data": data
    }


@router.get("/areas")
async def get_area_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get statistics by area/city"""
    areas = db.query(
        IncidentSQL.city,
        func.count(IncidentSQL.id).label("total_incidents")
    ).filter(
        IncidentSQL.city.isnot(None)
    ).group_by(IncidentSQL.city).all()
    
    result = []
    for city, count in areas:
        # Calculate avg response time for this city
        resolved = db.query(IncidentSQL).filter(
            IncidentSQL.city == city,
            IncidentSQL.status == "RESOLVED",
            IncidentSQL.resolved_at.isnot(None)
        ).all()
        
        avg_time = 0
        if resolved:
            times = [(inc.resolved_at - inc.created_at).total_seconds() / 60 for inc in resolved]
            avg_time = round(sum(times) / len(times), 2)
        
        efficiency = round((len(resolved) / count * 100), 2) if count > 0 else 0
        
        result.append({
            "area": city,
            "incidents": count,
            "avg_response_time_min": avg_time,
            "efficiency": efficiency
        })
    
    return {"areas": result}
