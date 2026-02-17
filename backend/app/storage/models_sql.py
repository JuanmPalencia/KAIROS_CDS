from sqlalchemy import String, Float, Boolean, Integer, Column, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from .db import Base

class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[str] = mapped_column(String, primary_key=True)      # "SVA-001"
    type: Mapped[str] = mapped_column(String, default="AMB")       # AMB (ambulancia genérica)
    subtype: Mapped[str] = mapped_column(String, default="SVB")    # SVB/SVA/VIR/VAMM/SAMU
    status: Mapped[str] = mapped_column(String, default="IDLE")    # IDLE/EN_ROUTE/REFUELING/...

    lat: Mapped[float] = mapped_column(Float, default=40.4168)
    lon: Mapped[float] = mapped_column(Float, default=-3.7038)

    speed: Mapped[float] = mapped_column(Float, default=0.0)
    fuel: Mapped[float] = mapped_column(Float, default=100.0)      # % del depósito
    tank_capacity: Mapped[float] = mapped_column(Float, default=80.0)  # Litros reales del depósito

    route_progress: Mapped[float] = mapped_column(Float, default=0.0)  # Progress on route (0.0-1.0)

    trust_score: Mapped[int] = mapped_column(Integer, default=100) # 0-100
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    sim_vehicle_ref: Mapped[str | None] = mapped_column(String, nullable=True)

