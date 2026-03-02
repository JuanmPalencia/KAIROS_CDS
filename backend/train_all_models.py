#!/usr/bin/env python3
"""
KAIROS CDS — Script unificado de entrenamiento de TODOS los modelos de IA.

Ejecutar:
    cd backend
    python train_all_models.py

Entrena y persiste:
  1. Severity Classifier   (TF-IDF + RandomForest)       → models/severity_classifier.joblib
  2. Chat Intent Classifier (TF-IDF + LogisticRegression) → models/chat_intent_model.joblib
  3. Vision Scene Classifier(TF-IDF + SVM)                → models/vision_scene_model.joblib
  4. Demand Predictor       (RandomForest, ya existente)   → models/demand_predictor.joblib
  5. ETA Predictor          (GradientBoosting)             → models/eta_predictor.joblib
  6. Anomaly Detector       (IsolationForest)              → models/anomaly_detector.joblib
"""

import os
import sys
import csv
import json
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import (
    RandomForestClassifier,
    RandomForestRegressor,
    GradientBoostingRegressor,
    IsolationForest,
)
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import cross_val_score
from sklearn.metrics import classification_report, accuracy_score

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
DATASETS_DIR = os.path.join(os.path.dirname(__file__), "datasets")

os.makedirs(MODELS_DIR, exist_ok=True)


# ─────────────────────────────────────────────────────────────────
# 1. SEVERITY CLASSIFIER
# ─────────────────────────────────────────────────────────────────

def train_severity_classifier():
    """Entrena clasificador de severidad con TF-IDF + RandomForest."""
    print("\n" + "=" * 60)
    print("🔴 ENTRENANDO: Severity Classifier")
    print("=" * 60)

    csv_path = os.path.join(DATASETS_DIR, "severity_dataset.csv")
    df = pd.read_csv(csv_path)

    # Rellenar NaN en response_time con mediana por severidad
    df["response_time"] = df.groupby("severity")["response_time"].transform(
        lambda s: s.fillna(s.median())
    )
    # Si aún quedan NaN (severidad sin datos), rellenar con mediana global
    df["response_time"] = df["response_time"].fillna(df["response_time"].median())

    print(f"   Dataset: {len(df)} muestras")
    print(f"   Distribución: {dict(df['severity'].value_counts())}")

    # Crear feature combinando descripción + tipo + affected
    df["text_feature"] = (
        df["description"]
        + " TIPO:" + df["incident_type"]
        + " AFECTADOS:" + df["affected_count"].astype(str)
    )

    X = df["text_feature"].values
    y_severity = df["severity"].values
    y_response_time = df["response_time"].values
    specialties_list = df["specialties"].values

    # Pipeline severity
    severity_pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            max_features=3000,
            ngram_range=(1, 2),
            sublinear_tf=True,
            strip_accents="unicode",
        )),
        ("clf", RandomForestClassifier(
            n_estimators=200,
            max_depth=20,
            random_state=42,
            class_weight="balanced",
        )),
    ])

    severity_pipeline.fit(X, y_severity)

    # Evaluar
    scores = cross_val_score(severity_pipeline, X, y_severity, cv=5, scoring="accuracy")
    print(f"   Accuracy (5-fold CV): {scores.mean():.2%} ± {scores.std():.2%}")

    y_pred = severity_pipeline.predict(X)
    print(f"   Train accuracy: {accuracy_score(y_severity, y_pred):.2%}")

    # Pipeline response time
    rt_pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            max_features=2000,
            ngram_range=(1, 2),
            sublinear_tf=True,
            strip_accents="unicode",
        )),
        ("reg", GradientBoostingRegressor(
            n_estimators=100,
            max_depth=5,
            random_state=42,
        )),
    ])
    rt_pipeline.fit(X, y_response_time)

    # Mapeo de especialidades por tipo de incidente (lookup table)
    specialty_map = {}
    for _, row in df.iterrows():
        key = (row["incident_type"], row["severity"])
        if key not in specialty_map:
            specialty_map[key] = row["specialties"]

    # Guardar todo junto
    model_data = {
        "severity_pipeline": severity_pipeline,
        "response_time_pipeline": rt_pipeline,
        "specialty_map": specialty_map,
        "label_classes": list(severity_pipeline.classes_),
        "version": "1.0.0",
        "trained_at": datetime.utcnow().isoformat(),
        "samples": len(df),
    }

    out_path = os.path.join(MODELS_DIR, "severity_classifier.joblib")
    joblib.dump(model_data, out_path)
    print(f"   ✅ Guardado: {out_path} ({os.path.getsize(out_path) / 1024:.0f} KB)")

    return model_data


