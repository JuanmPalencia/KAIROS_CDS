# app/core/anonymizer.py
"""
Motor de anonimización de datos para cumplimiento RGPD / LOPD-GDD.

Anonimiza datos personales identificables (PII) antes de almacenarlos
en datasets de reentrenamiento de IA. Opera en tres capas:

1. **Supresión**: Elimina campos de identidad (nombre, DNI, teléfono).
2. **Generalización**: Reduce precisión de coordenadas, edades, fechas.
3. **Perturbación**: Añade ruido a valores numéricos (constantes vitales, etc.).

Todos los datos que entran al pipeline de reentrenamiento pasan por este filtro.
"""
import re
import hashlib
import random
from typing import Dict, Any, Optional, List
from datetime import datetime


# ──────────────────────────────────────────
# Patrones PII para scrubbing de texto libre
# ──────────────────────────────────────────
_PII_PATTERNS = [
    # DNI / NIE español
    (re.compile(r"\b[0-9]{8}[A-Za-z]\b"), "[DNI_ANON]"),
    (re.compile(r"\b[XYZ][0-9]{7}[A-Za-z]\b", re.I), "[NIE_ANON]"),
    # Teléfonos españoles (+34 6xx / 9xx / 7xx)
    (re.compile(r"(?:\+34[\s-]?)?[679]\d{2}[\s.-]?\d{3}[\s.-]?\d{3}\b"), "[TEL_ANON]"),
    # Emails
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"), "[EMAIL_ANON]"),
    # Nombres propios precedidos de "paciente" o "nombre"
    (re.compile(r"(?:paciente|nombre|llamado/a?|sr\.?|sra\.?|don|doña)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*)", re.I), "[NOMBRE_ANON]"),
    # Direcciones: Calle/Avenida/Plaza + nombre + número
    (re.compile(r"(?:(?:C|c)(?:alle|/)|(?:A|a)v(?:enida|da\.?|\.)|(?:P|p)(?:laza|za\.?)|(?:P|p)aseo)\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ\s]+(?:,?\s*(?:n[ºo°]?\s*)?\d+)?", re.I), "[DIR_ANON]"),
    # Matrículas españolas  1234 ABC
    (re.compile(r"\b\d{4}\s?[A-Z]{3}\b"), "[MATR_ANON]"),
    # NSS (Número Seguridad Social)
    (re.compile(r"\b\d{2}/?\d{8,10}/?\d{2}\b"), "[NSS_ANON]"),
    # Tarjeta sanitaria (CIP)
    (re.compile(r"\b[A-Z]{4}\d{10,14}\b"), "[CIP_ANON]"),
]

# Campos que siempre se eliminan (supresión total)
_SUPPRESS_FIELDS = {
    "patient_name", "patient_id_number", "patient_id",
    "name", "full_name", "first_name", "last_name",
    "phone", "email", "contact_phone",
    "dni", "nie", "nss", "cip",
    "photo_url", "photo",
    "ip_address", "user_agent",
    "username", "user_id",
}

# Campos que se generalizan (reducir precisión)
_GENERALIZE_FIELDS = {
    "patient_age": "age_range",
    "lat": "lat_approx",
    "lon": "lon_approx",
    "address": "zone",
}


