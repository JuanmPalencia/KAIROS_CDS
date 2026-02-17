# app/core/ai_severity_classifier.py
"""
Clasificador inteligente de severidad usando modelo local (TF-IDF + RandomForest).
Entrenado con dataset propio — NO requiere OpenAI.

Modelo: models/severity_classifier.joblib
Entrenamiento: python train_all_models.py
"""
import os
import joblib
from typing import Optional, Dict, Any
from pydantic import BaseModel


class SeverityClassification(BaseModel):
    """Resultado de clasificación de severidad"""
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    confidence: float  # 0.0 - 1.0
    reasoning: str
    suggested_specialties: list[str]
    estimated_response_time: int  # minutos
    recommended_actions: list[str]


class SeverityClassifier:
    """Clasificador de severidad con modelo local sklearn."""

    def __init__(self):
        self.model_data = None
        self.enabled = False
        self._load_model()

    def _load_model(self):
        """Carga el modelo entrenado desde disco."""
        model_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "models", "severity_classifier.joblib"
        )
        model_path = os.path.abspath(model_path)

        if os.path.exists(model_path):
            self.model_data = joblib.load(model_path)
            self.enabled = True
            print(f"✅ Severity Classifier cargado (v{self.model_data.get('version', '?')}, "
                  f"{self.model_data.get('samples', '?')} muestras)")
        else:
            self.enabled = False
            print("⚠️ Severity Classifier: modelo no encontrado, usando reglas. "
                  "Ejecuta: python train_all_models.py")

    async def classify_incident(
        self,
        description: str,
        incident_type: str,
        affected_count: int = 1,
    ) -> SeverityClassification:
        """
        Clasifica la severidad de un incidente usando el modelo local.
        """
        if not self.enabled or self.model_data is None:
            return self._classify_with_rules(description, incident_type, affected_count)

        try:
            text_feature = (
                f"{description} TIPO:{incident_type} AFECTADOS:{affected_count}"
            )

            severity_pipeline = self.model_data["severity_pipeline"]
            rt_pipeline = self.model_data["response_time_pipeline"]
            specialty_map = self.model_data["specialty_map"]

            severity = severity_pipeline.predict([text_feature])[0]

            probas = severity_pipeline.predict_proba([text_feature])[0]
            confidence = float(max(probas))

            response_time = int(round(rt_pipeline.predict([text_feature])[0]))
            response_time = max(3, min(30, response_time))

            key = (incident_type, severity)
            specialties_str = specialty_map.get(key, "TRAUMA")
            specialties = [s.strip() for s in specialties_str.split(";")]

            actions_map = {
                "CRITICAL": [
                    "Activar protocolo de máxima prioridad",
                    "Asignar ambulancia SVA más cercana",
                    "Notificar hospital receptor inmediatamente",
                    "Preparar equipo de reanimación",
                ],
                "HIGH": [
                    "Asignar ambulancia inmediatamente",
                    "Notificar al hospital más cercano",
                    "Preparar equipo médico apropiado",
                ],
                "MEDIUM": [
                    "Asignar ambulancia disponible",
                    "Evaluar necesidad de SVA o SVB",
                    "Preparar kit de primeros auxilios",
                ],
                "LOW": [
                    "Asignar unidad cuando esté disponible",
                    "Valorar atención en centro de salud",
                    "Evaluar si requiere transporte sanitario",
                ],
            }

            return SeverityClassification(
                severity=severity,
                confidence=round(confidence, 2),
                reasoning=(
                    f"Clasificación por modelo ML local (TF-IDF + RandomForest). "
                    f"Tipo: {incident_type}, Afectados: {affected_count}. "
                    f"Confianza: {confidence:.0%}"
                ),
                suggested_specialties=specialties,
                estimated_response_time=response_time,
                recommended_actions=actions_map.get(severity, actions_map["MEDIUM"]),
            )

        except Exception as e:
            print(f"⚠️ ML classification failed: {e}, using fallback")
            return self._classify_with_rules(description, incident_type, affected_count)

    def _classify_with_rules(
        self,
        description: str,
        incident_type: str,
        affected_count: int,
    ) -> SeverityClassification:
        """Clasificación basada en reglas (fallback)."""
        desc_lower = description.lower()

        critical_keywords = [
            "inconsciente", "no respira", "paro cardíaco", "hemorragia severa",
            "convulsiones", "unconscious", "not breathing", "cardiac arrest",
            "severe bleeding", "seizures",
        ]

        high_keywords = [
            "dolor de pecho", "dificultad respirar", "fractura", "quemadura",
            "chest pain", "difficulty breathing", "fracture", "burn",
        ]

        critical_types = ["CARDIAC_ARREST", "DROWNING", "SEVERE_BLEEDING"]
        high_types = ["TRAFFIC_ACCIDENT", "STROKE", "BURNS", "OBSTETRIC"]

        if any(kw in desc_lower for kw in critical_keywords) or incident_type in critical_types:
            severity = "CRITICAL"
            confidence = 0.9
            response_time = 3
        elif any(kw in desc_lower for kw in high_keywords) or incident_type in high_types:
            severity = "HIGH"
            confidence = 0.75
            response_time = 8
        elif affected_count >= 3:
            severity = "HIGH"
            confidence = 0.7
            response_time = 10
        else:
            severity = "MEDIUM"
            confidence = 0.6
            response_time = 15

        specialty_map = {
            "CARDIAC_ARREST": ["CARDIO"],
            "RESPIRATORY": ["RESPIRATORY"],
            "TRAFFIC_ACCIDENT": ["TRAUMA"],
            "STROKE": ["NEURO"],
            "OBSTETRIC": ["OBSTETRIC"],
            "BURNS": ["BURNS"],
            "POISONING": ["POISONING"],
        }

        specialties = specialty_map.get(incident_type, ["TRAUMA"])

        return SeverityClassification(
            severity=severity,
            confidence=confidence,
            reasoning=f"Clasificación por reglas (modelo ML no disponible). Tipo: {incident_type}",
            suggested_specialties=specialties,
            estimated_response_time=response_time,
            recommended_actions=[
                "Asignar ambulancia inmediatamente",
                "Notificar al hospital más cercano",
                "Preparar equipo médico apropiado",
            ],
        )


# Singleton global
_severity_classifier = None


def get_severity_classifier() -> SeverityClassifier:
    """Obtiene instancia singleton del clasificador."""
    global _severity_classifier
    if _severity_classifier is None:
        _severity_classifier = SeverityClassifier()
    return _severity_classifier