# ─────────────────────────────────────────────────────────────────
# 2. CHAT INTENT CLASSIFIER
# ─────────────────────────────────────────────────────────────────

def train_chat_intent_classifier():
    """Entrena clasificador de intents para el chatbot con TF-IDF + Logistic."""
    print("\n" + "=" * 60)
    print("💬 ENTRENANDO: Chat Intent Classifier")
    print("=" * 60)

    csv_path = os.path.join(DATASETS_DIR, "chat_intents_dataset.csv")
    df = pd.read_csv(csv_path)
    print(f"   Dataset: {len(df)} muestras")
    print(f"   Intents: {dict(df['intent'].value_counts())}")

    X = df["text"].values
    y = df["intent"].values

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            max_features=2000,
            ngram_range=(1, 3),
            sublinear_tf=True,
            strip_accents="unicode",
        )),
        ("clf", LogisticRegression(
            max_iter=1000,
            C=5.0,
            class_weight="balanced",
            random_state=42,
        )),
    ])

    pipeline.fit(X, y)

    scores = cross_val_score(pipeline, X, y, cv=5, scoring="accuracy")
    print(f"   Accuracy (5-fold CV): {scores.mean():.2%} ± {scores.std():.2%}")

    y_pred = pipeline.predict(X)
    print(f"   Train accuracy: {accuracy_score(y, y_pred):.2%}")

    # Templates de respuesta por intent
    response_templates = {
        "fleet_status": [
            "🚑 **Estado de la flota:**\n{fleet_data}",
            "📊 Aquí tienes el estado actual de las ambulancias:\n{fleet_data}",
        ],
        "incidents_summary": [
            "🚨 **Resumen de incidentes:**\n{incidents_data}",
            "📋 Incidentes activos en el sistema:\n{incidents_data}",
        ],
        "hospital_capacity": [
            "🏥 **Capacidad hospitalaria:**\n{hospital_data}",
            "📊 Estado de los hospitales:\n{hospital_data}",
        ],
        "create_incident": [
            "⚠️ Para crear un incidente, proporciona:\n- **Tipo**: CARDIAC_ARREST, TRAFFIC_ACCIDENT, RESPIRATORY, etc.\n- **Ubicación**: coordenadas o dirección\n- **Descripción**: qué está ocurriendo\n\nUsa el formulario de creación de incidentes en el panel o indica los datos.",
        ],
        "analytics": [
            "📈 **Métricas del sistema:**\n{analytics_data}",
            "📊 Resumen de rendimiento:\n{analytics_data}",
        ],
        "hotspots": [
            "🔥 **Predicción de zonas calientes:**\n{hotspot_data}",
            "📍 Zonas de alta demanda previstas:\n{hotspot_data}",
        ],
        "greeting": [
            "👋 ¡Hola! Soy **KAIROS AI**, tu asistente de emergencias. ¿En qué puedo ayudarte?\n\nPuedo informarte sobre:\n🚑 Estado de la flota\n🚨 Incidentes activos\n🏥 Capacidad hospitalaria\n📊 Métricas y analytics\n🔥 Predicción de demanda",
            "¡Buenos días! 🚑 Soy KAIROS AI. Pregúntame sobre flota, incidentes, hospitales o predicciones.",
        ],
        "help": [
            "ℹ️ **Mis capacidades:**\n\n🚑 **Flota**: \"estado de la flota\", \"ambulancias disponibles\"\n🚨 **Incidentes**: \"incidentes abiertos\", \"emergencias activas\"\n🏥 **Hospitales**: \"capacidad hospitalaria\", \"hospital con camas\"\n📊 **Analytics**: \"métricas\", \"tiempo de respuesta\"\n🔥 **Predicción**: \"hotspots\", \"predecir demanda\"\n➕ **Crear**: \"crear incidente\", \"nueva emergencia\"",
        ],
    }

    # Guardar
    model_data = {
        "pipeline": pipeline,
        "response_templates": response_templates,
        "intent_classes": list(pipeline.classes_),
        "version": "1.0.0",
        "trained_at": datetime.utcnow().isoformat(),
        "samples": len(df),
    }

    out_path = os.path.join(MODELS_DIR, "chat_intent_model.joblib")
    joblib.dump(model_data, out_path)
    print(f"   ✅ Guardado: {out_path} ({os.path.getsize(out_path) / 1024:.0f} KB)")

    return model_data


