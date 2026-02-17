# app/core/ai_conversational_assistant.py
"""
Asistente conversacional IA para el Dashboard.
Usa modelo local (TF-IDF + LogisticRegression) para clasificar intents
y genera respuestas con datos reales del sistema — NO requiere OpenAI.

Modelo: models/chat_intent_model.joblib
Entrenamiento: python train_all_models.py
"""
import os
import re
import json
import random
import joblib
from typing import Optional, List, Dict, Any
from datetime import datetime


class ConversationalAssistant:
    """Asistente IA conversacional con intent classification local."""

    def __init__(self):
        self.model_data = None
        self.enabled = False
        self.conversation_history: List[Dict[str, str]] = []
        self._load_model()

    def _load_model(self):
        """Carga el modelo de intents entrenado."""
        model_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "models", "chat_intent_model.joblib"
        )
        model_path = os.path.abspath(model_path)

        if os.path.exists(model_path):
            self.model_data = joblib.load(model_path)
            self.enabled = True
            print(f"✅ Conversational Assistant cargado (v{self.model_data.get('version', '?')}, "
                  f"{self.model_data.get('samples', '?')} muestras, "
                  f"intents: {self.model_data.get('intent_classes', [])})")
        else:
            self.enabled = False
            print("⚠️ Conversational Assistant: modelo no encontrado. "
                  "Ejecuta: python train_all_models.py")

    def _classify_intent(self, message: str) -> tuple:
        """Clasifica el intent del mensaje. Retorna (intent, confidence)."""
        if not self.model_data:
            return ("help", 0.5)

        pipeline = self.model_data["pipeline"]
        intent = pipeline.predict([message])[0]

        # Obtener confianza
        probas = pipeline.predict_proba([message])[0]
        confidence = float(max(probas))

        return (intent, confidence)

    def _extract_coordinates(self, text: str) -> Optional[tuple]:
        """Extrae coordenadas del texto si las hay."""
        # Buscar patrones como "40.41, -3.70" o "coordenadas 40.41 -3.70"
        pattern = r'(-?\d+\.?\d*)[,\s]+(-?\d+\.?\d*)'
        matches = re.findall(pattern, text)
        for lat_str, lon_str in matches:
            lat, lon = float(lat_str), float(lon_str)
            if 35 < lat < 45 and -10 < lon < 5:  # Rango España
                return (lat, lon)
        return None

    def _build_response(self, intent: str, confidence: float, message: str,
                        context: Optional[Dict] = None) -> Dict[str, Any]:
        """Construye respuesta basada en el intent detectado."""
        templates = self.model_data.get("response_templates", {}) if self.model_data else {}
        function_calls = []
        requires_action = False

        if intent == "fleet_status":
            template_list = templates.get("fleet_status", ["🚑 Consultando estado de la flota..."])
            response = random.choice(template_list).replace(
                "{fleet_data}",
                "Usa el endpoint `GET /fleet/vehicles` o consulta el Dashboard para ver el estado en tiempo real."
            )
            function_calls.append({"name": "get_fleet_status", "arguments": {}})
            requires_action = True

        elif intent == "incidents_summary":
            template_list = templates.get("incidents_summary", ["🚨 Consultando incidentes..."])
            response = random.choice(template_list).replace(
                "{incidents_data}",
                "Consulta la vista de incidentes en el Dashboard o usa `GET /events/incidents`."
            )
            function_calls.append({"name": "get_incidents_summary", "arguments": {"status": "all"}})
            requires_action = True

        elif intent == "hospital_capacity":
            template_list = templates.get("hospital_capacity", ["🏥 Consultando hospitales..."])
            response = random.choice(template_list).replace(
                "{hospital_data}",
                "Consulta el panel de hospitales o usa `GET /api/hospitals/`."
            )
            function_calls.append({"name": "get_hospital_capacity", "arguments": {}})
            requires_action = True

        elif intent == "create_incident":
            template_list = templates.get("create_incident", ["⚠️ Crear incidente..."])
            response = random.choice(template_list)

            coords = self._extract_coordinates(message)
            if coords:
                function_calls.append({
                    "name": "create_incident",
                    "arguments": {
                        "lat": coords[0],
                        "lon": coords[1],
                        "description": message,
                        "type": "OTHER",
                    }
                })
                requires_action = True

        elif intent == "analytics":
            template_list = templates.get("analytics", ["📈 Consultando métricas..."])
            response = random.choice(template_list).replace(
                "{analytics_data}",
                "Accede a la sección Analytics o KPIs del Dashboard para métricas detalladas."
            )
            function_calls.append({"name": "get_analytics_summary", "arguments": {"period": "today"}})
            requires_action = True

        elif intent == "hotspots":
            template_list = templates.get("hotspots", ["🔥 Prediciendo demanda..."])
            response = random.choice(template_list).replace(
                "{hotspot_data}",
                "Accede a AI Insights en el Dashboard para ver el mapa de predicción."
            )
            function_calls.append({"name": "predict_hotspots", "arguments": {"hours_ahead": 1}})
            requires_action = True

        elif intent == "greeting":
            template_list = templates.get("greeting", [
                "👋 ¡Hola! Soy KAIROS AI. ¿En qué puedo ayudarte?"
            ])
            response = random.choice(template_list)

        elif intent == "help":
            template_list = templates.get("help", [
                "ℹ️ Puedo ayudarte con: flota, incidentes, hospitales, analytics y predicciones."
            ])
            response = random.choice(template_list)

        else:
            response = (
                "🤔 No estoy seguro de cómo ayudarte con eso. "
                "Prueba preguntar sobre:\n"
                "🚑 Estado de la flota\n"
                "🚨 Incidentes activos\n"
                "🏥 Capacidad hospitalaria\n"
                "📊 Métricas\n"
                "🔥 Predicción de demanda"
            )

        return {
            "response": response,
            "function_calls": function_calls,
            "requires_action": requires_action,
            "suggested_actions": self._extract_suggested_actions(intent),
            "intent": intent,
            "confidence": round(confidence, 2),
        }

    def _extract_suggested_actions(self, intent: str) -> List[str]:
        """Acciones sugeridas según intent."""
        action_map = {
            "fleet_status": ["check_status"],
            "incidents_summary": ["check_status"],
            "hospital_capacity": ["check_status"],
            "create_incident": ["create_incident"],
            "analytics": ["check_status"],
            "hotspots": ["check_status"],
        }
        return action_map.get(intent, [])

    async def chat(
        self,
        user_message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Procesa un mensaje del usuario y retorna respuesta.
        """
        if not self.enabled:
            return {
                "response": (
                    "⚠️ El asistente IA no está disponible (modelo no entrenado). "
                    "Ejecuta: `python train_all_models.py` para activarlo."
                ),
                "function_calls": [],
                "requires_action": False,
            }

        try:
            # Historial
            self.conversation_history.append({
                "role": "user",
                "content": user_message,
            })
            if len(self.conversation_history) > 10:
                self.conversation_history = self.conversation_history[-10:]

            # Clasificar intent
            intent, confidence = self._classify_intent(user_message)

            # Construir respuesta
            result = self._build_response(intent, confidence, user_message, context)

            # Agregar al historial
            self.conversation_history.append({
                "role": "assistant",
                "content": result["response"],
            })

            return result

        except Exception as e:
            print(f"⚠️ Assistant error: {e}")
            return {
                "response": f"Error procesando tu solicitud: {str(e)}",
                "function_calls": [],
                "requires_action": False,
            }

    def clear_history(self):
        """Limpia el historial de conversación."""
        self.conversation_history = []


# Singleton global
_assistant = None


def get_assistant() -> ConversationalAssistant:
    """Obtiene instancia singleton del asistente."""
    global _assistant
    if _assistant is None:
        _assistant = ConversationalAssistant()
    return _assistant
