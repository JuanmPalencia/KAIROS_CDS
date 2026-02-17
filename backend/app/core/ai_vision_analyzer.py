# app/core/ai_vision_analyzer.py
"""
Analizador de imágenes de emergencia usando modelo local.
Combina análisis de imagen (Pillow) con clasificador de escenas
(TF-IDF + SVM) — NO requiere OpenAI.

Modelo: models/vision_scene_model.joblib
Entrenamiento: python train_all_models.py
"""
import os
import random
import joblib
from typing import Optional, Dict, Any, List
from io import BytesIO
from PIL import Image
import numpy as np


class VisionAnalyzer:
    """Analizador de imágenes de emergencia con modelo local."""

    def __init__(self):
        self.model_data = None
        self.enabled = False
        self._load_model()

    def _load_model(self):
        """Carga el modelo de escenas entrenado."""
        model_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "models", "vision_scene_model.joblib"
        )
        model_path = os.path.abspath(model_path)

        if os.path.exists(model_path):
            self.model_data = joblib.load(model_path)
            self.enabled = True
            print(f"✅ Vision Analyzer cargado (v{self.model_data.get('version', '?')}, "
                  f"escenas: {self.model_data.get('scene_classes', [])})")
        else:
            self.enabled = False
            print("⚠️ Vision Analyzer: modelo no encontrado. "
                  "Ejecuta: python train_all_models.py")

    def _analyze_image_features(self, image: Image.Image) -> Dict[str, Any]:
        """Extrae features visuales básicas con Pillow + numpy."""
        img_array = np.array(image.convert("RGB"))

        # Canales
        r, g, b = img_array[:, :, 0], img_array[:, :, 1], img_array[:, :, 2]

        # Estadísticas de color
        avg_r, avg_g, avg_b = float(r.mean()), float(g.mean()), float(b.mean())
        brightness = float(img_array.mean())

        # Detección heurística de colores dominantes
        red_ratio = avg_r / max(brightness, 1)
        blue_ratio = avg_b / max(brightness, 1)
        dark_ratio = float((img_array < 50).mean())
        bright_ratio = float((img_array > 200).mean())

        # Varianza (escenas caóticas tienden a tener más varianza)
        variance = float(img_array.astype(float).var())

        # Descriptores de escena basados en features visuales
        scene_hints = []

        if red_ratio > 0.5 and avg_r > 150:
            scene_hints.append("fire scene with flames or red elements")
        if dark_ratio > 0.4:
            scene_hints.append("dark scene possibly at night or with smoke")
        if blue_ratio > 0.45 and avg_b > 130:
            scene_hints.append("water or flood scene with blue elements")
        if variance > 5000:
            scene_hints.append("chaotic scene with high visual variability")
        if brightness < 80:
            scene_hints.append("dark environment low visibility")
        if brightness > 180:
            scene_hints.append("bright well-lit outdoor scene")

        # Tamaño de imagen
        width, height = image.size

        return {
            "brightness": round(brightness, 1),
            "avg_rgb": (round(avg_r, 1), round(avg_g, 1), round(avg_b, 1)),
            "red_ratio": round(red_ratio, 3),
            "dark_ratio": round(dark_ratio, 3),
            "variance": round(variance, 1),
            "resolution": f"{width}x{height}",
            "scene_hints": scene_hints,
        }

    def _classify_scene_from_features(self, features: Dict) -> str:
        """Clasifica tipo de escena basándose en features visuales."""
        hints = " ".join(features.get("scene_hints", []))

        if self.model_data and hints:
            pipeline = self.model_data["pipeline"]
            scene_type = pipeline.predict([hints])[0]
            return scene_type

        # Fallback heurístico si no hay hints claros
        if features["red_ratio"] > 0.5:
            return "FIRE_SCENE"
        if features["dark_ratio"] > 0.4:
            return "STRUCTURAL_COLLAPSE"
        if features["variance"] > 5000:
            return "TRAFFIC_ACCIDENT"
        return "MEDICAL_EMERGENCY"

    async def analyze_incident_image(
        self,
        image_data: bytes,
        image_format: str = "jpeg",
    ) -> Dict[str, Any]:
        """
        Analiza una imagen de incidente usando modelo local.

        Args:
            image_data: Bytes de la imagen
            image_format: Formato de imagen

        Returns:
            Dict con análisis de la escena
        """
        if not self.enabled:
            return self._mock_vision_analysis()

        try:
            image = Image.open(BytesIO(image_data))

            # Redimensionar si muy grande
            max_size = 1024
            if max(image.size) > max_size:
                ratio = max_size / max(image.size)
                new_size = tuple(int(dim * ratio) for dim in image.size)
                image = image.resize(new_size, Image.Resampling.LANCZOS)

            # Extraer features visuales
            features = self._analyze_image_features(image)

            # Clasificar escena
            scene_type = self._classify_scene_from_features(features)

            # Obtener análisis detallado del mapa
            scene_map = self.model_data.get("scene_analysis_map", {})
            analysis = scene_map.get(scene_type, scene_map.get("MEDICAL_EMERGENCY", {}))

            # Ajustar severidad por features
            severity = analysis.get("default_severity", "MEDIUM")
            if features["dark_ratio"] > 0.5 or features["red_ratio"] > 0.6:
                if severity == "MEDIUM":
                    severity = "HIGH"
                elif severity == "HIGH":
                    severity = "CRITICAL"

            # Estimar pacientes (heurístico por varianza)
            patient_estimate = 1
            if features["variance"] > 8000:
                patient_estimate = random.randint(2, 5)

            confidence = 0.65
            if features["scene_hints"]:
                confidence = min(0.85, 0.65 + len(features["scene_hints"]) * 0.05)

            return {
                "injury_type": analysis.get("injury_type", "UNKNOWN"),
                "severity_visual": severity,
                "confidence": round(confidence, 2),
                "observations": [
                    f"Escena clasificada como: {scene_type}",
                    f"Brillo medio: {features['brightness']:.0f}/255",
                    f"Resolución: {features['resolution']}",
                    f"Varianza: {features['variance']:.0f}",
                ] + features.get("scene_hints", []),
                "recommended_equipment": analysis.get("equipment", ["Kit de primeros auxilios estándar"]),
                "detected_hazards": analysis.get("hazards", []),
                "patient_count_estimate": patient_estimate,
                "scene_type": scene_type,
                "image_features": features,
            }

        except Exception as e:
            print(f"⚠️ Vision analysis failed: {e}")
            return self._mock_vision_analysis()

    def _mock_vision_analysis(self) -> Dict[str, Any]:
        """Análisis mock cuando no hay modelo disponible."""
        return {
            "injury_type": "UNKNOWN",
            "severity_visual": "MEDIUM",
            "confidence": 0.0,
            "observations": [
                "Análisis visual no disponible (modelo no entrenado). "
                "Ejecuta: python train_all_models.py"
            ],
            "recommended_equipment": ["Kit de primeros auxilios estándar"],
            "detected_hazards": [],
            "patient_count_estimate": 1,
        }

    async def analyze_scene_safety(
        self,
        image_data: bytes,
        image_format: str = "jpeg",
    ) -> Dict[str, Any]:
        """Analiza la seguridad de la escena del incidente."""
        if not self.enabled:
            return {
                "is_safe": True,
                "hazards": [],
                "recommendations": ["Evaluación visual no disponible — modelo no entrenado"],
                "access_difficulty": "MODERATE",
            }

        try:
            image = Image.open(BytesIO(image_data))

            if max(image.size) > 1024:
                ratio = 1024 / max(image.size)
                new_size = tuple(int(dim * ratio) for dim in image.size)
                image = image.resize(new_size, Image.Resampling.LANCZOS)

            features = self._analyze_image_features(image)
            scene_type = self._classify_scene_from_features(features)

            scene_map = self.model_data.get("scene_analysis_map", {})
            analysis = scene_map.get(scene_type, scene_map.get("SAFE_SCENE", {}))

            return {
                "is_safe": analysis.get("is_safe", True),
                "hazards": analysis.get("hazards", []),
                "recommendations": analysis.get("recommendations", ["Evaluar la situación al llegar"]),
                "access_difficulty": analysis.get("access_difficulty", "MODERATE"),
                "scene_type": scene_type,
            }

        except Exception as e:
            print(f"⚠️ Scene safety analysis failed: {e}")
            return {
                "is_safe": True,
                "hazards": [],
                "recommendations": ["Error en análisis, proceder con precaución"],
                "access_difficulty": "MODERATE",
            }


# Singleton global
_vision_analyzer = None


def get_vision_analyzer() -> VisionAnalyzer:
    """Obtiene instancia singleton del analizador de visión."""
    global _vision_analyzer
    if _vision_analyzer is None:
        _vision_analyzer = VisionAnalyzer()
    return _vision_analyzer