# ─────────────────────────────────────────────────────────────────
# 3. VISION SCENE CLASSIFIER
# ─────────────────────────────────────────────────────────────────

def train_vision_scene_classifier():
    """Entrena clasificador de escenas con TF-IDF + SVM sobre metadatos de imagen."""
    print("\n" + "=" * 60)
    print("👁️ ENTRENANDO: Vision Scene Classifier")
    print("=" * 60)

    csv_path = os.path.join(DATASETS_DIR, "vision_scenes_dataset.csv")
    df = pd.read_csv(csv_path)
    print(f"   Dataset: {len(df)} muestras")
    print(f"   Clases: {dict(df['label'].value_counts())}")

    X = df["description"].values
    y = df["label"].values

    # Pipeline TF-IDF + SVM (para clasificar descripciones/metadata de escena)
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            max_features=2000,
            ngram_range=(1, 2),
            sublinear_tf=True,
            strip_accents="unicode",
        )),
        ("clf", LinearSVC(
            C=1.0,
            max_iter=2000,
            class_weight="balanced",
            random_state=42,
        )),
    ])

    pipeline.fit(X, y)

    scores = cross_val_score(pipeline, X, y, cv=3, scoring="accuracy")
    print(f"   Accuracy (3-fold CV): {scores.mean():.2%} ± {scores.std():.2%}")

    # Mapeo de escena → análisis de seguridad
    scene_analysis_map = {
        "TRAFFIC_ACCIDENT": {
            "injury_type": "TRAUMA",
            "default_severity": "HIGH",
            "hazards": ["Vehículos inestables", "Tráfico activo", "Posible derrame de combustible"],
            "equipment": ["Collarín cervical", "Tabla espinal", "Kit de extricación"],
            "is_safe": False,
            "access_difficulty": "MODERATE",
            "recommendations": [
                "Señalizar la zona del accidente",
                "Cortar el tráfico en ambos sentidos",
                "Verificar estabilidad de vehículos antes de acceder",
            ],
        },
        "FIRE_SCENE": {
            "injury_type": "BURNS",
            "default_severity": "CRITICAL",
            "hazards": ["Llamas activas", "Humo tóxico", "Estructura inestable", "Riesgo de explosión"],
            "equipment": ["Equipo de protección térmica", "Oxígeno", "Kit de quemaduras", "Mascarilla FFP3"],
            "is_safe": False,
            "access_difficulty": "DIFFICULT",
            "recommendations": [
                "Esperar a que bomberos aseguren la zona",
                "Mantener distancia de seguridad",
                "Preparar oxígeno para inhalación de humo",
            ],
        },
        "MEDICAL_EMERGENCY": {
            "injury_type": "TRAUMA",
            "default_severity": "MEDIUM",
            "hazards": [],
            "equipment": ["Kit de primeros auxilios", "DEA", "Oxígeno portátil"],
            "is_safe": True,
            "access_difficulty": "EASY",
            "recommendations": [
                "Evaluar constantes vitales",
                "Preparar camilla",
                "Contactar con hospital receptor",
            ],
        },
        "STRUCTURAL_COLLAPSE": {
            "injury_type": "MULTIPLE_TRAUMA",
            "default_severity": "CRITICAL",
            "hazards": ["Estructura inestable", "Escombros sueltos", "Polvo denso", "Posibles atrapados"],
            "equipment": ["Equipo de rescate", "Kit trauma avanzado", "Radios de comunicación"],
            "is_safe": False,
            "access_difficulty": "EXTREME",
            "recommendations": [
                "NO acceder sin equipo de rescate urbano",
                "Establecer perímetro de seguridad amplio",
                "Coordinar con bomberos y equipo USAR",
            ],
        },
        "FLOOD_SCENE": {
            "injury_type": "TRAUMA",
            "default_severity": "HIGH",
            "hazards": ["Corriente de agua", "Nivel creciente", "Objetos arrastrados", "Contaminación"],
            "equipment": ["Chaleco salvavidas", "Cuerdas de rescate", "Bote inflable"],
            "is_safe": False,
            "access_difficulty": "DIFFICULT",
            "recommendations": [
                "No cruzar zonas inundadas a pie",
                "Coordinar con equipo de rescate acuático",
                "Vigilar nivel del agua",
            ],
        },
        "HAZMAT_SCENE": {
            "injury_type": "POISONING",
            "default_severity": "HIGH",
            "hazards": ["Sustancia química desconocida", "Vapores tóxicos", "Riesgo de contaminación"],
            "equipment": ["Traje HAZMAT nivel C", "Mascarilla con filtro ABEK", "Kit de descontaminación"],
            "is_safe": False,
            "access_difficulty": "EXTREME",
            "recommendations": [
                "Mantener distancia mínima de 100m",
                "Aproximarse desde barlovento",
                "Esperar identificación de la sustancia",
                "No tocar ni oler la sustancia",
            ],
        },
        "SAFE_SCENE": {
            "injury_type": "NONE_VISIBLE",
            "default_severity": "LOW",
            "hazards": [],
            "equipment": ["Kit de primeros auxilios estándar"],
            "is_safe": True,
            "access_difficulty": "EASY",
            "recommendations": [
                "Acceso seguro sin precauciones especiales",
                "Evaluar la situación al llegar",
            ],
        },
    }

    model_data = {
        "pipeline": pipeline,
        "scene_analysis_map": scene_analysis_map,
        "scene_classes": list(set(y)),
        "version": "1.0.0",
        "trained_at": datetime.utcnow().isoformat(),
        "samples": len(df),
    }

    out_path = os.path.join(MODELS_DIR, "vision_scene_model.joblib")
    joblib.dump(model_data, out_path)
    print(f"   ✅ Guardado: {out_path} ({os.path.getsize(out_path) / 1024:.0f} KB)")

    return model_data


