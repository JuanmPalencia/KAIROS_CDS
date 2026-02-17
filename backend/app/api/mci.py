"""MCI (Incidente con Múltiples Víctimas) — Triaje START + Instrucciones pre-arrival."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from ..storage.db import get_db
from ..storage.models_sql import MCITriage, IncidentSQL

router = APIRouter(prefix="/api/mci", tags=["mci"])


# ── START Triage Protocol ──
# Adaptado al sistema español de triaje prehospitalario

START_PROTOCOL = {
    "steps": [
        {"id": 1, "question": "¿Puede caminar?", "yes": "VERDE", "no": "step_2"},
        {"id": 2, "question": "¿Respira?", "yes": "step_3", "no": "step_2b"},
        {"id": 3, "question": "¿Frecuencia respiratoria > 30/min?", "yes": "ROJO", "no": "step_4"},
        {"id": 4, "question": "¿Relleno capilar > 2 segundos?", "yes": "ROJO", "no": "step_5"},
        {"id": 5, "question": "¿Obedece órdenes sencillas?", "yes": "AMARILLO", "no": "ROJO"},
    ],
    "step_2b": {"action": "Abrir vía aérea", "question": "¿Respira ahora?", "yes": "ROJO", "no": "NEGRO"},
    "colors": {
        "VERDE": {"label": "Leve", "priority": 3, "description": "Puede caminar, heridas menores. Espera."},
        "AMARILLO": {"label": "Urgente", "priority": 2, "description": "No puede caminar pero estable. Atención diferida."},
        "ROJO": {"label": "Emergencia", "priority": 1, "description": "Inmediata. Riesgo vital inminente."},
        "NEGRO": {"label": "Fallecido/No recuperable", "priority": 4, "description": "Sin signos vitales tras apertura de vía aérea."},
    }
}


# ── Pre-arrival instructions (Instrucciones pre-llegada) ──
PRE_ARRIVAL_INSTRUCTIONS = {
    "CARDIO": {
        "title": "Dolor Torácico / Parada Cardíaca",
        "steps": [
            "1. Mantener al paciente sentado o semiincorporado",
            "2. Aflojar ropa apretada (cinturón, corbata, sujetador)",
            "3. Si tiene prescrita nitroglicerina sublingual, ayudarle a tomarla",
            "4. Si pierde la consciencia y deja de respirar → iniciar RCP",
            "5. RCP: 30 compresiones / 2 ventilaciones (100-120 lpm)",
            "6. Si hay DEA cercano → enviar a alguien a buscarlo",
            "7. No dar nada de comer ni beber",
        ],
        "critical": "Si PCR: RCP inmediata + DEA. Cada minuto sin RCP reduce supervivencia un 10%."
    },
    "RESPIRATORY": {
        "title": "Dificultad Respiratoria",
        "steps": [
            "1. Sentar al paciente en posición de trípode (inclinado hacia delante)",
            "2. Aflojar ropa que oprima pecho/cuello",
            "3. Si es asmático, ayudar con su inhalador de rescate (salbutamol)",
            "4. Mantener la calma, hablar con voz tranquila",
            "5. Si deja de respirar → iniciar RCP",
        ],
        "critical": "No tumbar al paciente: empeora la disnea."
    },
    "NEUROLOGICAL": {
        "title": "ACV / Ictus — Código Ictus",
        "steps": [
            "1. Anotar hora EXACTA de inicio de síntomas (crucial para tratamiento)",
            "2. Test FAST: Face (sonrisa asimétrica), Arms (no puede levantar ambos), Speech (arrastra palabras), Time",
            "3. Tumbar con cabeza elevada 30°",
            "4. No dar nada de comer ni beber (riesgo de aspiración)",
            "5. Si vomita → posición lateral de seguridad",
            "6. No administrar medicación",
        ],
        "critical": "Hora de inicio = dato más importante. Ventana trombolisis: 4.5h."
    },
    "TRAUMA": {
        "title": "Traumatismo",
        "steps": [
            "1. No mover al paciente salvo peligro inminente (incendio, derrumbe)",
            "2. Controlar hemorragias: presión directa con tela limpia",
            "3. No retirar objetos clavados",
            "4. Inmovilizar extremidad si sospecha de fractura",
            "5. Abrigar al paciente (prevenir hipotermia)",
            "6. Si inconsciente → posición lateral de seguridad (si no hay sospecha cervical)",
        ],
        "critical": "No mover columna cervical. Mantener alineación cabeza-cuello-tronco."
    },
    "BURN": {
        "title": "Quemaduras",
        "steps": [
            "1. Alejar de la fuente de calor/fuego",
            "2. Enfriar con agua corriente templada durante 20 minutos",
            "3. NO usar hielo, mantequilla, pasta de dientes ni remedios caseros",
            "4. Retirar anillos, pulseras, ropa no adherida",
            "5. Cubrir con gasas estériles o sábana limpia húmeda",
            "6. Si quemadura en cara: vigilar vía aérea",
        ],
        "critical": "Quemaduras >18% SCT o en cara/manos/genitales → centro de quemados."
    },
    "POISONING": {
        "title": "Intoxicación / Envenenamiento",
        "steps": [
            "1. Identificar el tóxico (envase, nombre, cantidad estimada, hora)",
            "2. NO provocar el vómito (salvo indicación telefónica médica)",
            "3. Si es por inhalación: sacar al aire libre",
            "4. Si contacto en piel: retirar ropa y lavar con agua abundante",
            "5. Si inconsciente → posición lateral de seguridad",
            "6. Guardar el envase/producto para los sanitarios",
        ],
        "critical": "Llamar al Instituto de Toxicología: 915 620 420"
    },
    "OBSTETRIC": {
        "title": "Parto Inminente / Emergencia Obstétrica",
        "steps": [
            "1. Tumbar a la mujer sobre su costado izquierdo",
            "2. Preparar toallas limpias y mantas para el bebé",
            "3. Si se ve la cabeza del bebé: NO empujar la cabeza hacia dentro",
            "4. Dejar que salga naturalmente, sujetar con ambas manos",
            "5. Secar al bebé inmediatamente y colocarlo piel con piel sobre la madre",
            "6. NO cortar el cordón umbilical (esperar a los sanitarios)",
        ],
        "critical": "Si prolapso de cordón: elevar caderas de la madre con almohadas."
    },
    "ALLERGIC": {
        "title": "Reacción Alérgica / Anafilaxia",
        "steps": [
            "1. Si tiene autoinyector de adrenalina (EpiPen): ayudar a administrarlo en muslo externo",
            "2. Tumbar con piernas elevadas (si no hay dificultad respiratoria)",
            "3. Si dificultad respiratoria → sentado o semiincorporado",
            "4. Quitar alérgeno si es posible (retirar aguijón, dejar de comer)",
            "5. Vigilar respiración constantemente",
        ],
        "critical": "Anafilaxia puede progresar a PCR en minutos. Adrenalina = tratamiento clave."
    },
    "DROWNING": {
        "title": "Ahogamiento / Sumersión",
        "steps": [
            "1. Sacar del agua (sin ponerse en riesgo)",
            "2. Si no respira → RCP inmediata (empezar con 5 ventilaciones de rescate)",
            "3. Continuar con 30 compresiones / 2 ventilaciones",
            "4. Si vomita → girar de lado, limpiar boca, continuar RCP",
            "5. Abrigar (hipotermia es muy común)",
            "6. Incluso si se recupera: SIEMPRE necesita evaluación hospitalaria (ahogamiento seco)",
        ],
        "critical": "RCP en ahogamiento: empezar siempre con ventilaciones."
    },
    "GENERAL": {
        "title": "Emergencia General",
        "steps": [
            "1. Mantener la calma y vigilar al paciente",
            "2. Si inconsciente pero respira → posición lateral de seguridad",
            "3. Si no respira → iniciar RCP (30:2)",
            "4. Aflojar ropa",
            "5. Abrigar y proteger del frío/calor",
            "6. No dar nada de comer ni beber",
        ],
        "critical": "Vigilar constantemente nivel de consciencia y respiración."
    },
}


class TriageCreate(BaseModel):
    incident_id: str
    tag_color: str  # ROJO, AMARILLO, VERDE, NEGRO
    patient_number: int
    description: Optional[str] = None
    location_in_scene: Optional[str] = None
    can_walk: Optional[bool] = None
    breathing: Optional[bool] = None
    respiratory_rate: Optional[int] = None
    perfusion: Optional[bool] = None
    mental_status: Optional[str] = None


class MCIDeclare(BaseModel):
    incident_id: str
    estimated_victims: int = 5
    scene_description: Optional[str] = None


@router.get("/start-protocol")
def get_start_protocol():
    """Obtener el protocolo START de triaje."""
    return START_PROTOCOL


@router.get("/pre-arrival/{incident_type}")
def get_pre_arrival_instructions(incident_type: str):
    """Obtener instrucciones pre-llegada por tipo de incidente."""
    instructions = PRE_ARRIVAL_INSTRUCTIONS.get(incident_type.upper())
    if not instructions:
        instructions = PRE_ARRIVAL_INSTRUCTIONS["GENERAL"]
    return instructions


@router.get("/pre-arrival")
def list_all_pre_arrival():
    """Listar todos los protocolos de instrucciones pre-llegada."""
    return PRE_ARRIVAL_INSTRUCTIONS


@router.post("/declare")
def declare_mci(body: MCIDeclare, db: Session = Depends(get_db)):
    """Declarar un incidente como IMV (Incidente con Múltiples Víctimas)."""
    inc = db.query(IncidentSQL).filter(IncidentSQL.id == body.incident_id).first()
    if not inc:
        raise HTTPException(404, "Incident not found")

    inc.affected_count = body.estimated_victims
    # Mark as MCI by updating description
    inc.description = f"[IMV] {body.scene_description or inc.description or 'Incidente con múltiples víctimas'}"
    db.commit()
    return {"ok": True, "incident_id": inc.id, "estimated_victims": body.estimated_victims}


@router.post("/triage")
def create_triage_tag(body: TriageCreate, db: Session = Depends(get_db)):
    """Crear una etiqueta de triaje START para una víctima del IMV."""
    if body.tag_color not in ["ROJO", "AMARILLO", "VERDE", "NEGRO"]:
        raise HTTPException(400, "Tag color must be ROJO, AMARILLO, VERDE or NEGRO")

    tag = MCITriage(
        incident_id=body.incident_id,
        tag_color=body.tag_color,
        patient_number=body.patient_number,
        description=body.description,
        location_in_scene=body.location_in_scene,
        can_walk=body.can_walk,
        breathing=body.breathing,
        respiratory_rate=body.respiratory_rate,
        perfusion=body.perfusion,
        mental_status=body.mental_status,
    )
    db.add(tag)
    db.commit()
    return {"ok": True, "triage_id": tag.id, "tag_color": tag.tag_color}


@router.get("/triage/{incident_id}")
def get_triage_tags(incident_id: str, db: Session = Depends(get_db)):
    """Obtener todas las etiquetas de triaje de un IMV."""
    tags = db.query(MCITriage).filter(
        MCITriage.incident_id == incident_id
    ).order_by(MCITriage.patient_number).all()

    summary = {"ROJO": 0, "AMARILLO": 0, "VERDE": 0, "NEGRO": 0}
    result = []
    for t in tags:
        summary[t.tag_color] = summary.get(t.tag_color, 0) + 1
        result.append({
            "id": t.id,
            "tag_color": t.tag_color,
            "patient_number": t.patient_number,
            "description": t.description,
            "location_in_scene": t.location_in_scene,
            "can_walk": t.can_walk,
            "breathing": t.breathing,
            "respiratory_rate": t.respiratory_rate,
            "mental_status": t.mental_status,
            "assigned_vehicle_id": t.assigned_vehicle_id,
            "status": t.status,
        })

    return {
        "incident_id": incident_id,
        "summary": summary,
        "total_victims": len(tags),
        "tags": result,
    }


@router.put("/triage/{triage_id}/assign")
def assign_triage_patient(triage_id: int, vehicle_id: str, hospital_id: Optional[str] = None,
                           db: Session = Depends(get_db)):
    """Asignar ambulancia a una víctima triada."""
    tag = db.query(MCITriage).filter(MCITriage.id == triage_id).first()
    if not tag:
        raise HTTPException(404, "Triage tag not found")
    tag.assigned_vehicle_id = vehicle_id
    tag.destination_hospital_id = hospital_id
    tag.status = "IN_TRANSPORT"
    db.commit()
    return {"ok": True}
