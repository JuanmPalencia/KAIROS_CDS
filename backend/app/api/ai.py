# app/api/ai.py
"""
Endpoints API para todas las funcionalidades de IA.
Exposición completa del sistema de Inteligencia Artificial.
"""
import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from ..storage.db import get_db
from ..storage.models_sql import IncidentSQL, Vehicle, Hospital
from ..auth.dependencies import get_current_user, User, require_role

# Importar todos los módulos de IA
from ..core.ai_demand_prediction import get_demand_predictor
from ..core.ai_severity_classifier import get_severity_classifier
from ..core.ai_conversational_assistant import get_assistant
from ..core.ai_anomaly_detector import get_anomaly_detector
from ..core.ai_eta_predictor import get_eta_predictor
from ..core.ai_maintenance_predictor import get_maintenance_predictor
from ..core.ai_traffic_integration import get_traffic_integration
from ..core.ai_vision_analyzer import get_vision_analyzer
from ..core.ai_recommendation_system import get_recommendation_system
from ..core.data_collector import collect_chat_interaction, collect_vision_analysis, get_dataset_stats


router = APIRouter(prefix="/api/ai", tags=["AI & Machine Learning"])


# ========== DEMAND PREDICTION ==========

@router.get("/demand/hotspots")
async def predict_hotspots(
    hours_ahead: int = 1,
    grid_size: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "OPERATOR", "VIEWER"]))
):
    """
    🔮 Predice hotspots (zonas de alta demanda) usando ML.
    
    - **hours_ahead**: Horas hacia el futuro (default: 1)
    - **grid_size**: Resolución del grid (default: 10x10)
    """
    predictor = get_demand_predictor()
    
    target_time = datetime.utcnow()
    if hours_ahead > 0:
        from datetime import timedelta
        target_time += timedelta(hours=hours_ahead)
    
    hotspots = predictor.predict_hotspots(target_time, grid_size)
    
    return {
        "hotspots": hotspots,
        "target_datetime": target_time.isoformat(),
        "grid_size": grid_size,
        "model_trained": predictor.is_trained
    }


@router.post("/demand/train")
async def train_demand_model(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    """🎓 Entrena el modelo de predicción de demanda con datos históricos."""
    predictor = get_demand_predictor()
    predictor.train_with_historical_data(db)
    
    return {
        "status": "success",
        "message": "Modelo de demanda entrenado exitosamente",
        "is_trained": predictor.is_trained
    }


# ========== SEVERITY CLASSIFICATION ==========

class SeverityClassificationRequest(BaseModel):
    description: str
    incident_type: str
    affected_count: int = 1


@router.post("/severity/classify")
async def classify_severity(
    request: SeverityClassificationRequest,
    current_user: User = Depends(require_role(["ADMIN", "OPERATOR", "DOCTOR"]))
):
    """
    🤖 Clasifica severidad de un incidente usando GPT-4.
    
    - **description**: Descripción del incidente
    - **incident_type**: Tipo (CARDIAC_ARREST, TRAFFIC_ACCIDENT, etc.)
    - **affected_count**: Número de personas afectadas
    """
    classifier = get_severity_classifier()
    
    classification = await classifier.classify_incident(
        request.description,
        request.incident_type,
        request.affected_count
    )
    
    return classification.model_dump()


# ========== CONVERSATIONAL ASSISTANT ==========

class ChatRequest(BaseModel):
    message: str
    context: Optional[dict] = None


@router.post("/chat")
async def chat_with_assistant(
    request: ChatRequest,
    current_user: User = Depends(require_role(["ADMIN", "OPERATOR", "DOCTOR", "VIEWER"]))
):
    """
    💬 Chatea con el asistente IA KAIROS.
    
    Ejemplos:
    - "¿Cuántas ambulancias disponibles hay?"
    - "Crear incidente cardíaco en coordenadas 40.41, -3.70"
    - "¿Qué hospital tiene menor carga?"
    """
    assistant = get_assistant()
    
    # Agregar contexto del usuario
    context = request.context or {}
    context["user_id"] = current_user.id
    context["username"] = current_user.username
    context["role"] = current_user.role
    
    response = await assistant.chat(request.message, context)

    # Recoger interacción anonimizada para reentrenamiento
    try:
        intent = response.get("intent", "")
        confidence = response.get("confidence", 0)
        if intent and confidence >= 0.7:
            collect_chat_interaction(request.message, intent)
    except Exception:
        pass

    return response


@router.post("/chat/clear")
async def clear_chat_history(
    current_user: User = Depends(require_role(["ADMIN", "OPERATOR", "DOCTOR", "VIEWER"]))
):
    """🧹 Limpia el historial de conversación."""
    assistant = get_assistant()
    assistant.clear_history()
    
    return {"status": "success", "message": "Historial limpiado"}


# ========== ANOMALY DETECTION ==========

@router.get("/anomalies/vehicles")
async def detect_vehicle_anomalies(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "OPERATOR", "VIEWER"]))
):
    """🚨 Detecta anomalías en la flota de vehículos."""
    detector = get_anomaly_detector()
    vehicles = db.query(Vehicle).filter(Vehicle.enabled == True).all()
    
    anomalies = detector.detect_vehicle_anomalies(vehicles, db)
    
    return {
        "anomalies": anomalies,
        "total_anomalies": len(anomalies),
        "vehicles_checked": len(vehicles),
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/anomalies/incidents")
async def detect_incident_anomalies(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "OPERATOR", "VIEWER"]))
):
    """⚠️ Detecta anomalías en incidentes (resolución demorada, etc.)."""
    detector = get_anomaly_detector()
    incidents = db.query(IncidentSQL).filter(
        IncidentSQL.status.in_(["OPEN", "ASSIGNED"])
    ).all()
    
    anomalies = detector.detect_incident_anomalies(incidents)
    
    return {
        "anomalies": anomalies,
        "total_anomalies": len(anomalies),
        "incidents_checked": len(incidents),
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/anomalies/system-health")
async def get_system_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "OPERATOR", "VIEWER"]))
):
    """📊 Score general de salud del sistema."""
    detector = get_anomaly_detector()
    health = detector.get_system_health_score(db)
    
    return health