# ─────────────────────────────────────────────────────────────────
# 4. DEMAND PREDICTOR  (re-train with synthetic if no DB)
# ─────────────────────────────────────────────────────────────────

def train_demand_predictor():
    """Entrena predictor de demanda con datos sintéticos de Madrid."""
    print("\n" + "=" * 60)
    print("📊 ENTRENANDO: Demand Predictor")
    print("=" * 60)

    random.seed(42)
    np.random.seed(42)

    # Generar datos sintéticos de Madrid
    madrid_zones = [
        (40.4168, -3.7038),   # Centro / Sol
        (40.4530, -3.6883),   # Chamartín
        (40.3920, -3.6995),   # Arganzuela
        (40.4380, -3.7200),   # Chamberí
        (40.4260, -3.6840),   # Salamanca
        (40.3800, -3.7100),   # Usera
        (40.4000, -3.7400),   # Carabanchel
        (40.3600, -3.6900),   # Villaverde
        (40.4700, -3.6800),   # Hortaleza
        (40.4400, -3.6500),   # Ciudad Lineal
        (40.4100, -3.6600),   # Retiro
        (40.3900, -3.7500),   # Latina
    ]

    samples = []
    for _ in range(800):
        hour = random.randint(0, 23)
        weekday = random.randint(0, 6)
        month = random.randint(1, 12)
        day = random.randint(1, 28)

        # Features derivadas
        is_weekend = 1 if weekday >= 5 else 0
        is_night = 1 if hour < 6 or hour > 22 else 0
        is_rush_hour = 1 if hour in [7, 8, 9, 13, 14, 17, 18, 19] else 0

        zone = random.choice(madrid_zones)
        lat = zone[0] + random.uniform(-0.01, 0.01)
        lon = zone[1] + random.uniform(-0.01, 0.01)

        # Severidad correlacionada con condiciones
        base_severity = 2.0
        if is_night:
            base_severity += 0.5
        if is_rush_hour:
            base_severity += 0.3
        if is_weekend:
            base_severity -= 0.2

        # Zonas céntricas → más incidentes
        dist_center = ((lat - 40.4168) ** 2 + (lon + 3.7038) ** 2) ** 0.5
        if dist_center < 0.02:
            base_severity += 0.5

        severity = max(1, min(4, int(base_severity + random.gauss(0, 0.8))))

        samples.append([hour, weekday, month, day, is_weekend, is_night, is_rush_hour, lat, lon, severity])

    columns = ["hour", "weekday", "month", "day", "is_weekend", "is_night", "is_rush_hour", "lat", "lon", "severity"]
    df = pd.DataFrame(samples, columns=columns)
    print(f"   Dataset sintético: {len(df)} muestras")

    X = df[["hour", "weekday", "month", "day", "is_weekend", "is_night", "is_rush_hour", "lat", "lon"]].values
    y = df["severity"].values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = RandomForestRegressor(
        n_estimators=150,
        max_depth=12,
        random_state=42,
    )
    model.fit(X_scaled, y)

    scores = cross_val_score(model, X_scaled, y, cv=5, scoring="r2")
    print(f"   R² (5-fold CV): {scores.mean():.3f} ± {scores.std():.3f}")

    # Guardar
    joblib.dump(model, os.path.join(MODELS_DIR, "demand_predictor.joblib"))
    joblib.dump(scaler, os.path.join(MODELS_DIR, "demand_scaler.joblib"))

    out_path = os.path.join(MODELS_DIR, "demand_predictor.joblib")
    print(f"   ✅ Guardado: {out_path} ({os.path.getsize(out_path) / 1024:.0f} KB)")

    return model, scaler