class IncidentSQL(Base):
    __tablename__ = "incidents"
    id = Column(String, primary_key=True, index=True)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    severity = Column(Integer, default=1)  # 1-5
    status = Column(String, default="OPEN")  # OPEN / ASSIGNED / EN_ROUTE / ARRIVED / RESOLVED / CLOSED
    assigned_vehicle_id = Column(String, nullable=True)
    assigned_hospital_id = Column(String, nullable=True)  # Hospital asignado
    suggested_hospital_id = Column(String, nullable=True)  # Sugerencia de IA
    ai_confidence = Column(Float, nullable=True)  # Confianza de la IA (0-1)
    ai_reasoning = Column(Text, nullable=True)  # Explicación de la IA
    route_data = Column(Text, nullable=True)  # JSON con ruta de OpenStreetMap
    route_phase = Column(String, default="TO_INCIDENT")  # TO_INCIDENT / TO_HOSPITAL / COMPLETED
    incident_type = Column(String, default="GENERAL")  # CARDIO, RESPIRATORY, etc.
    description = Column(Text, nullable=True)
    address = Column(String, nullable=True)
    city = Column(String, nullable=True)
    province = Column(String, nullable=True)
    affected_count = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="VIEWER")  # ADMIN, OPERATOR, DOCTOR, VIEWER
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    user_id = Column(Integer, nullable=True)
    username = Column(String, nullable=True)
    action = Column(String, nullable=False)  # CREATE, UPDATE, DELETE, LOGIN, etc.
    resource = Column(String, nullable=True)  # INCIDENT, VEHICLE, USER, etc.
    resource_id = Column(String, nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    # Blockchain notarization (BSV)
    blockchain_hash = Column(String, nullable=True, index=True)  # SHA-256 del registro canónico
    blockchain_tx_id = Column(String, nullable=True)  # BSV transaction ID
    # Merkle batch reference
    merkle_batch_id = Column(Integer, ForeignKey("merkle_batches.id"), nullable=True)


class MerkleBatch(Base):
    """Batch de audit logs notarizado como un solo Merkle Root en BSV.

    N audit hashes → Merkle Tree → 1 TX con merkle_root → todos verificables.
    """
    __tablename__ = "merkle_batches"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    merkle_root = Column(String, nullable=False, unique=True, index=True)
    leaf_count = Column(Integer, nullable=False)  # Número de audit logs en el batch
    leaf_hashes = Column(Text, nullable=False)  # JSON array de hashes (orden importa)
    merkle_tree_json = Column(Text, nullable=True)  # Árbol completo para generar proofs
    tx_id = Column(String, nullable=True)  # BSV transaction ID
    status = Column(String, default="PENDING")  # PENDING / ON_CHAIN / FAILED
    network = Column(String, default="main")
    explorer_url = Column(String, nullable=True)


class Hospital(Base):
    __tablename__ = "hospitals"
    id = Column(String, primary_key=True, index=True)  # "HOSP-001"
    name = Column(String, nullable=False)
    address = Column(String, nullable=True)
    city = Column(String, default="Madrid")
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    capacity = Column(Integer, default=100)  # Capacidad total
    current_load = Column(Integer, default=0)  # Pacientes actuales
    specialties = Column(Text, nullable=True)  # JSON string con especialidades
    emergency_level = Column(Integer, default=1)  # 1-3: básico, medio, avanzado
    available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class GasStation(Base):
    """Gasolineras / puntos de recarga de combustible."""
    __tablename__ = "gas_stations"
    id = Column(String, primary_key=True, index=True)  # "GAS-001"
    name = Column(String, nullable=False)
    brand = Column(String, nullable=True)  # "Repsol", "Cepsa", "BP"...
    address = Column(String, nullable=True)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    fuel_types = Column(Text, nullable=True)  # JSON: ["diesel","gasolina95"]
    price_per_liter = Column(Float, default=1.65)
    is_open = Column(Boolean, default=True)
    open_24h = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# ═══════════════════════════════════════════════════════════
# NEW MODELS — Real-world emergency management features
# ═══════════════════════════════════════════════════════════


class CrewMember(Base):
    """Personal sanitario / tripulación de ambulancia."""
    __tablename__ = "crew_members"
    id = Column(String, primary_key=True, index=True)  # "CREW-001"
    name = Column(String, nullable=False)
    role = Column(String, default="TES")  # TES, ENFERMERO, MEDICO, CONDUCTOR
    certification = Column(String, nullable=True)  # BLS, ACLS, PHTLS, ATLS
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    photo_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Shift(Base):
    """Turnos de trabajo asignados a tripulaciones."""
    __tablename__ = "shifts"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    crew_member_id = Column(String, ForeignKey("crew_members.id"), nullable=False)
    vehicle_id = Column(String, ForeignKey("vehicles.id"), nullable=True)
    shift_type = Column(String, default="DIA")  # DIA (8-20), NOCHE (20-8), GUARDIA_24H
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    status = Column(String, default="SCHEDULED")  # SCHEDULED, ACTIVE, COMPLETED, CANCELLED
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class PatientCareReport(Base):
    """ePCR — Informe clínico electrónico del paciente."""
    __tablename__ = "patient_care_reports"
    id = Column(String, primary_key=True, index=True)  # "PCR-001"
    incident_id = Column(String, ForeignKey("incidents.id"), nullable=False)
    vehicle_id = Column(String, ForeignKey("vehicles.id"), nullable=True)
    crew_member_id = Column(String, ForeignKey("crew_members.id"), nullable=True)
    # Datos paciente
    patient_name = Column(String, nullable=True)
    patient_age = Column(Integer, nullable=True)
    patient_gender = Column(String, nullable=True)  # M, F, X
    patient_id_number = Column(String, nullable=True)  # DNI/NIE
    # Valoración inicial
    chief_complaint = Column(Text, nullable=True)
    symptoms = Column(Text, nullable=True)  # JSON array
    allergies = Column(Text, nullable=True)
    medications = Column(Text, nullable=True)
    medical_history = Column(Text, nullable=True)
    # Constantes vitales
    heart_rate = Column(Integer, nullable=True)
    blood_pressure_sys = Column(Integer, nullable=True)
    blood_pressure_dia = Column(Integer, nullable=True)
    respiratory_rate = Column(Integer, nullable=True)
    spo2 = Column(Integer, nullable=True)
    temperature = Column(Float, nullable=True)
    glasgow_score = Column(Integer, nullable=True)  # 3-15
    pain_scale = Column(Integer, nullable=True)  # 0-10
    # Tratamiento
    treatment = Column(Text, nullable=True)
    medications_administered = Column(Text, nullable=True)  # JSON
    procedures = Column(Text, nullable=True)  # JSON: intubación, vía, etc.
    # MPDS / Triage telefónico
    mpds_code = Column(String, nullable=True)  # "10-D-1" Chest Pain DELTA
    mpds_determinant = Column(String, nullable=True)  # ALPHA/BRAVO/CHARLIE/DELTA/ECHO
    # Resultado
    disposition = Column(String, nullable=True)  # HOSPITAL_TRANSFER, ON_SCENE_RELEASE, DECEASED
    receiving_hospital_id = Column(String, ForeignKey("hospitals.id"), nullable=True)
    # Timestamps
    scene_arrival = Column(DateTime, nullable=True)
    scene_departure = Column(DateTime, nullable=True)
    hospital_arrival = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DEALocation(Base):
    """Puntos de DEA (Desfibrilador Externo Automático) públicos."""
    __tablename__ = "dea_locations"
    id = Column(String, primary_key=True, index=True)  # "DEA-001"
    name = Column(String, nullable=False)
    address = Column(String, nullable=True)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    location_type = Column(String, default="PUBLIC")  # PUBLIC, PRIVATE, TRANSPORT
    installation_date = Column(DateTime, nullable=True)
    last_maintenance = Column(DateTime, nullable=True)
    is_available = Column(Boolean, default=True)
    access_hours = Column(String, nullable=True)  # "24h" / "L-V 8:00-20:00"
    contact_phone = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class FirstResponder(Base):
    """Ciudadanos voluntarios formados en SVB/DEA (primer respondedor)."""
    __tablename__ = "first_responders"
    id = Column(String, primary_key=True, index=True)  # "FR-001"
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    email = Column(String, nullable=True)
    certification = Column(String, default="SVB_DEA")  # SVB_DEA, DESA, RCP
    certification_expiry = Column(DateTime, nullable=True)
    lat = Column(Float, nullable=True)  # Última ubicación conocida
    lon = Column(Float, nullable=True)
    is_available = Column(Boolean, default=True)
    alerts_responded = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class MCITriage(Base):
    """Triaje START para Incidentes con Múltiples Víctimas (IMV)."""
    __tablename__ = "mci_triage"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    incident_id = Column(String, ForeignKey("incidents.id"), nullable=False)
    tag_color = Column(String, nullable=False)  # ROJO, AMARILLO, VERDE, NEGRO
    patient_number = Column(Integer, nullable=False)  # Nº de víctima en el IMV
    description = Column(Text, nullable=True)
    location_in_scene = Column(String, nullable=True)  # "Zona A", "Vehículo 2"
    can_walk = Column(Boolean, nullable=True)  # START: ¿puede caminar?
    breathing = Column(Boolean, nullable=True)  # START: ¿respira?
    respiratory_rate = Column(Integer, nullable=True)  # START: freq resp
    perfusion = Column(Boolean, nullable=True)  # START: relleno capilar <2s
    mental_status = Column(String, nullable=True)  # START: ¿obedece órdenes?
    assigned_vehicle_id = Column(String, nullable=True)
    destination_hospital_id = Column(String, nullable=True)
    status = Column(String, default="PENDING")  # PENDING, IN_TRANSPORT, AT_HOSPITAL
    created_at = Column(DateTime, default=datetime.utcnow)


class PatientTracking(Base):
    """Seguimiento del ciclo de vida del paciente: escena → ambulancia → urgencias → alta."""
    __tablename__ = "patient_tracking"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    incident_id = Column(String, ForeignKey("incidents.id"), nullable=False)
    epcr_id = Column(String, ForeignKey("patient_care_reports.id"), nullable=True)
    patient_name = Column(String, nullable=True)
    current_phase = Column(String, default="ON_SCENE")
    # ON_SCENE → IN_AMBULANCE → AT_HOSPITAL_ER → ADMITTED → DISCHARGED
    vehicle_id = Column(String, nullable=True)
    hospital_id = Column(String, nullable=True)
    hospital_bed = Column(String, nullable=True)
    admission_time = Column(DateTime, nullable=True)
    discharge_time = Column(DateTime, nullable=True)
    discharge_disposition = Column(String, nullable=True)  # HOME, ICU, WARD, DECEASED, AMA
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class KPISnapshot(Base):
    """Snapshot periódico de KPIs operativos."""
    __tablename__ = "kpi_snapshots"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    # Tiempos de respuesta
    avg_response_time_sec = Column(Float, nullable=True)  # Activación → llegada escena
    avg_scene_time_sec = Column(Float, nullable=True)  # Tiempo en escena
    avg_transport_time_sec = Column(Float, nullable=True)  # Escena → hospital
    avg_total_time_sec = Column(Float, nullable=True)  # Total del caso
    # Compliance
    response_under_8min_pct = Column(Float, nullable=True)  # % < 8 min (estándar SAMUR)
    response_under_15min_pct = Column(Float, nullable=True)  # % < 15 min (urbano)
    # Volúmenes
    incidents_total = Column(Integer, default=0)
    incidents_resolved = Column(Integer, default=0)
    incidents_open = Column(Integer, default=0)
    vehicles_active = Column(Integer, default=0)
    vehicles_idle = Column(Integer, default=0)
    # Utilización
    fleet_utilization_pct = Column(Float, nullable=True)
    avg_fuel_pct = Column(Float, nullable=True)
    # MCI
    mci_events = Column(Integer, default=0)


class WeatherCondition(Base):
    """Condiciones meteorológicas que afectan a las operaciones."""
    __tablename__ = "weather_conditions"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    lat = Column(Float, default=40.4168)
    lon = Column(Float, default=-3.7038)
    condition = Column(String, default="CLEAR")  # CLEAR, RAIN, HEAVY_RAIN, STORM, SNOW, FOG, HEAT
    temperature_c = Column(Float, nullable=True)
    humidity_pct = Column(Float, nullable=True)
    wind_speed_kmh = Column(Float, nullable=True)
    visibility_km = Column(Float, nullable=True)
    eta_multiplier = Column(Float, default=1.0)  # Factor que ralentiza ETAs (1.0=normal, 1.5=lluvia)
    alert_level = Column(String, default="GREEN")  # GREEN, YELLOW, ORANGE, RED
    description = Column(Text, nullable=True)


class GISLayer(Base):
    """Puntos de interés GIS: colegios, residencias, industria HAZMAT, etc."""
    __tablename__ = "gis_layers"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    layer_type = Column(String, nullable=False)  # SCHOOL, NURSING_HOME, HAZMAT, METRO, POLICE, FIRE
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    address = Column(String, nullable=True)
    details = Column(Text, nullable=True)  # JSON con info extra
    risk_level = Column(Integer, default=1)  # 1-5
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AgencyResource(Base):
    """Recursos de otras agencias (Bomberos, Policía, Protección Civil)."""
    __tablename__ = "agency_resources"
    id = Column(String, primary_key=True, index=True)
    agency = Column(String, nullable=False)  # BOMBEROS, POLICIA_NACIONAL, POLICIA_MUNICIPAL, PROTECCION_CIVIL
    unit_name = Column(String, nullable=False)
    unit_type = Column(String, nullable=True)  # BUP, BRAVO, ALFA, PATRULLA
    status = Column(String, default="AVAILABLE")  # AVAILABLE, DISPATCHED, ON_SCENE, UNAVAILABLE
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    assigned_incident_id = Column(String, nullable=True)
    contact_radio = Column(String, nullable=True)  # Canal TETRA / frecuencia
    created_at = Column(DateTime, default=datetime.utcnow)