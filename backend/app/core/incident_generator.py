# app/core/incident_generator.py
"""
Generador automático de incidentes realistas para Madrid.

Genera incidentes aleatorios con:
- Ubicaciones reales en Madrid (calles y barrios)
- Tipos variados con distribución realista de frecuencia
- Severidades proporcionales al tipo
- Descripción narrativa automática
"""

import random
import math
from datetime import datetime

# ── Tipos de incidentes con peso relativo de frecuencia ─────────────
# Más peso = más frecuente en la vida real
INCIDENT_TYPES = [
    # Tipo, Peso, Severidad_min, Severidad_max, Descripciones posibles
    {
        "type": "CARDIO",
        "weight": 18,
        "sev_range": (3, 5),
        "descriptions": [
            "Dolor torácico intenso, posible IAM",
            "Parada cardiorrespiratoria en vía pública",
            "Arritmia severa, paciente consciente",
            "Síncope cardiaco, paciente caído",
            "Insuficiencia cardiaca aguda, disnea severa",
        ],
    },
    {
        "type": "RESPIRATORY",
        "weight": 14,
        "sev_range": (2, 4),
        "descriptions": [
            "Crisis asmática severa, dificultad respiratoria",
            "EPOC agudizado, saturación baja",
            "Ahogamiento parcial en piscina",
            "Reacción alérgica con edema de glotis",
            "Neumonía grave, fiebre alta y disnea",
        ],
    },
    {
        "type": "NEUROLOGICAL",
        "weight": 10,
        "sev_range": (3, 5),
        "descriptions": [
            "Posible ictus, déficit neurológico agudo",
            "Convulsiones tónico-clónicas generalizadas",
            "Pérdida súbita de consciencia",
            "Cefalea intensa con rigidez de nuca",
            "Parálisis facial súbita, sospecha ACV",
        ],
    },
    {
        "type": "TRAUMA",
        "weight": 20,
        "sev_range": (2, 5),
        "descriptions": [
            "Accidente de tráfico, colisión frontal",
            "Caída desde altura (2º piso), politraumatismo",
            "Atropello de peatón, traumatismo craneal",
            "Accidente de moto, fractura abierta de fémur",
            "Caída en obra, traumatismo vertebral",
            "Colisión múltiple en M-30, varios heridos",
            "Ciclista atropellado, traumatismo torácico",
        ],
    },
    {
        "type": "BURN",
        "weight": 5,
        "sev_range": (2, 5),
        "descriptions": [
            "Quemaduras por explosión de gas en vivienda",
            "Quemaduras químicas en laboratorio industrial",
            "Incendio en vivienda, quemaduras en 30% SCT",
            "Quemaduras por aceite hirviendo en cocina",
            "Electrocución con quemaduras de contacto",
        ],
    },
    {
        "type": "POISONING",
        "weight": 6,
        "sev_range": (2, 4),
        "descriptions": [
            "Intoxicación por monóxido de carbono en vivienda",
            "Sobreingesta medicamentosa voluntaria",
            "Intoxicación etílica grave, coma alcohólico",
            "Intoxicación alimentaria severa, vómitos",
            "Contacto con sustancia química industrial",
        ],
    },
    {
        "type": "OBSTETRIC",
        "weight": 4,
        "sev_range": (3, 5),
        "descriptions": [
            "Parto inminente en domicilio, semana 39",
            "Hemorragia en gestante, tercer trimestre",
            "Eclampsia, convulsiones en embarazada",
            "Complicación postparto, hemorragia severa",
        ],
    },
    {
        "type": "PEDIATRIC",
        "weight": 7,
        "sev_range": (2, 5),
        "descriptions": [
            "Lactante con dificultad respiratoria aguda",
            "Convulsión febril en niño de 3 años",
            "Caída infantil, traumatismo craneal leve",
            "Reacción alérgica severa en menor",
            "Atragantamiento en niño pequeño",
            "Intoxicación accidental por producto de limpieza",
        ],
    },
    {
        "type": "PSYCHIATRIC",
        "weight": 5,
        "sev_range": (1, 3),
        "descriptions": [
            "Crisis de ansiedad severa, hiperventilación",
            "Intento autolítico, paciente en cornisa",
            "Agitación psicomotriz, riesgo para terceros",
            "Brote psicótico agudo en vía pública",
        ],
    },
    {
        "type": "VIOLENCE",
        "weight": 4,
        "sev_range": (2, 5),
        "descriptions": [
            "Agresión con arma blanca, herida inciso-cortante",
            "Pelea callejera, traumatismo facial múltiple",
            "Violencia doméstica, contusiones múltiples",
            "Agresión grupal, víctima inconsciente",
            "Herida por arma de fuego (poco frecuente)",
        ],
    },
    {
        "type": "ALLERGIC",
        "weight": 5,
        "sev_range": (2, 5),
        "descriptions": [
            "Anafilaxia por picadura de avispa",
            "Shock anafiláctico por alimento (frutos secos)",
            "Reacción alérgica severa a medicamento",
            "Urticaria gigante con compromiso respiratorio",
        ],
    },
    {
        "type": "METABOLIC",
        "weight": 6,
        "sev_range": (2, 4),
        "descriptions": [
            "Hipoglucemia severa, paciente diabético inconsciente",
            "Cetoacidosis diabética, deshidratación grave",
            "Crisis hipertensiva, TA > 220/120 mmHg",
            "Golpe de calor, hipertermia maligna",
            "Hipotermia severa en persona sin hogar",
        ],
    },
    {
        "type": "INTOXICATION",
        "weight": 4,
        "sev_range": (1, 4),
        "descriptions": [
            "Sobredosis de opiáceos, depresión respiratoria",
            "Intoxicación por drogas de síntesis en discoteca",
            "Bad trip severo, agitación extrema",
            "Coma etílico en menor de edad",
        ],
    },
    {
        "type": "DROWNING",
        "weight": 2,
        "sev_range": (4, 5),
        "descriptions": [
            "Ahogamiento en piscina comunitaria",
            "Caída al río Manzanares, rescate acuático",
            "Inmersión prolongada, parada respiratoria",
        ],
    },
    {
        "type": "FALL",
        "weight": 8,
        "sev_range": (1, 4),
        "descriptions": [
            "Caída de anciano en domicilio, fractura de cadera",
            "Tropiezo en acera, traumatismo en muñeca",
            "Resbalón en escaleras, dolor lumbar intenso",
            "Caída en supermercado, contusión craneal",
            "Anciano caído sin poder levantarse, posible fractura",
        ],
    },
    {
        "type": "GENERAL",
        "weight": 8,
        "sev_range": (1, 3),
        "descriptions": [
            "Malestar general, evaluación en vía pública",
            "Persona encontrada inconsciente en banco",
            "Fiebre alta y desorientación en anciano",
            "Dolor abdominal agudo, posible abdomen quirúrgico",
            "Lipotimia en centro comercial",
        ],
    },
]