# ─────────────────────────────────────────────────────────────────
# 5. ETA PREDICTOR
# ─────────────────────────────────────────────────────────────────

def train_eta_predictor():
    """Entrena predictor de ETA con datos sintéticos."""
    print("\n" + "=" * 60)
    print("⏱️  ENTRENANDO: ETA Predictor")
    print("=" * 60)

    random.seed(42)
    np.random.seed(42)

    incident_types = [
        "CARDIAC_ARREST", "TRAFFIC_ACCIDENT", "RESPIRATORY", "STROKE",
        "TRAUMA", "BURNS", "POISONING", "OBSTETRIC", "OTHER", "FALL",
        "DROWNING", "SEVERE_BLEEDING", "ALLERGIC_REACTION", "PSYCHIATRIC",
    ]
    type_to_idx = {t: i for i, t in enumerate(incident_types)}

    samples = []
    for _ in range(500):
        distance_km = random.uniform(0.5, 25.0)
        speed_kmh = random.uniform(20, 120)
        severity_num = random.randint(1, 4)
        inc_type = random.choice(incident_types)
        inc_type_idx = type_to_idx[inc_type]
        hour = random.randint(0, 23)
        is_rush = 1 if hour in [7, 8, 9, 13, 14, 17, 18, 19] else 0

        # ETA base = distancia / velocidad * 60 (en minutos)
        base_eta = (distance_km / max(speed_kmh, 10)) * 60

        # Modificadores
        if is_rush:
            base_eta *= random.uniform(1.2, 1.8)  # Tráfico
        if severity_num >= 3:
            base_eta *= 0.85  # Prioridad alta → más rápido
        
        # Ruido
        eta_min = max(1, base_eta + random.gauss(0, base_eta * 0.15))

        samples.append([distance_km, speed_kmh, severity_num, inc_type_idx, hour, is_rush, eta_min])

    columns = ["distance_km", "speed_kmh", "severity", "incident_type_idx", "hour", "is_rush_hour", "eta_minutes"]
    df = pd.DataFrame(samples, columns=columns)
    print(f"   Dataset sintético: {len(df)} muestras")

    X = df[["distance_km", "speed_kmh", "severity", "incident_type_idx", "hour", "is_rush_hour"]].values
    y = df["eta_minutes"].values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = GradientBoostingRegressor(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        random_state=42,
    )
    model.fit(X_scaled, y)

    scores = cross_val_score(model, X_scaled, y, cv=5, scoring="r2")
    print(f"   R² (5-fold CV): {scores.mean():.3f} ± {scores.std():.3f}")

    # Guardar
    model_data = {
        "model": model,
        "scaler": scaler,
        "incident_types": incident_types,
        "type_to_idx": type_to_idx,
        "version": "1.0.0",
        "trained_at": datetime.utcnow().isoformat(),
    }

    out_path = os.path.join(MODELS_DIR, "eta_predictor.joblib")
    joblib.dump(model_data, out_path)
    joblib.dump(scaler, os.path.join(MODELS_DIR, "eta_scaler.joblib"))
    print(f"   ✅ Guardado: {out_path} ({os.path.getsize(out_path) / 1024:.0f} KB)")

    return model_data


# ─────────────────────────────────────────────────────────────────
# 6. ANOMALY DETECTOR
# ─────────────────────────────────────────────────────────────────