@router.post("/anomalies/train")
async def train_anomaly_detector(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    """🎓 Entrena el detector de anomalías con baseline normal."""
    detector = get_anomaly_detector()
    detector.train_baseline(db)
    
    return {
        "status": "success",
        "message": "Detector de anomalías entrenado",
        "is_trained": detector.is_trained
    }


# ========== ETA PREDICTION ==========

@router.get("/eta/predict/{vehicle_id}/{incident_id}")
async def predict_eta(
    vehicle_id: str,
    incident_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "OPERATOR", "VIEWER"]))
):
    """⏱️ Predice ETA mejorado usando ML (considera tráfico, severidad, hora)."""
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    incident = db.query(IncidentSQL).filter(IncidentSQL.id == incident_id).first()
    
    if not vehicle or not incident:
        raise HTTPException(status_code=404, detail="Vehicle or incident not found")
    
    predictor = get_eta_predictor()
    eta_prediction = predictor.predict_eta(vehicle, incident)
    
    return eta_prediction


@router.post("/eta/train")
async def train_eta_model(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    """🎓 Entrena el modelo de predicción de ETA con datos históricos."""
    predictor = get_eta_predictor()
    predictor.train_with_historical_data(db)
    
    return {
        "status": "success",
        "message": "Modelo ETA entrenado",
        "is_trained": predictor.is_trained
    }


# ========== MAINTENANCE PREDICTION ==========

@router.get("/maintenance/predict/{vehicle_id}")
async def predict_maintenance(
    vehicle_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "OPERATOR", "VIEWER"]))
):
    """🔧 Predice necesidades de mantenimiento para un vehículo."""
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    predictor = get_maintenance_predictor()
    prediction = predictor.predict_maintenance_need(vehicle, db)
    
    return prediction


@router.get("/maintenance/fleet-schedule")
async def get_fleet_maintenance_schedule(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "OPERATOR", "VIEWER"]))
):
    """📅 Schedule de mantenimiento para toda la flota."""
    predictor = get_maintenance_predictor()
    schedule = predictor.get_fleet_maintenance_schedule(db)
    
    return schedule


# ========== TRAFFIC INTEGRATION ==========