# ── Ubicaciones realistas en Madrid ─────────────────────────────────
MADRID_LOCATIONS = [
    {"lat": 40.4168, "lon": -3.7038, "address": "Puerta del Sol, Centro", "city": "Madrid"},
    {"lat": 40.4530, "lon": -3.6883, "address": "Paseo de la Castellana 200, Chamartín", "city": "Madrid"},
    {"lat": 40.4070, "lon": -3.6920, "address": "Parque del Retiro", "city": "Madrid"},
    {"lat": 40.4380, "lon": -3.6950, "address": "Calle Serrano 45, Salamanca", "city": "Madrid"},
    {"lat": 40.3850, "lon": -3.7100, "address": "Avenida de Oporto, Usera", "city": "Madrid"},
    {"lat": 40.4250, "lon": -3.7120, "address": "Gran Vía 32, Centro", "city": "Madrid"},
    {"lat": 40.4650, "lon": -3.7050, "address": "Hospital La Paz, Fuencarral", "city": "Madrid"},
    {"lat": 40.4100, "lon": -3.7500, "address": "Casa de Campo", "city": "Madrid"},
    {"lat": 40.4400, "lon": -3.7200, "address": "AZCA, Tetuán", "city": "Madrid"},
    {"lat": 40.3960, "lon": -3.7210, "address": "Plaza Elíptica, Carabanchel", "city": "Madrid"},
    {"lat": 40.4470, "lon": -3.6640, "address": "Avenida de América, Prosperidad", "city": "Madrid"},
    {"lat": 40.4300, "lon": -3.6760, "address": "Calle Alcalá 300, Ventas", "city": "Madrid"},
    {"lat": 40.4020, "lon": -3.6740, "address": "Puente de Vallecas", "city": "Madrid"},
    {"lat": 40.3780, "lon": -3.6850, "address": "Villa de Vallecas", "city": "Madrid"},
    {"lat": 40.4600, "lon": -3.6380, "address": "Aeropuerto Barajas T4", "city": "Madrid"},
    {"lat": 40.4530, "lon": -3.7300, "address": "Dehesa de la Villa", "city": "Madrid"},
    {"lat": 40.4150, "lon": -3.7070, "address": "Plaza Mayor, Centro", "city": "Madrid"},
    {"lat": 40.4200, "lon": -3.7060, "address": "Calle Montera, Centro", "city": "Madrid"},
    {"lat": 40.4480, "lon": -3.7100, "address": "Estadio Santiago Bernabéu", "city": "Madrid"},
    {"lat": 40.4010, "lon": -3.6960, "address": "Estación de Atocha", "city": "Madrid"},
    {"lat": 40.4330, "lon": -3.7040, "address": "Tribunal, Malasaña", "city": "Madrid"},
    {"lat": 40.4390, "lon": -3.6870, "address": "Barrio de Salamanca, Goya", "city": "Madrid"},
    {"lat": 40.3900, "lon": -3.7450, "address": "Colonia Jardín, Latina", "city": "Madrid"},
    {"lat": 40.4700, "lon": -3.6900, "address": "Hortaleza", "city": "Madrid"},
    {"lat": 40.4350, "lon": -3.7150, "address": "Calle Fuencarral, Centro", "city": "Madrid"},
    {"lat": 40.4060, "lon": -3.7150, "address": "Embajadores, Lavapiés", "city": "Madrid"},
    {"lat": 40.4440, "lon": -3.7050, "address": "Alonso Martínez, Chamberí", "city": "Madrid"},
    {"lat": 40.3830, "lon": -3.7350, "address": "Aluche, Latina", "city": "Madrid"},
    {"lat": 40.4580, "lon": -3.6750, "address": "Arturo Soria, Ciudad Lineal", "city": "Madrid"},
    {"lat": 40.4120, "lon": -3.6830, "address": "Ibiza, Retiro", "city": "Madrid"},
]


