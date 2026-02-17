# app/core/ai_recommendation_system.py
"""
Sistema de recomendaciones personalizadas para operadores.
Aprende de las decisiones del usuario y sugiere acciones.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import Counter
from sqlalchemy.orm import Session
from ..storage.models_sql import IncidentSQL, Vehicle, Hospital, AuditLog


class RecommendationSystem:
    """Sistema de recomendaciones basado en historial del operador"""
    
    def __init__(self):
        self.user_profiles = {}  # Cache de perfiles de usuario
    
    def _build_user_profile(
        self,
        db: Session,
        user_id: int,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """Construye perfil de decisiones del usuario"""
        if user_id in self.user_profiles:
            # Retornar cache si es reciente (< 1 hora)
            cached = self.user_profiles[user_id]
            if (datetime.utcnow() - cached["timestamp"]).total_seconds() < 3600:
                return cached
        
        since_date = datetime.utcnow() - timedelta(days=days_back)
        
        # Obtener decisiones del usuario desde audit log
        user_decisions = db.query(AuditLog).filter(
            AuditLog.user_id == user_id,
            AuditLog.timestamp >= since_date,
            AuditLog.action.in_(["AI_ACCEPTED", "AI_OVERRIDDEN"])
        ).all()
        
        # Calcular estadísticas
        total_decisions = len(user_decisions)
        ai_accepted = sum(1 for d in user_decisions if d.action == "AI_ACCEPTED")
        ai_overridden = sum(1 for d in user_decisions if d.action == "AI_OVERRIDDEN")
        
        acceptance_rate = ai_accepted / total_decisions if total_decisions > 0 else 0.5
        
        # Analizar patrones de override
        override_reasons = []
        preferred_hospitals = []
        
        for decision in user_decisions:
            if decision.action == "AI_OVERRIDDEN" and decision.details:
                try:
                    import json
                    details = json.loads(decision.details)
                    if "override_reason" in details:
                        override_reasons.append(details["override_reason"])
                    if "hospital_id" in details:
                        preferred_hospitals.append(details["hospital_id"])
                except:
                    pass
        
        # Razones comunes de override
        common_override_reasons = Counter(override_reasons).most_common(3)
        
        # Hospitales preferidos
        preferred_hospital_counts = Counter(preferred_hospitals).most_common(5)
        
        profile = {
            "user_id": user_id,
            "total_decisions": total_decisions,
            "ai_acceptance_rate": round(acceptance_rate, 2),
            "ai_overrides": ai_overridden,
            "common_override_reasons": [r[0] for r in common_override_reasons],
            "preferred_hospitals": [h[0] for h in preferred_hospital_counts],
            "experience_level": self._calculate_experience_level(total_decisions),
            "timestamp": datetime.utcnow()
        }
        
        # Guardar en cache
        self.user_profiles[user_id] = profile
        
        return profile
    
    def _calculate_experience_level(self, total_decisions: int) -> str:
        """Calcula nivel de experiencia basado en decisiones"""
        if total_decisions < 10:
            return "NOVICE"
        elif total_decisions < 50:
            return "INTERMEDIATE"
        elif total_decisions < 200:
            return "ADVANCED"
        else:
            return "EXPERT"
    
    def get_personalized_suggestions(
        self,
        db: Session,
        user_id: int,
        incident: IncidentSQL,
        ai_suggestion: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Genera sugerencias personalizadas basadas en el perfil del usuario.
        
        Args:
            db: Sesión de base de datos
            user_id: ID del usuario
            incident: Incidente actual
            ai_suggestion: Sugerencia original de la IA
        
        Returns:
            {
                "personalized_message": str,
                "confidence_adjustment": float,
                "alternative_suggestions": [...],
                "insights": List[str]
            }
        """
        profile = self._build_user_profile(db, user_id)
        
        insights = []
        confidence_adjustment = 0.0
        personalized_message = ""
        alternative_suggestions = []
        
        # 1. Ajustar confianza basado en tasa de aceptación
        acceptance_rate = profile["ai_acceptance_rate"]
        
        if acceptance_rate > 0.8:
            confidence_adjustment = 0.05
            insights.append(f"✅ Alta tasa de aceptación de IA ({int(acceptance_rate*100)}%)")
        elif acceptance_rate < 0.4:
            confidence_adjustment = -0.1
            insights.append(f"⚠️ Frecuentemente sobrescribes sugerencias IA ({int((1-acceptance_rate)*100)}%)")
        
        # 2. Considerar hospitales preferidos del usuario
        preferred_hospitals = profile.get("preferred_hospitals", [])
        suggested_hospital_id = ai_suggestion.get("suggested_hospital", {}).get("id")
        
        if suggested_hospital_id and suggested_hospital_id not in preferred_hospitals and preferred_hospitals:
            # Usuario suele elegir otros hospitales
            top_preferred = preferred_hospitals[0] if preferred_hospitals else None
            
            if top_preferred:
                preferred_hospital = db.query(Hospital).filter(Hospital.id == top_preferred).first()
                if preferred_hospital:
                    alternative_suggestions.append({
                        "type": "HOSPITAL",
                        "id": preferred_hospital.id,
                        "name": preferred_hospital.name,
                        "reason": "Tu hospital más frecuentemente elegido"
                    })
                    insights.append(f"📍 Sueles preferir: {preferred_hospital.name}")
        
        # 3. Razones comunes de override
        common_reasons = profile.get("common_override_reasons", [])
        if common_reasons:
            insights.append(f"💡 Frecuentemente: '{common_reasons[0]}'")
        
        # 4. Nivel de experiencia
        experience = profile["experience_level"]
        
        if experience == "NOVICE":
            personalized_message = "💚 Te recomiendo seguir la sugerencia IA mientras ganas experiencia"
            confidence_adjustment += 0.1  # Más confianza para novatos
        elif experience == "EXPERT":
            personalized_message = "🎖️ Tu experiencia es valiosa. Confía en tu criterio si ves una mejor opción"
            # No ajustar confianza para expertos
        
        # 5. Análisis de patrones de distancia/severidad
        # (Requeriría más datos históricos, simplificado aquí)
        
        # Mensaje personalizado por defecto
        if not personalized_message:
            if acceptance_rate > 0.7:
                personalized_message = f"📊 Históricamente aceptas {int(acceptance_rate*100)}% de sugerencias IA"
            else:
                personalized_message = f"🤔 Sueles tener diferentes criterios ({int((1-acceptance_rate)*100)}% overrides)"
        
        # Ajustar confianza final
        original_confidence = ai_suggestion.get("confidence", 0.5)
        adjusted_confidence = min(1.0, max(0.0, original_confidence + confidence_adjustment))
        
        return {
            "personalized_message": personalized_message,
            "confidence_adjustment": round(confidence_adjustment, 2),
            "adjusted_confidence": round(adjusted_confidence, 2),
            "alternative_suggestions": alternative_suggestions,
            "insights": insights,
            "profile_summary": {
                "experience_level": experience,
                "total_decisions": profile["total_decisions"],
                "acceptance_rate": acceptance_rate
            }
        }
    
    def get_learning_insights(
        self,
        db: Session,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Proporciona insights sobre el aprendizaje y progreso del operador.
        
        Returns:
            {
                "progress": {...},
                "strengths": [...],
                "areas_for_improvement": [...],
                "achievements": [...]
            }
        """
        profile = self._build_user_profile(db, user_id)
        
        total_decisions = profile["total_decisions"]
        acceptance_rate = profile["ai_acceptance_rate"]
        experience = profile["experience_level"]
        
        strengths = []
        areas_for_improvement = []
        achievements = []
        
        # Análisis de fortalezas
        if acceptance_rate > 0.75:
            strengths.append("Alta concordancia con IA - buena toma de decisiones")
        elif acceptance_rate < 0.3:
            strengths.append("Criterio independiente - piensas críticamente")
        
        if total_decisions > 100:
            strengths.append("Experiencia significativa en operaciones")
        
        # Áreas de mejora
        if total_decisions < 20:
            areas_for_improvement.append("Ganar más experiencia con casos diversos")
        
        if acceptance_rate > 0.9:
            areas_for_improvement.append("Considerar desarrollar criterio propio, no solo seguir IA")
        
        # Achievements
        if total_decisions >= 10:
            achievements.append({"name": "🎯 Primeras 10 decisiones", "unlocked": True})
        if total_decisions >= 50:
            achievements.append({"name": "🏆 Medio centenar", "unlocked": True})
        if total_decisions >= 100:
            achievements.append({"name": "💎 Centurión", "unlocked": True})
        
        if acceptance_rate > 0.85:
            achievements.append({"name": "🤖 IA Whisperer - Alta sintonía con IA", "unlocked": True})
        
        # Progreso hacia siguiente nivel
        next_level_threshold = {
            "NOVICE": 10,
            "INTERMEDIATE": 50,
            "ADVANCED": 200
        }.get(experience, 200)
        
        progress_percentage = min(100, (total_decisions / next_level_threshold) * 100)
        
        return {
            "progress": {
                "current_level": experience,
                "total_decisions": total_decisions,
                "progress_to_next": round(progress_percentage, 1),
                "decisions_needed": max(0, next_level_threshold - total_decisions)
            },
            "strengths": strengths if strengths else ["Continúa desarrollando tu experiencia"],
            "areas_for_improvement": areas_for_improvement if areas_for_improvement else ["¡Vas por buen camino!"],
            "achievements": achievements,
            "acceptance_rate": round(acceptance_rate * 100, 1)
        }


# Singleton global
_recommendation_system = None

def get_recommendation_system() -> RecommendationSystem:
    """Obtiene instancia singleton del sistema de recomendaciones"""
    global _recommendation_system
    if _recommendation_system is None:
        _recommendation_system = RecommendationSystem()
    return _recommendation_system