def train_anomaly_detector():
    """Entrena detector de anomalías con datos sintéticos de vehículos."""
    print("\n" + "=" * 60)
    print("🔍 ENTRENANDO: Anomaly Detector")
    print("=" * 60)

    random.seed(42)
    np.random.seed(42)

    # Datos normales de vehículos
    n_normal = 300
    vehicle_data = []
    for _ in range(n_normal):
        speed = random.uniform(0, 80)       # km/h normal
        fuel = random.uniform(30, 100)       # % fuel normal
        trust = random.uniform(70, 100)      # trust score normal
        vehicle_data.append([speed, fuel, trust])

    # Añadir anomalías (10%)
    n_anomaly = 30
    for _ in range(n_anomaly):
        speed = random.uniform(100, 200)     # velocidad excesiva
        fuel = random.uniform(0, 10)         # fuel crítico
        trust = random.uniform(0, 40)        # trust bajo
        vehicle_data.append([speed, fuel, trust])

    X_vehicle = np.array(vehicle_data)

    vehicle_scaler = StandardScaler()
    X_vehicle_scaled = vehicle_scaler.fit_transform(X_vehicle)

    vehicle_model = IsolationForest(
        n_estimators=150,
        contamination=0.1,
        random_state=42,
    )
    vehicle_model.fit(X_vehicle_scaled)

    # Datos de incidentes
    n_normal_inc = 200
    incident_data = []
    for _ in range(n_normal_inc):
        response_time = random.uniform(3, 20)
        resolution_time = random.uniform(15, 90)
        severity = random.randint(1, 4)
        incident_data.append([response_time, resolution_time, severity])

    # Anomalías de incidentes
    n_anomaly_inc = 20
    for _ in range(n_anomaly_inc):
        response_time = random.uniform(40, 120)   # respuesta muy lenta
        resolution_time = random.uniform(120, 300) # resolución muy lenta
        severity = random.randint(3, 4)
        incident_data.append([response_time, resolution_time, severity])

    X_incident = np.array(incident_data)

    incident_scaler = StandardScaler()
    X_incident_scaled = incident_scaler.fit_transform(X_incident)

    incident_model = IsolationForest(
        n_estimators=150,
        contamination=0.1,
        random_state=42,
    )
    incident_model.fit(X_incident_scaled)

    print(f"   Vehículos: {len(X_vehicle)} muestras ({n_normal} normales + {n_anomaly} anomalías)")
    print(f"   Incidentes: {len(X_incident)} muestras ({n_normal_inc} normales + {n_anomaly_inc} anomalías)")

    # Guardar
    model_data = {
        "vehicle_model": vehicle_model,
        "vehicle_scaler": vehicle_scaler,
        "incident_model": incident_model,
        "incident_scaler": incident_scaler,
        "version": "1.0.0",
        "trained_at": datetime.utcnow().isoformat(),
    }

    out_path = os.path.join(MODELS_DIR, "anomaly_detector.joblib")
    joblib.dump(model_data, out_path)
    print(f"   ✅ Guardado: {out_path} ({os.path.getsize(out_path) / 1024:.0f} KB)")

    return model_data


# ─────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("   KAIROS CDS — Entrenamiento de TODOS los modelos de IA")
    print("=" * 60)
    start = datetime.now()

    results = {}

    results["severity"] = train_severity_classifier()
    results["chat"] = train_chat_intent_classifier()
    results["vision"] = train_vision_scene_classifier()
    results["demand"] = train_demand_predictor()
    results["eta"] = train_eta_predictor()
    results["anomaly"] = train_anomaly_detector()

    elapsed = (datetime.now() - start).total_seconds()

    print("\n" + "=" * 60)
    print("   ✅ RESUMEN — Todos los modelos entrenados")
    print("=" * 60)

    models_dir = MODELS_DIR
    total_size = 0
    for fname in sorted(os.listdir(models_dir)):
        if fname.endswith(".joblib"):
            fpath = os.path.join(models_dir, fname)
            size_kb = os.path.getsize(fpath) / 1024
            total_size += size_kb
            print(f"   📦 {fname:<35s} {size_kb:>8.0f} KB")

    print(f"\n   Total: {total_size:.0f} KB")
    print(f"   Tiempo: {elapsed:.1f}s")
    print(f"\n   🎉 ¡Listo! Todos los modelos están en backend/models/")
    print("=" * 60)


if __name__ == "__main__":
    main()