class DataAnonymizer:
    """Anonimizador conforme RGPD para datos de emergencia."""

    def __init__(self, seed: int = 42):
        self._rng = random.Random(seed)
        self._salt = hashlib.sha256(str(seed).encode()).hexdigest()[:16]

    # ─── API pública ───────────────────────────────────

    def anonymize_text(self, text: str) -> str:
        """Elimina PII de texto libre (descripciones, notas clínicas)."""
        if not text:
            return text
        result = text
        for pattern, replacement in _PII_PATTERNS:
            result = pattern.sub(replacement, result)
        return result

    def anonymize_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Anonimiza un registro completo (dict).

        - Campos PII → se suprimen o reemplazan.
        - Coordenadas → se reducen a 2 decimales (~1 km).
        - Texto libre → se pasa por scrub de PII.
        - Edad → rango etario.
        - Constantes vitales → ruido ±5 %.
        """
        anon = {}
        for key, value in record.items():
            k = key.lower()

            # 1. Supresión total de campos PII
            if k in _SUPPRESS_FIELDS:
                continue

            # 2. Generalización de coordenadas
            if k in ("lat", "latitude") and isinstance(value, (int, float)):
                anon[k] = round(float(value), 2)  # ~1.1 km precisión
                continue
            if k in ("lon", "longitude", "lng") and isinstance(value, (int, float)):
                anon[k] = round(float(value), 2)
                continue

            # 3. Generalización de edad → rango
            if k in ("patient_age", "age") and isinstance(value, (int, float)):
                anon["age_range"] = self._age_to_range(int(value))
                continue

            # 4. Generalización de dirección → zona/distrito
            if k in ("address", "direccion") and isinstance(value, str):
                anon["zone"] = self._address_to_zone(value)
                continue

            # 5. Perturbación de constantes vitales
            if k in (
                "heart_rate", "blood_pressure_sys", "blood_pressure_dia",
                "respiratory_rate", "spo2", "temperature",
                "glasgow_score", "pain_scale",
            ) and isinstance(value, (int, float)):
                anon[k] = self._perturb_numeric(value, pct=0.05)
                continue

            # 6. Scrub de texto libre
            if k in (
                "description", "chief_complaint", "symptoms",
                "treatment", "notes", "details", "medical_history",
                "observations", "allergies", "medications",
            ) and isinstance(value, str):
                anon[k] = self.anonymize_text(value)
                continue

            # 7. Fechas → solo fecha (sin hora exacta)
            if k.endswith("_at") or k.endswith("_time"):
                if isinstance(value, datetime):
                    anon[k] = value.strftime("%Y-%m-%d")
                elif isinstance(value, str) and "T" in value:
                    anon[k] = value.split("T")[0]
                else:
                    anon[k] = value
                continue

            # 8. Resto de campos → pasar sin cambios
            anon[k] = value

        # Añadir hash de anonimización (trazabilidad sin re-identificación)
        anon["_anon_hash"] = self._pseudonymize_id(
            str(record.get("id", record.get("incident_id", "")))
        )
        anon["_anon_ts"] = datetime.utcnow().isoformat()

        return anon

    def anonymize_incident_for_training(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """
        Anonimiza un incidente para añadirlo al dataset de reentrenamiento
        del clasificador de severidad.

        Retorna solo los campos relevantes para el modelo.
        """
        anon = self.anonymize_record(incident)

        # Campos que necesita el severity_dataset.csv
        return {
            "description": anon.get("description", ""),
            "incident_type": anon.get("incident_type", "GENERAL"),
            "affected_count": anon.get("affected_count", 1),
            "severity": anon.get("severity", "MEDIUM"),
            "lat": anon.get("lat"),
            "lon": anon.get("lon"),
        }

    def anonymize_chat_for_training(self, message: str, intent: str) -> Dict[str, str]:
        """Anonimiza un mensaje de chat para el dataset de intents."""
        return {
            "intent": intent,
            "text": self.anonymize_text(message),
        }

    def anonymize_patient_record(self, pcr: Dict[str, Any]) -> Dict[str, Any]:
        """
        Anonimiza un ePCR completo.
        Conserva datos clínicos perturbados, elimina identidad.
        """
        return self.anonymize_record(pcr)

    # ─── Helpers internos ──────────────────────────────

    def _age_to_range(self, age: int) -> str:
        """Convierte edad exacta a rango etario."""
        if age < 1:
            return "NEONATO"
        if age < 5:
            return "INFANTIL_0-4"
        if age < 13:
            return "PEDIATRIC_5-12"
        if age < 18:
            return "ADOLESCENTE_13-17"
        if age < 30:
            return "ADULTO_18-29"
        if age < 45:
            return "ADULTO_30-44"
        if age < 65:
            return "ADULTO_45-64"
        if age < 80:
            return "MAYOR_65-79"
        return "MAYOR_80+"

    def _address_to_zone(self, address: str) -> str:
        """Extrae zona/distrito genérico de una dirección."""
        # Intentar extraer código postal
        cp_match = re.search(r"\b(\d{5})\b", address)
        if cp_match:
            return f"CP_{cp_match.group(1)[:3]}xx"  # Solo primeros 3 dígitos

        # Intentar extraer barrio/distrito conocido
        for district in [
            "Centro", "Chamberí", "Salamanca", "Retiro", "Arganzuela",
            "Moncloa", "Chamartín", "Tetuán", "Fuencarral", "Latina",
            "Carabanchel", "Usera", "Puente de Vallecas", "Moratalaz",
            "Ciudad Lineal", "Hortaleza", "Villaverde", "Barajas",
        ]:
            if district.lower() in address.lower():
                return f"DISTRITO_{district.upper()}"

        return "ZONA_DESCONOCIDA"

    def _perturb_numeric(self, value: float, pct: float = 0.05) -> float:
        """Añade ruido gaussiano al valor (±pct%)."""
        noise = self._rng.gauss(0, abs(value) * pct)
        result = value + noise
        if isinstance(value, int):
            return max(0, int(round(result)))
        return round(result, 1)

    def _pseudonymize_id(self, original_id: str) -> str:
        """Genera pseudónimo irreversible de un ID original."""
        return hashlib.sha256(
            f"{self._salt}:{original_id}".encode()
        ).hexdigest()[:12]


# ─── Singleton global ─────────────────────────────────
_anonymizer: Optional[DataAnonymizer] = None


def get_anonymizer() -> DataAnonymizer:
    """Obtiene instancia singleton del anonimizador."""
    global _anonymizer
    if _anonymizer is None:
        _anonymizer = DataAnonymizer()
    return _anonymizer
