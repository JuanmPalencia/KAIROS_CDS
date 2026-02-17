# app/core/data_collector.py
"""
Recolector de datos anonimizados para reentrenamiento continuo de modelos IA.

Flujo:
  Dato operativo → Anonimizador → CSV append → Reentrenamiento periódico

Datasets alimentados:
  ┌─────────────────────────────────────┬──────────────────────────────┐
  │ Evento                              │ Dataset destino              │
  ├─────────────────────────────────────┼──────────────────────────────┤
  │ Creación/resolución de incidente    │ severity_dataset.csv         │
  │ Mensaje de chat + intent detectado  │ chat_intents_dataset.csv     │
  │ Análisis de imagen                  │ vision_scenes_dataset.csv    │
  └─────────────────────────────────────┴──────────────────────────────┘

Los datos se anonimización antes de persistirse. El script
`train_all_models.py` los consume directamente.
"""
import os
import csv
import threading
from datetime import datetime
from typing import Dict, Any, Optional, List
from .anonymizer import get_anonymizer

# Directorio de datasets
_DATASETS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "datasets")
)

# Lock para escritura concurrente segura
_write_lock = threading.Lock()


def _ensure_datasets_dir():
    """Crea el directorio datasets/ si no existe."""
    os.makedirs(_DATASETS_DIR, exist_ok=True)


def _csv_append(filename: str, row: Dict[str, Any], fieldnames: List[str]):
    """Escribe una fila en un CSV de forma thread-safe."""
    _ensure_datasets_dir()
    filepath = os.path.join(_DATASETS_DIR, filename)
    file_exists = os.path.exists(filepath)

    with _write_lock:
        with open(filepath, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            if not file_exists or os.path.getsize(filepath) == 0:
                writer.writeheader()
            writer.writerow(row)


# ═══════════════════════════════════════════════════════════
# Colectores por tipo de dato
# ═══════════════════════════════════════════════════════════

_SEVERITY_FIELDS = [
    "description", "incident_type", "affected_count",
    "severity", "specialties", "response_time",
]

_CHAT_FIELDS = ["intent", "text"]

_VISION_FIELDS = ["label", "description"]


def collect_incident(incident_data: Dict[str, Any]):
    """
    Recolecta un incidente para el dataset de severidad.

    Se llama tras la creación o resolución de un incidente.
    Los datos se anonimizan antes de escribir.
    """
    anon = get_anonymizer()
    clean = anon.anonymize_incident_for_training(incident_data)

    # Mapear severity numérica a etiqueta
    sev_map = {1: "LOW", 2: "LOW", 3: "MEDIUM", 4: "HIGH", 5: "CRITICAL"}
    sev = clean.get("severity", 3)
    if isinstance(sev, int):
        clean["severity"] = sev_map.get(sev, "MEDIUM")

    # Si no hay descripción útil, no guardar
    desc = clean.get("description", "")
    if not desc or len(desc.strip()) < 10:
        return

    clean.setdefault("specialties", "")
    clean.setdefault("response_time", "")

    _csv_append("severity_dataset.csv", clean, _SEVERITY_FIELDS)


def collect_chat_interaction(message: str, detected_intent: str):
    """
    Recolecta una interacción de chat para el dataset de intents.

    Solo recoge mensajes donde el modelo tiene confianza ≥ 0.7
    (se valida fuera de esta función).
    """
    anon = get_anonymizer()
    clean = anon.anonymize_chat_for_training(message, detected_intent)

    if not clean["text"] or len(clean["text"].strip()) < 3:
        return

    _csv_append("chat_intents_dataset.csv", clean, _CHAT_FIELDS)


def collect_vision_analysis(scene_type: str, observations: List[str]):
    """
    Recolecta resultados de análisis de visión para el dataset de escenas.
    """
    if not scene_type or not observations:
        return

    anon = get_anonymizer()
    desc = ". ".join(observations)
    clean_desc = anon.anonymize_text(desc)

    _csv_append("vision_scenes_dataset.csv", {
        "label": scene_type,
        "description": clean_desc,
    }, _VISION_FIELDS)


def get_dataset_stats() -> Dict[str, Any]:
    """Devuelve estadísticas de los datasets de reentrenamiento."""
    _ensure_datasets_dir()
    stats = {}

    for fname in ["severity_dataset.csv", "chat_intents_dataset.csv", "vision_scenes_dataset.csv"]:
        fpath = os.path.join(_DATASETS_DIR, fname)
        if os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                rows = sum(1 for _ in reader) - 1  # menos header
            stats[fname] = {
                "rows": max(0, rows),
                "size_kb": round(os.path.getsize(fpath) / 1024, 1),
                "last_modified": datetime.fromtimestamp(
                    os.path.getmtime(fpath)
                ).isoformat(),
            }
        else:
            stats[fname] = {"rows": 0, "size_kb": 0, "last_modified": None}

    return stats
