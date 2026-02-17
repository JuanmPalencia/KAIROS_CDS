from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import List, Dict, Any

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


class AlertWebhook(BaseModel):
    receiver: str
    status: str
    alerts: List[Dict[str, Any]]
    groupLabels: Dict[str, str]
    commonLabels: Dict[str, str]
    commonAnnotations: Dict[str, str]
    externalURL: str
    version: str
    groupKey: str


@router.post("/webhook")
async def receive_alert(webhook: AlertWebhook, request: Request):
    """Receive alerts from Alertmanager"""
    print(f"🚨 ALERT RECEIVED: {webhook.status}")
    
    for alert in webhook.alerts:
        alertname = alert.get("labels", {}).get("alertname", "Unknown")
        severity = alert.get("labels", {}).get("severity", "unknown")
        status = alert.get("status", "unknown")
        
        print(f"  - {alertname} [{severity}] - Status: {status}")
        
        if "annotations" in alert:
            summary = alert["annotations"].get("summary", "")
            description = alert["annotations"].get("description", "")
            if summary:
                print(f"    Summary: {summary}")
            if description:
                print(f"    Description: {description}")
    
    return {"status": "received", "count": len(webhook.alerts)}


@router.get("/test")
async def test_alerts():
    """Test endpoint"""
    return {"status": "alerts endpoint is working"}