def generate_random_incident() -> dict:
    """Genera un incidente aleatorio realista para Madrid.

    Returns:
        dict con: lat, lon, severity, incident_type, description,
                  address, city, province, affected_count
    """
    # Selección ponderada del tipo de incidente
    types = INCIDENT_TYPES
    weights = [t["weight"] for t in types]
    chosen = random.choices(types, weights=weights, k=1)[0]

    # Ubicación (base real + jitter de hasta ~200m)
    loc = random.choice(MADRID_LOCATIONS)
    jitter_lat = random.uniform(-0.002, 0.002)
    jitter_lon = random.uniform(-0.002, 0.002)

    severity = random.randint(*chosen["sev_range"])
    description = random.choice(chosen["descriptions"])

    # Afectados: normalmente 1, a veces más en accidentes/catástrofes
    affected = 1
    if chosen["type"] == "TRAUMA" and severity >= 4:
        affected = random.randint(1, 4)
    elif chosen["type"] in ("BURN", "DROWNING"):
        affected = random.randint(1, 3)
    elif chosen["type"] == "VIOLENCE" and severity >= 4:
        affected = random.randint(1, 3)

    return {
        "lat": round(loc["lat"] + jitter_lat, 6),
        "lon": round(loc["lon"] + jitter_lon, 6),
        "severity": severity,
        "incident_type": chosen["type"],
        "description": description,
        "address": loc["address"],
        "city": loc["city"],
        "province": "Madrid",
        "affected_count": affected,
    }


def get_all_incident_types() -> list[dict]:
    """Retorna la lista completa de tipos de incidentes disponibles."""
    return [
        {"type": t["type"], "weight": t["weight"], "sev_range": list(t["sev_range"])}
        for t in INCIDENT_TYPES
    ]