@router.get("/traffic/route")
async def get_traffic_aware_route(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
    current_user: User = Depends(require_role(["ADMIN", "OPERATOR", "VIEWER"]))
):
    """🚦 Obtiene ruta con información de tráfico en tiempo real."""
    traffic = get_traffic_integration()
    
    route = await traffic.get_traffic_aware_route(
        start_lat, start_lon, end_lat, end_lon
    )
    
    return route


# ========== VISION ANALYSIS ==========

@router.post("/vision/analyze-incident")
async def analyze_incident_image(
    file: UploadFile = File(...),
    current_user: User = Depends(require_role(["ADMIN", "OPERATOR"]))
):
    """
    👁️ Analiza imagen de incidente usando Vision AI.
    
    - **file**: Imagen (JPEG, PNG)
    """
    # Validar tipo de archivo
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Leer imagen
    image_data = await file.read()
    
    # Limitar tamaño (5MB)
    if len(image_data) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image too large (max 5MB)")
    
    analyzer = get_vision_analyzer()
    
    # Determinar formato
    image_format = file.content_type.split("/")[-1]
    
    analysis = await analyzer.analyze_incident_image(image_data, image_format)

    # Recoger análisis anonimizado para reentrenamiento
    try:
        scene = analysis.get("scene_type", "")
        obs = analysis.get("observations", [])
        if scene and obs:
            collect_vision_analysis(scene, obs)
    except Exception:
        pass

    return analysis


@router.post("/vision/analyze-scene-safety")
async def analyze_scene_safety(
    file: UploadFile = File(...),
    current_user: User = Depends(require_role(["ADMIN", "OPERATOR"]))
):
    """🛡️ Analiza seguridad de la escena del incidente."""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    image_data = await file.read()
    
    if len(image_data) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image too large (max 5MB)")
    
    analyzer = get_vision_analyzer()
    image_format = file.content_type.split("/")[-1]
    
    safety_analysis = await analyzer.analyze_scene_safety(image_data, image_format)
    
    return safety_analysis


# ========== RECOMMENDATION SYSTEM ==========

@router.get("/recommendations/personalized/{incident_id}")
async def get_personalized_recommendations(
    incident_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "OPERATOR"]))
):
    """
    🎯 Obtiene recomendaciones personalizadas basadas en tu historial.
    
    Aprende de tus decisiones previas y sugiere basado en tus preferencias.
    """
    incident = db.query(IncidentSQL).filter(IncidentSQL.id == incident_id).first()
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Obtener sugerencia IA básica (del sistema de asignación)
    from ..core.ai_assignment import suggest_hospital_assignment, suggest_vehicle_assignment
    
    ai_hospital_suggestion = suggest_hospital_assignment(db, incident)
    ai_vehicle_suggestion = suggest_vehicle_assignment(db, incident)
    
    ai_suggestion = {
        "suggested_hospital": ai_hospital_suggestion,
        "suggested_vehicle": ai_vehicle_suggestion,
        "confidence": ai_hospital_suggestion.get("confidence", 0.5) if ai_hospital_suggestion else 0.5
    }
    
    # Obtener recomendaciones personalizadas
    rec_system = get_recommendation_system()
    personalized = rec_system.get_personalized_suggestions(
        db, current_user.id, incident, ai_suggestion
    )
    
    return personalized


@router.get("/recommendations/profile")
async def get_user_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "OPERATOR", "VIEWER"]))
):
    """👤 Obtiene tu perfil de operador y estadísticas de aprendizaje."""
    rec_system = get_recommendation_system()
    
    # Construir perfil
    profile = rec_system._build_user_profile(db, current_user.id)
    
    # Obtener insights de aprendizaje
    learning = rec_system.get_learning_insights(db, current_user.id)
    
    return {
        "profile": profile,
        "learning": learning
    }


# ========== COMBINED AI INSIGHTS ==========

@router.get("/insights/dashboard")
async def get_ai_dashboard_insights(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "OPERATOR", "VIEWER"]))
):
    """
    🧠 Dashboard completo con todos los insights de IA.
    
    Combina: hotspots, anomalías, salud del sistema, mantenimiento, etc.
    """
    # Demand prediction
    predictor = get_demand_predictor()
    hotspots = predictor.predict_hotspots(datetime.utcnow(), grid_size=8)
    
    # Anomalies
    detector = get_anomaly_detector()
    system_health = detector.get_system_health_score(db)
    vehicles = db.query(Vehicle).filter(Vehicle.enabled == True).all()
    vehicle_anomalies = detector.detect_vehicle_anomalies(vehicles, db)
    
    # Maintenance
    maintenance_pred = get_maintenance_predictor()
    fleet_schedule = maintenance_pred.get_fleet_maintenance_schedule(db)
    
    # User profile
    rec_system = get_recommendation_system()
    user_profile = rec_system._build_user_profile(db, current_user.id)
    
    return {
        "system_health": system_health,
        "hotspots": hotspots[:5],  # Top 5
        "anomalies": {
            "vehicles": len(vehicle_anomalies),
            "critical": len([a for a in vehicle_anomalies if a["severity"] == "HIGH"])
        },
        "maintenance": {
            "urgent": len(fleet_schedule["urgent_maintenance"]),
            "fleet_health": fleet_schedule["fleet_health_score"]
        },
        "user": {
            "experience_level": user_profile["experience_level"],
            "ai_acceptance_rate": user_profile["ai_acceptance_rate"]
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/status")
async def get_ai_status(
    current_user: User = Depends(require_role(["ADMIN", "OPERATOR", "VIEWER"]))
):
    """ℹ️ Estado de todos los módulos de IA."""
    predictor = get_demand_predictor()
    classifier = get_severity_classifier()
    assistant = get_assistant()
    detector = get_anomaly_detector()
    eta_pred = get_eta_predictor()
    vision = get_vision_analyzer()
    
    return {
        "modules": {
            "demand_prediction": {
                "enabled": True,
                "trained": predictor.is_trained
            },
            "severity_classifier": {
                "enabled": classifier.enabled,
                "provider": "Local ML (sklearn)" if classifier.enabled else "Rules-based"
            },
            "conversational_assistant": {
                "enabled": assistant.enabled,
                "provider": "Local ML (sklearn)" if assistant.enabled else "Disabled"
            },
            "anomaly_detector": {
                "enabled": True,
                "trained": detector.is_trained
            },
            "eta_predictor": {
                "enabled": True,
                "trained": eta_pred.is_trained
            },
            "maintenance_predictor": {
                "enabled": True
            },
            "traffic_integration": {
                "enabled": True,
                "provider": "Mock (configurable)"
            },
            "vision_analyzer": {
                "enabled": vision.enabled,
                "provider": "Local ML (sklearn + Pillow)" if vision.enabled else "Disabled"
            },
            "recommendation_system": {
                "enabled": True
            }
        },
        "local_models_loaded": classifier.enabled,
        "anonymization": "enabled",
        "continuous_learning": "enabled",
        "timestamp": datetime.utcnow().isoformat()
    }


# ========== DATASET & RETRAINING ==========

@router.get("/datasets/stats")
async def get_datasets_info(
    current_user: User = Depends(require_role(["ADMIN"]))
):
    """📊 Estadísticas de los datasets de reentrenamiento (datos anonimizados)."""
    stats = get_dataset_stats()
    return {
        "datasets": stats,
        "anonymization": "RGPD-compliant (supresión + generalización + perturbación)",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.post("/retrain")
async def retrain_all_models(
    current_user: User = Depends(require_role(["ADMIN"]))
):
    """
    🔄 Re-entrena TODOS los modelos de IA con los datasets actualizados.

    Los datasets se alimentan automáticamente con datos operativos
    anonimizados (incidentes, chat, visión). Este endpoint ejecuta
    el script de entrenamiento unificado.
    """
    import subprocess
    import sys

    train_script = os.path.join(
        os.path.dirname(__file__), "..", "..", "train_all_models.py"
    )
    train_script = os.path.abspath(train_script)

    if not os.path.exists(train_script):
        raise HTTPException(status_code=500, detail="train_all_models.py not found")

    try:
        result = subprocess.run(
            [sys.executable, train_script],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=os.path.dirname(train_script),
        )

        success = result.returncode == 0
        return {
            "status": "success" if success else "error",
            "message": "Modelos re-entrenados correctamente" if success else "Error en re-entrenamiento",
            "stdout": result.stdout[-2000:] if result.stdout else "",
            "stderr": result.stderr[-500:] if result.stderr else "",
            "datasets": get_dataset_stats(),
            "timestamp": datetime.utcnow().isoformat(),
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Retraining timed out (120s)")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retraining failed: {str(e)}")
