# KAIROS CDS — Ficha Técnica Completa

## Sistema de Gemelo Digital para Gestión de Flotas de Emergencia

**Versión:** 1.0.0  
**Fecha:** Febrero 2026  
**Plataforma:** HPE GreenLake Cloud Platform  
**Licencia:** Propietaria — Desarrollo para HPE CDS Challenge  

---

# ÍNDICE

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Visión General del Sistema](#2-visión-general-del-sistema)
3. [Arquitectura de Software](#3-arquitectura-de-software)
4. [Stack Tecnológico](#4-stack-tecnológico)
5. [Infraestructura y Despliegue](#5-infraestructura-y-despliegue)
6. [Base de Datos — Modelo Relacional](#6-base-de-datos--modelo-relacional)
7. [Backend — FastAPI](#7-backend--fastapi)
8. [Motor de Gemelo Digital (TwinEngine)](#8-motor-de-gemelo-digital-twinengine)
9. [Módulos de Inteligencia Artificial](#9-módulos-de-inteligencia-artificial)
10. [Sistema de Ciberseguridad](#10-sistema-de-ciberseguridad)
11. [Blockchain y Auditoría Inmutable](#11-blockchain-y-auditoría-inmutable)
12. [Frontend — React 19](#12-frontend--react-19)
13. [Sistema de Routing (OSRM)](#13-sistema-de-routing-osrm)
14. [Gestión de Incidentes](#14-gestión-de-incidentes)
15. [Gestión de Flota](#15-gestión-de-flota)
16. [Gestión de Tripulaciones y Turnos](#16-gestión-de-tripulaciones-y-turnos)
17. [Atención al Paciente (ePCR)](#17-atención-al-paciente-epcr)
18. [Sistema Hospitalario](#18-sistema-hospitalario)
19. [KPIs y Analytics](#19-kpis-y-analytics)
20. [Monitorización (Prometheus + Alertmanager)](#20-monitorización-prometheus--alertmanager)
21. [Comunicación en Tiempo Real](#21-comunicación-en-tiempo-real)
22. [Sistema de Roles y Permisos (RBAC)](#22-sistema-de-roles-y-permisos-rbac)
23. [Simulación y Generación de Incidentes](#23-simulación-y-generación-de-incidentes)
24. [Gestión de Recursos](#24-gestión-de-recursos)
25. [Referencia Completa de API](#25-referencia-completa-de-api)
26. [Testing y Calidad de Código](#26-testing-y-calidad-de-código)
27. [Configuración y Variables de Entorno](#27-configuración-y-variables-de-entorno)
28. [Guía de Instalación](#28-guía-de-instalación)
29. [Rendimiento y Escalabilidad](#29-rendimiento-y-escalabilidad)
30. [Glosario](#30-glosario)

---

# 1. Resumen Ejecutivo

KAIROS CDS (Clinical Decision Support) es un sistema de gemelo digital en tiempo real para la gestión integral de servicios de emergencias médicas (SEM). El sistema simula, monitoriza y optimiza la operación de flotas de ambulancias a nivel nacional, integrando 10 módulos de inteligencia artificial, blockchain para auditoría inmutable, panel de ciberseguridad completo, y monitorización con Prometheus.

### Capacidades principales

| Capacidad | Descripción |
|---|---|
| **Gemelo Digital** | Motor asíncrono que simula el movimiento de vehículos en tiempo real sobre rutas reales OSRM |
| **IA Integrada** | 10 módulos 100% locales (sklearn): clasificación de severidad, predicción de demanda, ETA, anomalías, mantenimiento predictivo, visión, chat, tráfico, recomendaciones, asignación óptima. Sin dependencias externas (OpenAI, etc.) |
| **Anonimización RGPD** | Pipeline automático de anonimización (supresión + generalización + perturbación) con reentrenamiento continuo de modelos |
| **Blockchain BSV** | Notarización de auditoría con árboles Merkle y difusión on-chain |
| **Ciberseguridad** | Rate limiting, brute-force detection, input scanning, CSRF, gestión de sesiones, firewall de IPs |
| **Monitorización** | Prometheus + Alertmanager con 6 métricas y 4 reglas de alerta |
| **RBAC** | 4 roles: ADMIN, OPERATOR, DOCTOR, VIEWER con 22 permisos granulares |

### Métricas del proyecto

| Métrica | Valor |
|---|---|
| Endpoints API REST | 133 |
| Endpoint WebSocket | 1 |
| Routers API | 21 |
| Páginas frontend | 15 |
| Componentes React | 4 |
| Modelos SQLAlchemy | 18 tablas |
| Módulos de IA | 10 |
| Módulos blockchain | 7 |
| Archivos CSS | 18 |
| Dependencias Python | 26 (sin openai) |
| Dependencias npm | 24 (13 prod + 11 dev) |
| Servicios Docker | 6 (db, redis, backend, frontend, prometheus, alertmanager) |
| Tests automatizados | 13 suites (11 backend + 2 frontend), 72+ tests |

---

# 2. Visión General del Sistema

## 2.1 Problema que resuelve

Los servicios de emergencias médicas (SEM) enfrentan desafíos críticos:

- **Asignación subóptima de recursos**: Los despachos manuales no consideran factores como tráfico, especialización de vehículos ni carga hospitalaria.
- **Falta de visibilidad en tiempo real**: Los gestores no tienen una vista unificada de toda la flota, incidentes y hospitales.
- **Tiempos de respuesta elevados**: Sin predicción de demanda ni asignación inteligente, los tiempos de respuesta superan los estándares SAMUR (8 min / 15 min).
- **Auditoría insuficiente**: Las decisiones operativas no quedan registradas de forma inmutable.
- **Seguridad limitada**: Los sistemas tradicionales carecen de protección activa contra amenazas.

## 2.2 Solución KAIROS CDS

KAIROS CDS aborda cada uno de estos problemas con un enfoque integral:

1. **Gemelo Digital**: Replica el estado operativo en tiempo real, permitiendo simulaciones "what-if" antes de tomar decisiones.
2. **IA para despacho**: La asignación de vehículos y hospitales se basa en distancia, capacidad, severidad, historial y condiciones de tráfico.  
3. **Dashboard unificado**: Mapa Leaflet con capas GIS, heatmaps, rutas y estado de toda la operación.
4. **Blockchain**: Cada acción operativa queda notarizada en BSV, garantizando inmutabilidad legal.
5. **Ciberseguridad proactiva**: Detección de ataques en tiempo real con respuesta automatizada.

## 2.3 Flujo operativo principal

```
Incidente creado (manual/automático)
    │
    ▼
IA clasifica severidad (1-5)
    │
    ▼
IA sugiere vehículo óptimo + hospital
    │
    ▼
Operador confirma/modifica asignación
    │
    ▼
TwinEngine: vehículo EN_ROUTE → ruta OSRM
    │
    ▼
Llegada a incidente → atención al paciente
    │
    ▼
Traslado a hospital → ePCR + Patient Tracking
    │
    ▼
Resolución: hospital notificado, vehículo liberado
    │
    ▼
Auditoría registrada → Merkle batch → BSV blockchain
```

---

# 3. Arquitectura de Software

## 3.1 Diagrama de arquitectura

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          KAIROS CDS — v1.0                                   │
├──────────────────┬─────────────────────────┬─────────────────────────────────┤
│  FRONTEND        │   BACKEND               │  INFRAESTRUCTURA                │
│                  │                          │                                 │
│  React 19        │   FastAPI 0.115          │  PostgreSQL 16 + PostGIS        │
│  Vite 7          │   Python 3.10+           │  Redis 7                        │
│  Leaflet 1.9     │   SQLAlchemy 2.0         │  Prometheus + Alertmanager      │
│  Recharts        │   Pydantic 2.0           │  BSV Blockchain                 │
│  lucide-react    │   uvicorn (ASGI)         │  OSRM (routing externo)         │
│                  │                          │                                 │
│  15 páginas      │   131 endpoints          │  Docker Compose                 │
│  4 componentes   │   21 routers             │  4 servicios                    │
│  18 CSS (dark)   │   10 módulos IA          │  4 volúmenes persistentes       │
│  City filter     │   TwinEngine (async)     │                                 │
│  RoleRoute       │   Cybersecurity stack    │                                 │
│  WebSocket/Poll  │   Merkle + BSV           │                                 │
└──────────────────┴─────────────────────────┴─────────────────────────────────┘
```

## 3.2 Patrones de diseño

| Patrón | Aplicación |
|---|---|
| **Repository Pattern** | `repos/audit_repo.py`, `vehicles_repo.py`, `incidents_repo.py` |
| **Dependency Injection** | FastAPI `Depends()` para auth, DB sessions, roles |
| **Observer Pattern** | WebSocket broadcast + TwinEngine publish |
| **Strategy Pattern** | Módulos IA intercambiables para clasificación, ETA, asignación |
| **Middleware Chain** | Security → CORS → Metrics → Router |
| **Event Sourcing** | Auditoría completa con hash chain |
| **Digital Twin** | Réplica virtual del estado operativo con loop async |

## 3.3 Capas de la aplicación

```
┌───────────────────────────────────┐
│  Presentación (React 19 + Vite)   │  ← UI, rutas, hooks
├───────────────────────────────────┤
│  API (FastAPI routers)            │  ← HTTP/WS, validación Pydantic
├───────────────────────────────────┤
│  Dominio (core modules)          │  ← IA, TwinEngine, blockchain, cybersec
├───────────────────────────────────┤
│  Persistencia (SQLAlchemy + repos)│  ← ORM, queries, migraciones
├───────────────────────────────────┤
│  Infraestructura (Docker)        │  ← PostgreSQL, Redis, Prometheus
└───────────────────────────────────┘
```

---

# 4. Stack Tecnológico

## 4.1 Backend

| Tecnología | Versión | Función |
|---|---|---|
| Python | 3.10+ | Lenguaje principal |
| FastAPI | 0.115 | Framework web ASGI |
| uvicorn | latest | Servidor ASGI con hot-reload |
| SQLAlchemy | 2.0+ | ORM relacional |
| Pydantic | 2.0+ | Validación de datos y schemas |
| psycopg2 | latest | Driver PostgreSQL |
| GeoAlchemy2 | latest | Extensiones espaciales PostGIS |
| python-jose | latest | JWT tokens |
| passlib + bcrypt | latest | Hashing de contraseñas |
| scikit-learn | latest | Machine Learning (RF, GB, IF) |
| pandas + numpy | latest | Procesamiento de datos |
| joblib | latest | Serialización de modelos ML |
| openai | — | Eliminado: todos los modelos son locales (sklearn) |
| httpx | latest | Cliente HTTP asíncrono |
| prometheus-client | latest | Métricas Prometheus |
| redis + hiredis | latest | Cache y pub/sub |
| bsv-sdk | latest | Blockchain BSV |
| Pillow | latest | Procesamiento de imágenes |

## 4.2 Frontend

| Tecnología | Versión | Función |
|---|---|---|
| React | 19 | Biblioteca UI |
| Vite | 7 | Build tool + dev server |
| React Router | 7+ | Routing SPA |
| Leaflet | 1.9 | Mapas interactivos |
| leaflet.heat | latest | Heatmaps |
| leaflet.markercluster | latest | Clustering de marcadores |
| Recharts | latest | Gráficos y visualizaciones |
| lucide-react | latest | Iconos SVG |
| react-hot-toast | latest | Notificaciones toast |
| jsPDF + html2canvas | latest | Exportación PDF |
| date-fns | latest | Manipulación de fechas |

## 4.3 Infraestructura

| Tecnología | Versión | Función |
|---|---|---|
| PostgreSQL | 16 | Base de datos relacional |
| PostGIS | 3.4 | Extensiones geoespaciales |
| Redis | 7 (Alpine) | Cache, pub/sub, sesiones |
| Prometheus | latest | Recolección de métricas |
| Alertmanager | latest | Gestión de alertas |
| Docker Compose | v2 | Orquestación de contenedores |
| OSRM | externo | Routing sobre red viaria real |

---

# 5. Infraestructura y Despliegue

## 5.1 Docker Compose — Servicios

```yaml
services:
  db:
    image: postgis/postgis:16-3.4
    ports: ["55432:5432"]
    environment:
      POSTGRES_USER: twin
      POSTGRES_PASSWORD: twin
      POSTGRES_DB: twin
    volumes: [twin_db:/var/lib/postgresql/data]
    healthcheck:
      test: pg_isready -U twin
      interval: 10s
      retries: 5

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    volumes: [redis_data:/data]
    healthcheck:
      test: redis-cli ping
      interval: 10s
      retries: 5

  backend:
    build: ./backend
    ports: ["5001:5001"]
    depends_on:
      db: { condition: service_healthy }
      redis: { condition: service_healthy }
    environment:
      DATABASE_URL: postgresql+psycopg2://twin:twin@db:5432/twin
      REDIS_HOST: redis
    healthcheck:
      test: python -c "import urllib.request; urllib.request.urlopen('http://localhost:5001/health')"
      interval: 15s
      retries: 5

  frontend:
    build: ./frontend
    ports: ["5173:80"]
    depends_on:
      backend: { condition: service_healthy }
    healthcheck:
      test: wget -qO- http://localhost:80 || exit 1
      interval: 15s
      retries: 3

  prometheus:
    image: prom/prometheus:latest
    ports: ["9090:9090"]
    volumes:
      - prometheus_data:/prometheus
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - ./monitoring/alert.rules.yml:/etc/prometheus/alert.rules.yml

  alertmanager:
    image: prom/alertmanager:latest
    ports: ["9093:9093"]
    volumes:
      - alertmanager_data:/alertmanager
      - ./monitoring/alertmanager.yml:/etc/alertmanager/alertmanager.yml
```

> **Nota:** Los servicios `backend` y `frontend` incluyen Dockerfiles multi-stage optimizados con `.dockerignore` para builds reproducibles. El arranque es en cascada: db → redis → backend → frontend.

## 5.2 Puertos del sistema

| Servicio | Puerto | Protocolo |
|---|---|---|
| Frontend (Vite dev) | 5173 | HTTP |
| Backend (FastAPI) | 5001 | HTTP + WS |
| PostgreSQL | 55432 | TCP |
| Redis | 6379 | TCP |
| Prometheus | 9090 | HTTP |
| Alertmanager | 9093 | HTTP |

## 5.3 Volúmenes persistentes

| Volumen | Datos |
|---|---|
| `twin_db` | Base de datos PostgreSQL |
| `redis_data` | Cache Redis |
| `prometheus_data` | Series temporales de métricas |
| `alertmanager_data` | Configuración y silencios |

## 5.4 Requisitos mínimos de hardware

| Recurso | Mínimo | Recomendado |
|---|---|---|
| CPU | 2 cores | 4+ cores |
| RAM | 4 GB | 8+ GB |
| Disco | 10 GB | 20+ GB (SSD) |
| Red | Conexión a internet para OSRM (opcional) | — |

---

# 6. Base de Datos — Modelo Relacional

## 6.1 Diagrama entidad-relación

```
┌─────────────┐    ┌─────────────────┐    ┌──────────────┐
│  Vehicle     │    │  IncidentSQL    │    │  Hospital    │
│  (vehicles)  │◄───│  (incidents)    │───►│  (hospitals) │
│  PK: id      │    │  PK: id         │    │  PK: id      │
│  type,subtype│    │  severity 1-5   │    │  capacity    │
│  status      │    │  status         │    │  current_load│
│  lat,lon     │    │  assigned_veh   │    │  specialties │
│  fuel        │    │  assigned_hosp  │    │  level 1-3   │
│  trust_score │    │  route_phase    │    └──────────────┘
└──────┬───────┘    │  route_data     │
       │            └───────┬─────────┘    ┌──────────────┐
       │                    │              │  User        │
       │                    │              │  (users)     │
       │                    │              │  PK: id      │
       │                    │              │  role: RBAC  │
┌──────▼───────┐    ┌───────▼─────────┐    └──────────────┘
│  Shift       │    │  PatientCare    │
│  (shifts)    │    │  Report (PCR)   │    ┌──────────────┐
│  crew_member │    │  PK: id         │    │  AuditLog    │
│  vehicle_id  │    │  incident_id    │    │  (audit_logs)│
│  shift_type  │    │  vitals         │    │  action      │
│  status      │    │  mpds_code      │    │  hash SHA256 │
└──────────────┘    │  hospital_id    │    │  merkle_batch│
                    └───────┬─────────┘    └──────┬───────┘
┌──────────────┐    ┌───────▼─────────┐    ┌──────▼───────┐
│  CrewMember  │    │  PatientTrack   │    │  MerkleBatch │
│  (crew_mbrs) │    │  (patient_track)│    │  (merkle_bat)│
│  PK: id      │    │  current_phase  │    │  merkle_root │
│  role (médico│    │  vehicle_id     │    │  tx_id BSV   │
│  cert, phone)│    │  hospital_id    │    │  status      │
└──────────────┘    └─────────────────┘    └──────────────┘
```

## 6.2 Tablas del sistema (18 tablas)

### 6.2.1 `vehicles` — Flota de vehículos

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | VARCHAR (PK) | Identificador único (ej: "SVA-001") |
| `type` | VARCHAR | Tipo genérico: AMBULANCE, RAPID |
| `subtype` | VARCHAR | Subtipo español: SVB, SVA, VIR, VAMM, SAMU |
| `status` | VARCHAR | IDLE, EN_ROUTE, ON_SCENE, RETURNING, MAINTENANCE, REFUELING |
| `lat`, `lon` | FLOAT | Posición GPS en tiempo real |
| `speed` | FLOAT | Velocidad actual (km/h) |
| `fuel` | FLOAT | Nivel de combustible (%) |
| `tank_capacity` | FLOAT | Capacidad del tanque (litros) |
| `route_progress` | FLOAT | Progreso en la ruta actual (0.0–1.0) |
| `trust_score` | FLOAT | Puntuación de confianza IA (0–100) |
| `enabled` | BOOLEAN | Habilitado para servicio |
| `city` | VARCHAR | Ciudad asignada |

### 6.2.2 `incidents` — Incidentes de emergencia

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | VARCHAR (PK) | Identificador único (ej: "INC-0001") |
| `type` | VARCHAR | Tipo: CARDIO, TRAUMA, RESPIRATORY, etc. (16 tipos) |
| `severity` | INTEGER | Nivel de severidad 1–5 (5 = máxima) |
| `status` | VARCHAR | OPEN → ASSIGNED → EN_ROUTE → ARRIVED → RESOLVED → CLOSED |
| `description` | TEXT | Descripción del incidente |
| `lat`, `lon` | FLOAT | Ubicación del incidente |
| `city` | VARCHAR | Ciudad del incidente |
| `affected_count` | INTEGER | Número de afectados |
| `assigned_vehicle_id` | VARCHAR (FK) | Vehículo asignado |
| `assigned_hospital_id` | VARCHAR (FK) | Hospital de destino |
| `suggested_hospital_id` | VARCHAR | Hospital sugerido por IA |
| `ai_confidence` | FLOAT | Confianza de la sugerencia IA |
| `ai_reasoning` | TEXT | Razonamiento de la IA |
| `route_data` | TEXT (JSON) | Datos de ruta OSRM (geometría, waypoints) |
| `route_phase` | VARCHAR | TO_INCIDENT / TO_HOSPITAL / COMPLETED |
| `incident_type` | VARCHAR | Clasificación alternativa |
| `created_at` | TIMESTAMP | Fecha/hora de creación |
| `resolved_at` | TIMESTAMP | Fecha/hora de resolución |

### 6.2.3 `users` — Usuarios del sistema

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | INTEGER (PK) | Autoincremental |
| `username` | VARCHAR (unique) | Nombre de usuario |
| `email` | VARCHAR | Correo electrónico |
| `hashed_password` | VARCHAR | Contraseña hasheada con bcrypt |
| `role` | VARCHAR | ADMIN, OPERATOR, DOCTOR, VIEWER |
| `is_active` | BOOLEAN | Cuenta activa |

### 6.2.4 `hospitals` — Hospitales

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | VARCHAR (PK) | Identificador (ej: "HOSP-001") |
| `name` | VARCHAR | Nombre del hospital |
| `lat`, `lon` | FLOAT | Ubicación GPS |
| `capacity` | INTEGER | Capacidad total de camas |
| `current_load` | INTEGER | Camas ocupadas actualmente |
| `specialties` | VARCHAR | Especialidades (CSV): CARDIAC, TRAUMA, NEURO, BURN, PEDIATRIC, GENERAL |
| `emergency_level` | INTEGER | Nivel de emergencia 1–3 |

### 6.2.5 `crew_members` — Tripulación

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | VARCHAR (PK) | Ej: "CREW-001" |
| `name` | VARCHAR | Nombre completo |
| `role` | VARCHAR | TES, ENFERMERO, MEDICO, CONDUCTOR |
| `certification` | VARCHAR | Certificaciones (CSV): ACLS, ATLS, PHTLS, BLS, SVB_DEA, BTP |
| `phone` | VARCHAR | Teléfono de contacto |
| `email` | VARCHAR | Correo electrónico |
| `is_active` | BOOLEAN | Activo en servicio |

### 6.2.6 `shifts` — Turnos de trabajo

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | INTEGER (PK) | Autoincremental |
| `crew_member_id` | VARCHAR (FK) | Miembro de tripulación |
| `vehicle_id` | VARCHAR (FK) | Vehículo asignado |
| `shift_type` | VARCHAR | DIA (8-20h), NOCHE (20-8h), GUARDIA_24H |
| `start_time` | TIMESTAMP | Inicio del turno |
| `end_time` | TIMESTAMP | Fin del turno |
| `status` | VARCHAR | SCHEDULED, ACTIVE, COMPLETED, CANCELLED |
| `notes` | TEXT | Notas del turno |

### 6.2.7 `patient_care_reports` — ePCR (Electronic Patient Care Report)

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | VARCHAR (PK) | Ej: "PCR-001" |
| `incident_id` | VARCHAR (FK) | Incidente asociado |
| `vehicle_id` | VARCHAR (FK) | Vehículo que transportó |
| `crew_member_id` | VARCHAR (FK) | Sanitario responsable |
| `patient_name` | VARCHAR | Nombre del paciente |
| `patient_age` | INTEGER | Edad |
| `patient_gender` | VARCHAR | Género |
| `chief_complaint` | TEXT | Motivo principal de consulta |
| `heart_rate` | INTEGER | Frecuencia cardíaca (bpm) |
| `blood_pressure_sys/dia` | INTEGER | Presión arterial sistólica/diastólica |
| `respiratory_rate` | INTEGER | Frecuencia respiratoria |
| `spo2` | INTEGER | Saturación de oxígeno (%) |
| `temperature` | FLOAT | Temperatura corporal (°C) |
| `glasgow_score` | INTEGER | Escala de Glasgow (3–15) |
| `pain_scale` | INTEGER | Escala de dolor (0–10) |
| `mpds_code` | VARCHAR | Código MPDS de triaje |
| `treatment` | TEXT | Tratamiento administrado |
| `receiving_hospital_id` | VARCHAR (FK) | Hospital receptor |

### 6.2.8 `patient_tracking` — Seguimiento de pacientes

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | INTEGER (PK) | Autoincremental |
| `incident_id` | VARCHAR (FK) | Incidente asociado |
| `epcr_id` | VARCHAR (FK) | ePCR asociado |
| `patient_name` | VARCHAR | Nombre del paciente |
| `current_phase` | VARCHAR | ON_SCENE → IN_AMBULANCE → AT_HOSPITAL_ER → ADMITTED → DISCHARGED |
| `vehicle_id` | VARCHAR (FK) | Ambulancia utilizada |
| `hospital_id` | VARCHAR (FK) | Hospital de destino |
| `admission_time` | TIMESTAMP | Hora de ingreso hospitalario |
| `discharge_time` | TIMESTAMP | Hora de alta |
| `discharge_disposition` | VARCHAR | HOME, ICU, WARD, DECEASED, AMA |

### 6.2.9 `audit_logs` — Registro de auditoría

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | INTEGER (PK) | Autoincremental |
| `user_id` | INTEGER (FK) | Usuario que realizó la acción |
| `username` | VARCHAR | Nombre del usuario |
| `action` | VARCHAR | CREATE, UPDATE, DELETE, RESOLVE, AI_ACCEPTED, AI_OVERRIDDEN, LOGIN |
| `resource` | VARCHAR | INCIDENT, VEHICLE, HOSPITAL, USER, INCIDENT_ASSIGNMENT |
| `resource_id` | VARCHAR | ID del recurso afectado |
| `details` | TEXT (JSON) | Detalles adicionales |
| `ip_address` | VARCHAR | IP del cliente |
| `blockchain_hash` | VARCHAR | Hash SHA-256 del registro |
| `blockchain_tx_id` | VARCHAR | ID de transacción BSV |
| `merkle_batch_id` | INTEGER (FK) | Batch Merkle asociado |
| `created_at` | TIMESTAMP | Fecha/hora del evento |

### 6.2.10 `merkle_batches` — Lotes Merkle para blockchain

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | INTEGER (PK) | Autoincremental |
| `merkle_root` | VARCHAR | Raíz del árbol Merkle |
| `leaf_count` | INTEGER | Número de hojas (registros) |
| `tx_id` | VARCHAR | Transaction ID en BSV |
| `status` | VARCHAR | PENDING, ON_CHAIN, FAILED |
| `created_at` | TIMESTAMP | Fecha de creación |

### 6.2.11 Tablas adicionales

| Tabla | PK | Función |
|---|---|---|
| `gas_stations` | id (str) | Gasolineras: marca, precio, coordenadas, 24h |
| `dea_locations` | id (str) | Desfibriladores públicos geolocalizados |
| `first_responders` | id (str) | Voluntarios con certificación SVB/DEA |
| `mci_triage` | id (int) | Triaje START: ROJO/AMARILLO/VERDE/NEGRO |
| `kpi_snapshots` | id (int) | Snapshots periódicos de KPIs operativos |
| `weather_conditions` | id (int) | Condiciones meteorológicas + multiplicador ETA |
| `gis_layers` | id (str) | Capas GIS: colegios, residencias, HAZMAT, metro |
| `agency_resources` | id (str) | Recursos multi-agencia: Bomberos, Policía, etc. |

---

# 7. Backend — FastAPI

## 7.1 Estructura del backend

```
backend/
├── app/
│   ├── main.py                 # App FastAPI, lifespan, middleware, WS
│   ├── config.py               # Variables de entorno y constantes
│   ├── requirements.txt        # 27 dependencias Python
│   ├── api/                    # 21 routers (131 endpoints)
│   ├── auth/                   # JWT + bcrypt + RBAC
│   ├── blockchain/             # 7 módulos: Merkle, BSV, integridad
│   ├── core/                   # 17 módulos: IA, TwinEngine, cybersec
│   ├── domain/                 # DTOs Pydantic
│   ├── realtime/               # WebSocket manager
│   └── storage/                # ORM + repositorios
├── models/                     # Modelos ML serializados (.joblib)
└── tests/                      # 11 suites de tests (72+ tests)
```

## 7.2 Middleware stack (orden de ejecución)

```
Request → SecurityHeadersMiddleware
       → SecurityMiddleware (rate limiting + brute-force)
       → CORSMiddleware
       → PrometheusInstrumentator (métricas)
       → Router → Endpoint
```

### SecurityHeadersMiddleware
Añade a cada respuesta:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `Content-Security-Policy: default-src 'self'`
- `Referrer-Policy: strict-origin-when-cross-origin`

### SecurityMiddleware
- Rate limiting por IP: 100 requests/60s por defecto, 5 login/60s
- Detección brute-force: 5 intentos → lockout de 10 min
- Escaneo de inputs: SQL injection, XSS, path traversal
- Logging de eventos de seguridad

## 7.3 Lifecycle (lifespan)

```python
@asynccontextmanager
async def lifespan(app):
    # STARTUP
    Base.metadata.create_all(engine)    # Crear tablas
    twin = TwinEngine()                 # Iniciar gemelo digital
    asyncio.create_task(twin.run())     # Loop async en background
    yield
    # SHUTDOWN
    twin.running = False                # Detener gemelo digital
```

## 7.4 CORS configuración

Origins permitidos:
- `http://localhost:5173` (Vite dev)
- `http://127.0.0.1:5173`
- `http://localhost:3000` (fallback)

Métodos: todos. Headers: todos. Credentials: sí.

---

# 8. Motor de Gemelo Digital (TwinEngine)

## 8.1 Descripción

El TwinEngine es un loop asíncrono que se ejecuta en background durante toda la vida de la aplicación. Cada tick (500ms por defecto, configurable con multiplicador de velocidad 0.5×–20×) realiza:

1. **Auto-asignación**: Incidentes OPEN sin vehículo → asigna el vehículo IDLE más cercano.
2. **Routing**: Calcula ruta OSRM A→B (vehículo→incidente) o A→B→C (vehículo→incidente→hospital).
3. **Simulación de movimiento**: Avanza los vehículos EN_ROUTE a lo largo de su ruta.
4. **Gestión de fases**: 
   - `TO_INCIDENT`: Vehículo viajando al incidente.
   - `TO_HOSPITAL`: Vehículo trasladando paciente al hospital.
   - `COMPLETED`: Incidente resuelto.
5. **Resolución automática**: Al llegar al destino final, crea ePCR + patient tracking, decrementa carga hospitalaria, libera vehículo.
6. **Métricas**: Actualiza contadores Prometheus y telemetría para Digital Twin.

## 8.2 Ciclo de vida de un incidente en TwinEngine

```
OPEN (sin vehículo)
  │
  ├─ Auto-assign: vehículo IDLE más cercano
  │  ├─ vehicle.status = EN_ROUTE
  │  ├─ incident.status = ASSIGNED
  │  ├─ Hospital más cercano asignado
  │  └─ Ruta OSRM calculada (A→B→C)
  │
  ▼
ASSIGNED + TO_INCIDENT
  │
  ├─ sim_adapter.step(): mueve vehículo a lo largo de la ruta
  ├─ Consume combustible realista
  │
  ├─ (route_progress >= incident_waypoint) || (distancia < umbral)
  │
  ▼
TO_HOSPITAL (si hay hospital asignado)
  │
  ├─ Continúa misma ruta (segmento B→C)
  │
  ├─ (route_progress >= 0.95) || (distancia al hospital < umbral)
  │
  ▼
RESOLVED + COMPLETED
  ├─ incident.status = RESOLVED
  ├─ PatientCareReport creado automáticamente
  ├─ PatientTracking creado (fase: AT_HOSPITAL_ER)
  ├─ hospital.current_load decrementado
  ├─ vehicle.status = IDLE (liberado)
  └─ Prometheus: incidents_resolved_total++
```

## 8.3 Constantes del motor

| Constante | Valor | Descripción |
|---|---|---|
| `TICK_MS` | 500 | Milisegundos entre cada tick |
| `ARRIVAL_DIST2` | 0.00005² | Umbral de llegada (cuadrado de distancia en grados) |
| `LOW_FUEL_PCT` | 25% | Umbral de combustible bajo |
| `REFUEL_TICKS` | 16 | Ticks necesarios para repostar |
| Speed multiplier | 0.5×–20× | Rango del multiplicador de velocidad |

## 8.4 Routing OSRM

```
OSRM Server (externo)
  │
  ├─ GET /route/v1/driving/{lon1},{lat1};{lon2},{lat2};{lon3},{lat3}
  │   ?overview=full&geometries=geojson&steps=true
  │
  └─ Respuesta:
     ├─ geometry: array de [lon, lat] para la ruta completa
     ├─ distance: metros totales
     ├─ duration: segundos estimados
     └─ legs[]: segmentos A→B y B→C
```

Fallback: si OSRM no está disponible, se genera una ruta sintética interpolando puntos con jitter aleatorio para simular calles.

---

# 9. Módulos de Inteligencia Artificial

## 9.1 Resumen de módulos

| # | Módulo | Archivo | Algoritmo | Entrenamiento |
|---|---|---|---|---|
| 1 | Clasificación de severidad | `ai_severity_classifier.py` | TF-IDF + RandomForest | `python train_all_models.py` |
| 2 | Predicción de demanda | `ai_demand_prediction.py` | Random Forest | `POST /api/ai/demand/train` |
| 3 | Predicción de ETA | `ai_eta_predictor.py` | Gradient Boosting | `POST /api/ai/eta/train` |
| 4 | Detección de anomalías | `ai_anomaly_detector.py` | Isolation Forest + reglas | `POST /api/ai/anomalies/train` |
| 5 | Mantenimiento predictivo | `ai_maintenance_predictor.py` | Reglas heurísticas | No requiere |
| 6 | Visión por computador | `ai_vision_analyzer.py` | Pillow + TF-IDF + SVM | `python train_all_models.py` |
| 7 | Asistente conversacional | `ai_conversational_assistant.py` | TF-IDF + LogisticRegression | `python train_all_models.py` |
| 8 | Integración de tráfico | `ai_traffic_integration.py` | Reglas + hora del día | No requiere |
| 9 | Recomendaciones | `ai_recommendation_system.py` | Perfil de operador | Automático |
| 10 | Asignación inteligente | `ai_assignment.py` | Multi-criteria scoring | No requiere |

> 🔒 **100% local**: Ningún módulo requiere API keys externas. Todos los modelos se entrenan y ejecutan localmente con scikit-learn.
> 🔄 **Aprendizaje continuo**: Los datos operativos se anonimizan automáticamente (RGPD) y alimentan los datasets de reentrenamiento.

## 9.2 Detalle de cada módulo

### 9.2.1 Clasificación de severidad

**Entrada:** Texto descriptivo del incidente.  
**Salida:** Nivel de severidad 1–5 + justificación + confianza.  
**Algoritmo:** TF-IDF + RandomForestClassifier (200 estimadores).  
**Modelo:** `models/severity_classifier.joblib`  
**Dataset:** `datasets/severity_dataset.csv` (130+ muestras, 4 clases)  

Proceso:
1. Construye texto de features: `"{descripción} TIPO:{tipo} AFECTADOS:{n}"`.
2. Vectoriza con TF-IDF (bi-gramas, max 5000 features).
3. Clasifica con Random Forest → probabilidades por clase.
4. Retorna: `{severity: 4, confidence: 0.92, reasoning: "..."}`
5. Fallback: reglas heurísticas si el modelo no está entrenado.

### 9.2.2 Predicción de demanda (hotspots)

**Entrada:** Hora del día, día de la semana, historial de incidentes.  
**Salida:** Zonas de alta probabilidad de incidentes.  
**Algoritmo:** Random Forest entrenado con datos históricos.  
**Modelo:** Serializado en `models/demand_predictor.joblib` + `demand_scaler.joblib`

Features: hora, día semana, mes, zona geográfica.  
Output: Mapa de calor con probabilidades por zona.

### 9.2.3 Predicción de ETA

**Entrada:** Vehículo ID, incidente ID, condiciones actuales.  
**Salida:** ETA en minutos con intervalo de confianza.  
**Algoritmo:** Gradient Boosting Regressor.

Features: distancia, velocidad actual, hora del día, severidad, tráfico, clima.  
Multiplicadores: tráfico (0.8×–2.0×), lluvia (1.2×), noche (0.9×).

### 9.2.4 Detección de anomalías

**Tres módulos:**
- **Vehículos:** Detecta comportamientos inusuales (velocidad anormal, consumo excesivo, patrones de ruta).
- **Incidentes:** Detecta patrones inusuales (concentración geográfica, frecuencia anormal).
- **Salud del sistema:** Monitoriza métricas globales.

**Algoritmo:** Isolation Forest para detección estadística + reglas heurísticas.

### 9.2.5 Mantenimiento predictivo

**Entrada:** Estado actual del vehículo (km, horas, combustible, trust_score).  
**Salida:** Fecha estimada de mantenimiento, componentes en riesgo.  
**Algoritmo:** Reglas heurísticas basadas en umbrales:
- Km > 50.000 → revisión general
- Horas > 5.000 → mantenimiento preventivo  
- Fuel < 25% → repostaje automático
- Trust score < 60 → inspección

### 9.2.6 Visión por computador

**Entrada:** Imagen (bytes) de la escena de emergencia.  
**Salida:** Análisis de la escena + evaluación de seguridad.  
**Algoritmo:** Pillow (extracción de features visuales) + TF-IDF + LinearSVC (clasificación de escena).  
**Modelo:** `models/vision_scene_model.joblib`  
**Dataset:** `datasets/vision_scenes_dataset.csv` (56 muestras, 7 tipos de escena)  

Features visuales extraídas con Pillow:
- Brillo medio, ratio rojo/azul/oscuridad
- Varianza de píxeles (indicador de caos visual)
- Resolución de imagen

7 tipos de escena: TRAFFIC_ACCIDENT, FIRE_SCENE, MEDICAL_EMERGENCY, STRUCTURAL_COLLAPSE, FLOOD_SCENE, HAZMAT_SCENE, SAFE_SCENE.

Dos modos:
- `analyze-incident`: Identifica tipo de incidente, severidad visible, número de víctimas.
- `analyze-scene-safety`: Evalúa riesgos para el equipo de emergencia.

### 9.2.7 Asistente conversacional

**Motor:** TF-IDF + LogisticRegression (clasificador de intents).  
**Modelo:** `models/chat_intent_model.joblib`  
**Dataset:** `datasets/chat_intents_dataset.csv` (145+ muestras, 7 intents)  

**Funcionamiento:**
1. Clasifica el intent del mensaje del usuario (fleet_status, incidents_summary, hospital_capacity, create_incident, analytics, hotspots, greeting, help).
2. Genera respuesta templateática adaptada al intent detectado.
3. Extrae coordenadas de mensajes cuando se detecta intent `create_incident`.
4. Retorna: `{response, intent, confidence, suggested_actions}`

**Funcionalidades:**
- Responde preguntas sobre el estado operativo actual.
- Proporciona recomendaciones basadas en el contexto.
- Historial de chat persistente por sesión.

### 9.2.8 Integración de tráfico

**Entrada:** Coordenadas de origen/destino, hora.  
**Salida:** Ruta optimizada con estimación de tráfico.  
**Algoritmo:** Mapeo hora-del-día a nivel de congestión + ajuste de ETA.

Niveles de tráfico:
- 0:00–6:00: Bajo (×0.8)
- 7:00–9:00: Pico mañana (×1.5)
- 9:00–17:00: Medio (×1.2)
- 17:00–20:00: Pico tarde (×1.5)
- 20:00–24:00: Bajo (×0.9)

### 9.2.9 Sistema de recomendaciones

**Entrada:** Incidente actual, historial del operador.  
**Salida:** Recomendaciones personalizadas.  
**Algoritmo:** Aprendizaje del perfil del operador (acceptance rate, override patterns).

### 9.2.10 Asignación inteligente

**Vehículo:** Scoring multi-criterio:
- Distancia al incidente (40%)
- Nivel de fuel (15%)
- Trust score del vehículo (15%)
- Subtipo adecuado para severidad (20%)
- Estado de disponibilidad (10%)

**Hospital:** Scoring multi-criterio:
- Distancia al incidente (40%)
- Especialidad coincidente (30%)
- Capacidad disponible (20%)
- Nivel de emergencia (10%)

## 9.3 Endpoints de IA (22 endpoints)

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/api/ai/status` | Estado de todos los módulos IA |
| `GET` | `/api/ai/insights/dashboard` | Dashboard con métricas consolidadas |
| `POST` | `/api/ai/severity/classify` | Clasificar severidad de texto |
| `GET` | `/api/ai/demand/hotspots` | Zonas de alta demanda predichas |
| `POST` | `/api/ai/demand/train` | Entrenar predictor de demanda |
| `GET` | `/api/ai/eta/predict/{v}/{i}` | ETA vehículo→incidente |
| `POST` | `/api/ai/eta/train` | Entrenar predictor ETA |
| `GET` | `/api/ai/anomalies/vehicles` | Anomalías en vehículos |
| `GET` | `/api/ai/anomalies/incidents` | Anomalías en incidentes |
| `GET` | `/api/ai/anomalies/system-health` | Salud del sistema |
| `POST` | `/api/ai/anomalies/train` | Entrenar detector anomalías |
| `GET` | `/api/ai/maintenance/predict/{v}` | Predicción mantenimiento |
| `GET` | `/api/ai/maintenance/fleet-schedule` | Schedule de mantenimiento |
| `POST` | `/api/ai/vision/analyze-incident` | Analizar imagen de incidente |
| `POST` | `/api/ai/vision/analyze-scene-safety` | Seguridad de escena |
| `POST` | `/api/ai/chat` | Mensaje al asistente IA |
| `POST` | `/api/ai/chat/clear` | Limpiar historial de chat |
| `GET` | `/api/ai/traffic/route` | Ruta optimizada por tráfico |
| `GET` | `/api/ai/recommendations/personalized/{i}` | Recomendaciones por incidente |
| `GET` | `/api/ai/recommendations/profile` | Perfil del operador |
| `GET` | `/api/ai/datasets/stats` | Estadísticas de datasets de reentrenamiento |
| `POST` | `/api/ai/retrain` | Re-entrenar todos los modelos IA |

## 9.4 Entrenamiento de modelos

### Script unificado

```bash
cd backend
python train_all_models.py
```

Entrena **6 modelos** en secuencia:

| Modelo | Algoritmo | Dataset | Output |
|---|---|---|---|
| Severity Classifier | TF-IDF + RandomForest (200 est.) | `datasets/severity_dataset.csv` | `models/severity_classifier.joblib` |
| Chat Intent | TF-IDF + LogisticRegression (C=5) | `datasets/chat_intents_dataset.csv` | `models/chat_intent_model.joblib` |
| Vision Scene | TF-IDF + LinearSVC | `datasets/vision_scenes_dataset.csv` | `models/vision_scene_model.joblib` |
| Demand Predictor | RandomForestRegressor (150 est.) | Sintético (800 muestras Madrid) | `models/demand_predictor.joblib` |
| ETA Predictor | GradientBoostingRegressor (200 est.) | Sintético (500 muestras) | `models/eta_predictor.joblib` |
| Anomaly Detector | IsolationForest (150 est.) | Sintético (vehículos + incidentes) | `models/anomaly_detector.joblib` |

### Re-entrenamiento vía API

```bash
curl -X POST http://localhost:5001/api/ai/retrain \
  -H "Authorization: Bearer <ADMIN_TOKEN>"
```

## 9.5 Anonimización y Aprendizaje Continuo (RGPD/LOPD-GDD)

### 9.5.1 Pipeline de datos

```
┌─────────────────┐    ┌──────────────────┐    ┌───────────────┐    ┌──────────────┐
│ Dato operativo  │───►│  Anonimizador    │───►│ Dataset CSV   │───►│ Reentrenar   │
│ (incidente,     │    │  (RGPD)          │    │ (append       │    │ modelos      │
│  chat, imagen)  │    │                  │    │  thread-safe) │    │              │
└─────────────────┘    └──────────────────┘    └───────────────┘    └──────────────┘
```

### 9.5.2 Capas de anonimización

| Capa | Técnica | Campos afectados | Ejemplo |
|---|---|---|---|
| **Supresión** | Eliminación total | nombre, DNI, teléfono, email, IP, user_agent | `patient_name` → eliminado |
| **Generalización** | Reducción de precisión | coordenadas, edad, dirección, fechas | `lat 40.4168` → `40.42`; `edad 42` → `ADULTO_30-44` |
| **Perturbación** | Ruido gaussiano ±5% | constantes vitales | `FC 80` → `78`; `TAS 120` → `122` |
| **Scrubbing** | 18 patrones regex | texto libre (descripciones, notas) | `"paciente Juan Pérez, DNI 12345678A"` → `"[NOMBRE_ANON], [DNI_ANON]"` |

### 9.5.3 Patrones PII detectados

| Patrón | Regex | Reemplazo |
|---|---|---|
| DNI español | `\b[0-9]{8}[A-Za-z]\b` | `[DNI_ANON]` |
| NIE extranjero | `\b[XYZ][0-9]{7}[A-Za-z]\b` | `[NIE_ANON]` |
| Teléfono español | `(?:\+34)?[679]\d{2}.\d{3}.\d{3}` | `[TEL_ANON]` |
| Email | `\b[...]+@[...]+\.[...]+\b` | `[EMAIL_ANON]` |
| Nombres propios | `(?:paciente\|sr\|sra\|don\|doña)\s+[A-Z]...` | `[NOMBRE_ANON]` |
| Direcciones | `(?:Calle\|Avenida\|Plaza)\s+...` | `[DIR_ANON]` |
| Matrículas | `\b\d{4}\s?[A-Z]{3}\b` | `[MATR_ANON]` |
| NSS | `\b\d{2}/?\d{8,10}/?\d{2}\b` | `[NSS_ANON]` |
| Tarjeta sanitaria | `\b[A-Z]{4}\d{10,14}\b` | `[CIP_ANON]` |

### 9.5.4 Archivos

| Archivo | Función |
|---|---|
| `app/core/anonymizer.py` | Motor de anonimización RGPD (220 líneas) |
| `app/core/data_collector.py` | Recolector thread-safe con append a CSV |

### 9.5.5 Puntos de integración

| Evento | Endpoint | Dataset destino |
|---|---|---|
| Creación de incidente | `POST /events/incidents` | `severity_dataset.csv` |
| Mensaje de chat | `POST /api/ai/chat` | `chat_intents_dataset.csv` (si confianza ≥ 0.7) |
| Análisis de imagen | `POST /api/ai/vision/analyze-incident` | `vision_scenes_dataset.csv` |

---

# 10. Sistema de Ciberseguridad

## 10.1 Arquitectura de seguridad

```
┌─────────────────────────────────────────────┐
│           CAPA DE SEGURIDAD                 │
├─────────────────────────────────────────────┤
│  SecurityHeadersMiddleware                  │
│  ├─ X-Frame-Options: DENY                  │
│  ├─ X-Content-Type-Options: nosniff         │
│  ├─ HSTS: max-age=31536000                  │
│  └─ CSP: default-src 'self'                 │
├─────────────────────────────────────────────┤
│  SecurityMiddleware                         │
│  ├─ Rate Limiting (100 req/60s general)     │
│  ├─ Brute-Force Detection (5 intentos)      │
│  ├─ Input Scanning (SQL/XSS/Path Traversal) │
│  └─ Session Management                     │
├─────────────────────────────────────────────┤
│  JWT Authentication                         │
│  ├─ HS256 signing                           │
│  ├─ Token expiration: 30 min                │
│  └─ Role-based claims                      │
├─────────────────────────────────────────────┤
│  RBAC: ADMIN / OPERATOR / DOCTOR / VIEWER   │
├─────────────────────────────────────────────┤
│  Password Policy                            │
│  ├─ Mínimo 8 caracteres                    │
│  ├─ Requiere mayúscula + minúscula + dígito│
│  └─ Entropía mínima calculada              │
├─────────────────────────────────────────────┤
│  Blockchain Audit Trail (inmutable)         │
└─────────────────────────────────────────────┘
```

## 10.2 Módulos de protección

| Módulo | Descripción | Estado |
|---|---|---|
| Rate Limiting | Límite de peticiones por IP/endpoint | Activo |
| Brute-Force Detection | Bloqueo tras intentos fallidos de login | Activo |
| Input Sanitization | Detección de SQL injection, XSS, path traversal | Activo |
| Security Headers | HSTS, CSP, X-Frame-Options, etc. | Activo |
| CSRF Protection | Tokens de un solo uso para operaciones sensibles | Activo |
| Session Management | Tracking de sesiones JWT activas | Activo |
| IP Blocking | Bloqueo/desbloqueo manual de IPs | Activo |
| Password Policy | Validación de fortaleza de contraseñas | Activo |
| JWT Encryption | HS256 con clave configurable | Activo |
| Audit Blockchain | Registro inmutable de acciones | Activo |

## 10.3 Rate Limits configurados

| Endpoint | Máximo | Ventana |
|---|---|---|
| Login (`/api/auth/login`) | 5 | 60 segundos |
| General (todas las rutas) | 100 | 60 segundos |
| Brute-force lockout | 5 intentos fallidos | 10 minutos |

## 10.4 Escaneo de inputs

Patrones detectados:
- **SQL Injection:** `SELECT`, `INSERT`, `UPDATE`, `DELETE`, `DROP`, `UNION`, `OR 1=1`, `--`, `/*`, `*/`, `xp_`, `;`
- **XSS:** `<script>`, `javascript:`, `onerror=`, `onload=`, `eval(`, `document.cookie`, `<iframe`
- **Path Traversal:** `../`, `..\\`, `/etc/passwd`, `/etc/shadow`, `cmd.exe`, `%2e%2e`

## 10.5 Panel de ciberseguridad (Frontend)

5 pestañas:

| Pestaña | Contenido |
|---|---|
| Resumen | 6 KPIs + 8 protecciones activas + eventos recientes |
| Eventos | Tabla filtrable por severidad (CRITICAL/HIGH/MEDIUM/LOW/INFO) |
| Sesiones | Sesiones JWT activas con IP, usuario, fecha |
| Firewall | IPs bloqueadas + formulario de bloqueo manual |
| Herramientas | Escáner de amenazas + verificador de contraseñas + config |

## 10.6 Endpoints de seguridad (9 endpoints)

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/api/security/dashboard` | Panel principal (stats + protecciones + config) |
| `GET` | `/api/security/events` | Eventos de seguridad (filtro por severidad) |
| `GET` | `/api/security/sessions` | Sesiones JWT activas |
| `GET` | `/api/security/blocked-ips` | IPs bloqueadas con motivo y fecha |
| `POST` | `/api/security/block-ip` | Bloquear IP manualmente |
| `DELETE` | `/api/security/block-ip/{ip}` | Desbloquear IP |
| `GET` | `/api/security/csrf-token` | Obtener token CSRF |
| `POST` | `/api/security/scan-input` | Escanear texto para amenazas |
| `POST` | `/api/security/check-password` | Verificar fortaleza de contraseña |

---

# 11. Blockchain y Auditoría Inmutable

## 11.1 Arquitectura

```
Acción del usuario
    │
    ▼
AuditLog (hash SHA-256)
    │
    ▼
Merkle Batch (N registros → 1 raíz)
    │
    ▼
BSV Blockchain (tx_id inmutable)
    │
    ▼
Verificación: proof Merkle / tx lookup
```

## 11.2 Flujo de notarización

1. **Evento**: Cualquier acción del sistema (login, asignación, resolución) genera un `AuditLog`.
2. **Hash**: Cada registro se hashea con SHA-256 (`blockchain_hash`).
3. **Batch**: Los registros pendientes se agrupan en un `MerkleBatch` (N hojas → 1 raíz).
4. **Broadcast**: La raíz Merkle se envía a la blockchain BSV vía WhatsOnChain / ARC API.
5. **Verificación**: Se puede verificar cualquier registro individual recalculando su proof Merkle hasta la raíz, y comparando con el tx_id on-chain.

## 11.3 Módulos blockchain

| Módulo | Función |
|---|---|
| `merkle.py` | Implementación de árbol Merkle (build, get_proof, verify_proof) |
| `integrity.py` | Cálculo de hash SHA-256 y verificación de integridad |
| `batch_notarizer.py` | Agrupación de registros en lotes y creación de Merkle roots |
| `notarizer.py` | Notarización individual de registros |
| `adapter.py` | Adaptador BSV: creación de transacciones, broadcast |
| `generate_wallet.py` | Generación de claves BSV |

## 11.4 Endpoints blockchain (12 endpoints)

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/api/blockchain/verify/{hash}` | Verificar hash (público) |
| `GET` | `/api/blockchain/verify-by-id/{id}` | Verificar por audit_id |
| `GET` | `/api/blockchain/status` | Estado del sistema blockchain |
| `GET` | `/api/blockchain/records` | Registros recientes |
| `POST` | `/api/blockchain/retry/{id}` | Reintentar notarización |
| `GET` | `/api/blockchain/merkle/pending` | Registros pendientes |
| `POST` | `/api/blockchain/merkle/batch` | Crear lote Merkle |
| `POST` | `/api/blockchain/merkle/broadcast/{id}` | Difundir a BSV |
| `POST` | `/api/blockchain/merkle/batch-and-broadcast` | Batch + broadcast |
| `GET` | `/api/blockchain/merkle/proof/{id}` | Proof Merkle de un registro |
| `GET` | `/api/blockchain/merkle/verify/{id}` | Verificar proof Merkle |
| `GET` | `/api/blockchain/merkle/batches` | Listar batches |

---

# 12. Frontend — React 19

## 12.1 Estructura

```
frontend/src/
├── App.jsx              # Router + AuthProvider + Toaster
├── main.jsx             # Entry point (React 19 createRoot)
├── App.css              # Estilos globales
├── index.css            # Reset CSS + variables
├── components/
│   ├── Layout.jsx       # Shell: sidebar + navbar + city filter + dark mode
│   ├── ChatWidget.jsx   # Chat operativo multi-canal
│   ├── ChatWidget.css
│   └── mapIcons.js      # Iconos SVG para Leaflet
├── context/
│   └── AuthContext.jsx  # JWT provider + login/logout + role checking
├── pages/               # 15 páginas
│   ├── Dashboard.jsx    # (2245 líneas) Mapa principal
│   ├── IncidentList.jsx
│   ├── CreateIncident.jsx
│   ├── Analytics.jsx
│   ├── KPIs.jsx
│   ├── AIInsights.jsx
│   ├── AuditLog.jsx
│   ├── CrewManagement.jsx
│   ├── HospitalDashboard.jsx
│   ├── ParamedicView.jsx
│   ├── PatientTracking.jsx
│   ├── SecurityDashboard.jsx
│   ├── DriverMobile.jsx
│   ├── DriverLogin.jsx
│   └── Login.jsx
├── styles/              # 14 archivos CSS
└── utils/
    └── statusLabels.js  # Labels + colores para estados
```

## 12.2 Páginas del sistema

### Dashboard (`/`) — 2245 líneas
- Mapa Leaflet con capas: vehículos, incidentes, hospitales, gasolineras, DEAs, heatmap, agencias, GIS
- Panel de flota con KPIs en tiempo real
- Panel de incidentes activos con sugerencias IA
- Formulario de asignación manual con override
- Modal de detalle de incidente con timeline
- Botón de resolución para operadores/admin
- Widget de clima con multiplicador de ETA
- Filtro por ciudad en la barra de navegación

### Lista de Incidentes (`/incidents`)
- Tabla paginada con filtros: estado, severidad, ciudad, rango de fechas
- Columnas: ID, tipo, severidad, estado, ubicación, vehículo asignado, hospital, fecha
- Click en fila → detalle del incidente

### Crear Incidente (`/create-incident`) — Solo ADMIN
- Formulario con 16 tipos de incidentes
- Clasificación automática de severidad por IA
- Geolocalización por click en mapa
- Selector de severidad manual (override)
- Contador de afectados

### Analytics (`/analytics`)
- 4 gráficos Recharts:
  1. Incidentes por tipo (barras)
  2. Distribución por severidad (pie)
  3. Distribución horaria (líneas)
  4. Tiempo de respuesta por severidad (barras)
- Exportación a CSV y PDF (jsPDF + html2canvas)
- Filtro por ciudad

### KPIs (`/kpis`)
- Tiempo medio de respuesta (global y por severidad)
- Compliance SAMUR: <8 min y <15 min
- Utilización de flota (%)
- Tabla por vehículo: casos, tiempo medio, combustible, trust score
- Snapshot periódico guardado en BD
- Filtro por ciudad

### AI Insights (`/ai-insights`) — ADMIN, OPERATOR
- Dashboard de IA: hotspots, anomalías, mantenimiento, severidad
- Chat conversacional con intent classifier local
- Historial de chat persistente por sesión
- Entrenamiento de modelos desde la interfaz

### Auditoría (`/audit-log`) — Solo ADMIN
- Log de auditoría paginado con filtros
- Exportación a CSV
- Verificación de integridad blockchain por hash
- Indicador de estado: verificado/pendiente/fallido

### Tripulaciones (`/crew`) — ADMIN, OPERATOR
- Tab Personal: grid de cards con avatar, rol, certificaciones, turno activo
- Tab Turnos: tabla con filtro por tipo de turno (Día/Noche/24h)
- Finalización de turnos activos
- Seed de tripulación de ejemplo (12 miembros + turnos adaptativos)
- Búsqueda por nombre y filtro por rol

### Hospitales (`/hospital-dashboard`) — ADMIN, OPERATOR
- Cards por hospital: nombre, capacidad, carga actual, especialidades, nivel
- Barra de progreso de ocupación
- Ambulancias en camino (ASSIGNED + EN_ROUTE)
- Seed de hospitales de ejemplo

### Paramédico (`/paramedic`) — ADMIN, OPERATOR, DOCTOR
- Formulario ePCR completo: datos del paciente, constantes vitales, MPDS, tratamiento
- Protocolos pre-arrival por tipo de incidente
- Vista optimizada para uso en campo

### Patient Tracking (`/patient-tracking`) — ADMIN, OPERATOR, DOCTOR
- Pipeline visual de fases: ON_SCENE → IN_AMBULANCE → AT_HOSPITAL_ER → ADMITTED → DISCHARGED
- Botón "Avanzar fase" por paciente
- Toggle "Incluir altas" / "Solo activos"
- Seed de pacientes de ejemplo

### Seguridad (`/security`) — Solo ADMIN
- 5 pestañas: Resumen, Eventos, Sesiones, Firewall, Herramientas
- 6 KPIs + 8 indicadores de protección
- Escáner de amenazas + verificador de contraseñas
- Gestión de IPs bloqueadas

### App Conductor (`/driver`)
- Interfaz móvil optimizada para conductores de ambulancia
- Login por ID de vehículo
- Estado actual del vehículo + incidente asignado
- Botón "Volver al Panel" para ADMIN/OPERATOR

### Login (`/login`)
- Formulario de autenticación con JWT
- Dark mode independiente
- Credenciales por defecto visibles en desarrollo

## 12.3 Características transversales del frontend

| Característica | Implementación |
|---|---|
| **Dark Mode** | `data-theme="dark"` en `<html>`, persiste en localStorage |
| **City Filter** | Selector global en Layout, filtra Dashboard, Analytics, KPIs, Incidents |
| **RBAC Frontend** | `<RoleRoute roles={[...]}>`  + `canAccess()` para nav items |
| **Toast** | react-hot-toast para todas las notificaciones |
| **WebSocket** | `/ws/live` conectado desde Dashboard para datos en tiempo real |
| **Polling fallback** | `/api/live` como alternativa a WebSocket |
| **CSS Variables** | Temas claro/oscuro via custom properties |
| **Responsive** | Grid adaptativo en todas las páginas |
| **PWA** | Service Worker + manifest.json + iconos 192/512px, instalable en móvil |
| **ErrorBoundary** | Captura errores de renderizado con fallback UI amigable |
| **Lazy Loading** | `React.lazy()` + `Suspense` para todas las páginas (code splitting) |
| **Loading Skeletons** | Placeholders animados mientras cargan datos |
| **Browser Notifications** | Notificaciones push nativas para incidentes nuevos |
| **Vite Chunk Splitting** | Bundles separados: vendor-react, vendor-charts, vendor-map, vendor-utils |
| **Open Graph / SEO** | Meta tags OG + Twitter Card para compartir en redes sociales |

---

# 13. Sistema de Routing (OSRM)

## 13.1 Integración

KAIROS CDS utiliza OSRM (Open Source Routing Machine) para calcular rutas reales sobre la red viaria. La integración se realiza a través del módulo `core/routing.py`.

## 13.2 Flujo de routing

```
TwinEngine detecta incidente sin ruta
    │
    ▼
routing.get_route(origin, waypoint?, destination)
    │
    ├─ Intenta OSRM externo (router.project-osrm.org)
    │   └─ GET /route/v1/driving/{coords}?overview=full&geometries=geojson
    │
    ├─ Si OSRM falla → fallback sintético
    │   └─ Interpolación lineal con jitter (simula calles)
    │
    └─ Resultado:
        ├─ geometry: [[lon, lat], ...] (GeoJSON)
        ├─ distance_km: distancia total
        ├─ duration_minutes: tiempo estimado
        ├─ incident_waypoint_idx: índice del punto del incidente en la ruta
        └─ hospital_id: hospital de destino
```

## 13.3 Ruta A→B→C

Para un incidente con hospital asignado, la ruta se calcula como:
- A = Posición actual del vehículo
- B = Ubicación del incidente
- C = Hospital de destino

Los tres puntos se envían a OSRM en una sola consulta para obtener una ruta optimizada A→B→C. El `incident_waypoint_idx` indica en qué punto de la geometría se encuentra el incidente (B), para saber cuándo cambiar de fase `TO_INCIDENT` → `TO_HOSPITAL`.

---

# 14. Gestión de Incidentes

## 14.1 Tipos de incidentes (16 tipos)

| Tipo | Peso (generación) | Severidad |
|---|---|---|
| TRAUMA | 20 | 2–5 |
| CARDIO | 18 | 3–5 |
| RESPIRATORY | 14 | 2–4 |
| NEUROLOGICAL | 10 | 3–5 |
| FALL | 8 | 1–4 |
| GENERAL | 8 | 1–3 |
| PEDIATRIC | 7 | 2–5 |
| METABOLIC | 6 | 2–4 |
| POISONING | 6 | 2–4 |
| BURN | 5 | 2–5 |
| PSYCHIATRIC | 5 | 1–3 |
| ALLERGIC | 5 | 2–5 |
| OBSTETRIC | 4 | 3–5 |
| VIOLENCE | 4 | 2–5 |
| INTOXICATION | 4 | 1–4 |
| DROWNING | 2 | 4–5 |

## 14.2 Ciclo de vida del incidente

```
OPEN ──► ASSIGNED ──► EN_ROUTE ──► ARRIVED ──► RESOLVED ──► CLOSED
                                                    │
                                                    └─► CANCELLED
```

| Estado | Descripción | Color |
|---|---|---|
| OPEN | Incidente reportado, sin asignar | Amarillo (#f59e0b) |
| ASSIGNED | Vehículo y hospital asignados | Azul (#3b82f6) |
| EN_ROUTE | Vehículo en camino | Cyan (#0ea5e9) |
| ON_SCENE | Vehículo en la escena | Amarillo |
| RESOLVED | Paciente entregado, vehículo liberado | Verde (#10b981) |
| CLOSED | Caso cerrado administrativamente | Gris (#6b7280) |
| CANCELLED | Incidente cancelado | Gris |

## 14.3 Resolución de incidentes

Dos vías de resolución:

**Automática (TwinEngine):**
1. Vehículo llega al hospital (route_progress ≥ 0.95 o distancia < umbral)
2. Incidente → RESOLVED
3. ePCR creado automáticamente con datos del incidente
4. PatientTracking creado en fase AT_HOSPITAL_ER
5. Hospital load decrementado
6. Vehículo liberado → IDLE

**Manual (Operador):**
1. Operador pulsa "Marcar como Resuelto" en el modal de incidente
2. `POST /api/assignments/resolve/{incident_id}`
3. Si no existe ePCR, se crea automáticamente
4. PatientTracking creado/actualizado a AT_HOSPITAL_ER
5. Hospital load decrementado
6. Vehículo liberado → IDLE
7. Auditoría registrada con acción RESOLVE

---

# 15. Gestión de Flota

## 15.1 Tipos de vehículos (sistema español)

| Subtipo | Nombre completo | Tripulación | Capacidad | Consumo |
|---|---|---|---|---|
| SVB | Soporte Vital Básico | TES + Conductor | Básica (DEA, SVB) | 18 L/100km |
| SVA | Soporte Vital Avanzado | Médico + Enfermero + Conductor | Completa (UCI móvil) | 22 L/100km |
| VIR | Vehículo de Intervención Rápida | Médico | Respuesta rápida | 12 L/100km |
| VAMM | Vehículo Asistencia Múltiple | Médico + Enfermero + TES | Múltiples víctimas | 28 L/100km |
| SAMU | Servicio Atención Médica Urgente | Médico + Enfermero | Urgente | 14 L/100km |

## 15.2 Estados del vehículo

| Estado | Descripción |
|---|---|
| IDLE | Disponible en base |
| EN_ROUTE | En camino al incidente o hospital |
| ON_SCENE | En la escena del incidente |
| RETURNING | Retornando a base |
| MAINTENANCE | En mantenimiento |
| REFUELING | Repostando combustible |

## 15.3 Consumo de combustible

El sistema simula consumo realista de combustible:
- **En ruta:** Según L/100km del subtipo × distancia recorrida
- **En idle:** 1.5 L/hora
- **Repostaje automático:** Cuando fuel < 25% y vehículo IDLE sin incidente, se dirige a gasolinera más cercana
- **Duración repostaje:** 16 ticks (~8 segundos reales, ~5 minutos simulados)

## 15.4 Flota seed (8 vehículos)

| ID | Subtipo | Ubicación inicial |
|---|---|---|
| SVA-001 | SVA | Madrid centro |
| SVA-002 | SVA | Madrid norte |
| SVB-001 | SVB | Madrid sur |
| SVB-002 | SVB | Madrid este |
| SVB-003 | SVB | Madrid oeste |
| VIR-001 | VIR | Madrid centro |
| VAMM-001 | VAMM | Madrid centro |
| SAMU-001 | SAMU | Madrid centro |

---

# 16. Gestión de Tripulaciones y Turnos

## 16.1 Roles de tripulación

| Rol | Certificaciones | Color UI |
|---|---|---|
| MEDICO | ACLS, ATLS, PHTLS, PEDIATRIC, NEONATAL | Rojo (#ef4444) |
| ENFERMERO | ACLS, PHTLS, OBSTETRICIA | Azul (#3b82f6) |
| TES | BLS, SVB_DEA | Verde (#22c55e) |
| CONDUCTOR | BTP, BLS | Amarillo (#f59e0b) |

## 16.2 Tipos de turno

| Tipo | Horario | Backend key |
|---|---|---|
| Día | 8:00 – 20:00 | DIA |
| Noche | 20:00 – 8:00 | NOCHE |
| Guardia 24h | 24 horas continuas | GUARDIA_24H |

El seed de turnos detecta automáticamente la hora actual y asigna el tipo correspondiente:
- 8:00–20:00 → DIA
- 20:00–8:00 → NOCHE

## 16.3 Ciclo de vida del turno

```
SCHEDULED ──► ACTIVE ──► COMPLETED
                 │
                 └──► CANCELLED
```

Los turnos pueden finalizarse manualmente desde el frontend (botón "Finalizar" en la tabla de turnos), lo que actualiza el estado a COMPLETED y registra la hora de finalización.

## 16.4 Asignación tripulación-vehículo

| Vehículo | Tripulación |
|---|---|
| SVA-001 | Médico + Enfermero + Conductor |
| SVA-002 | Médico + Enfermero + Conductor |
| SVB-001 | TES + Conductor |
| SVB-002 | TES + Conductor |
| SVB-003 | TES + Conductor |
| VIR-001 | Médico |
| VAMM-001 | Médico + Enfermero + TES |
| SAMU-001 | Médico + Enfermero |

## 16.5 Endpoints de tripulaciones (8 endpoints)

| Método | Endpoint | Descripción |
|---|---|---|
| `POST` | `/api/crews/seed` | Seed 12 crew members + turnos adaptativos |
| `GET` | `/api/crews/members` | Listar tripulación activa |
| `GET` | `/api/crews/members/{id}` | Detalle de miembro + turno activo |
| `GET` | `/api/crews/shifts` | Listar turnos (todos los estados) |
| `GET` | `/api/crews/vehicle/{id}` | Tripulación activa de un vehículo |
| `POST` | `/api/crews/members` | Crear nuevo miembro |
| `POST` | `/api/crews/shifts` | Crear nuevo turno |
| `POST` | `/api/crews/shifts/{id}/end` | Finalizar turno activo |

---

# 17. Atención al Paciente (ePCR)

## 17.1 Electronic Patient Care Report

El ePCR (Electronic Patient Care Report) es el registro clínico digital de la atención prestada a un paciente durante un incidente de emergencia.

### Datos capturados:

| Sección | Campos |
|---|---|
| **Identificación** | Nombre, edad, género, DNI |
| **Motivo de consulta** | Chief complaint, síntomas |
| **Historial** | Alergias, medicación habitual, antecedentes |
| **Constantes vitales** | FC, TA (sys/dia), FR, SpO2, Tª, Glasgow, dolor |
| **Triaje** | Código MPDS, determinante MPDS |
| **Tratamiento** | Tratamiento administrado, medicaciones, procedimientos |
| **Disposición** | Destino del paciente, hospital receptor |

## 17.2 Patient Tracking — Fases

```
ON_SCENE ──► IN_AMBULANCE ──► AT_HOSPITAL_ER ──► ADMITTED ──► DISCHARGED
```

| Fase | Descripción | Timestamp |
|---|---|---|
| ON_SCENE | Paciente atendido en el lugar | created_at |
| IN_AMBULANCE | Paciente en la ambulancia, en traslado | — |
| AT_HOSPITAL_ER | En urgencias del hospital | admission_time |
| ADMITTED | Ingresado en planta/UCI | — |
| DISCHARGED | Dado de alta | discharge_time |

### Disposiciones de alta:
- `HOME` — Alta a domicilio
- `ICU` — Ingreso en UCI
- `WARD` — Ingreso en planta
- `DECEASED` — Fallecimiento
- `AMA` — Alta voluntaria (Against Medical Advice)

## 17.3 Creación automática

Cuando un incidente se resuelve (manual o automático), si no existe un ePCR previo, el sistema crea automáticamente:
1. Un `PatientCareReport` con datos del incidente (tipo, descripción, hospital)
2. Un `PatientTracking` en fase `AT_HOSPITAL_ER` con timestamp de admisión

## 17.4 Protocolos MPDS pre-arrival

Disponibles para cada tipo de incidente. Proporcionan instrucciones al operador mientras la ambulancia está en camino.

## 17.5 Endpoints ePCR (9 endpoints)

| Método | Endpoint | Descripción |
|---|---|---|
| `POST` | `/api/epcr/create` | Crear ePCR para un incidente |
| `GET` | `/api/epcr/incident/{id}` | Obtener ePCR por incidente |
| `PUT` | `/api/epcr/{id}/vitals` | Actualizar constantes vitales |
| `GET` | `/api/epcr/mpds-protocols` | Protocolos MPDS |
| `GET` | `/api/epcr/tracking/{id}` | Tracking de un incidente |
| `PUT` | `/api/epcr/tracking/{id}/phase` | Avanzar fase del paciente |
| `GET` | `/api/epcr/all-tracking` | Todos los pacientes activos |
| `GET` | `/api/epcr/all-tracking-full` | Todos incluido altas |
| `POST` | `/api/epcr/seed-demo-patients` | Seed 10 pacientes demo |

---

# 18. Sistema Hospitalario

## 18.1 Modelo de hospital

Cada hospital tiene:
- **Capacidad fija**: número total de camas
- **Carga actual**: camas ocupadas (se incrementa al asignar, se decrementa al resolver)
- **Especialidades**: CARDIAC, TRAUMA, NEURO, BURN, PEDIATRIC, GENERAL
- **Nivel de emergencia**: 1 (básico), 2 (avanzado), 3 (referencia)

## 18.2 Algoritmo de asignación

La IA asigna el hospital óptimo basándose en:
1. **Distancia** (40%): Haversine al incidente
2. **Especialidad** (30%): ¿El hospital tiene la especialidad que coincide con el tipo de incidente?
3. **Capacidad** (20%): ¿Cuántas camas quedan libres?
4. **Nivel** (10%): ¿El nivel de emergencia del hospital es adecuado para la severidad?

## 18.3 Dashboard hospitalario

- Cards por hospital con barra de ocupación
- Indicador de ambulancias en camino (status ASSIGNED + EN_ROUTE)
- Especialidades como badges
- Auto-seed si no hay hospitales cargados

## 18.4 Hospitales seed (6 hospitales Madrid)

| ID | Nombre | Capacidad | Especialidades | Nivel |
|---|---|---|---|---|
| HOSP-001 | Hospital 12 de Octubre | 120 | CARDIAC, TRAUMA, NEURO | 3 |
| HOSP-002 | Hospital La Paz | 150 | CARDIAC, PEDIATRIC, NEURO | 3 |
| HOSP-003 | Hospital Gregorio Marañón | 100 | GENERAL, TRAUMA | 2 |
| HOSP-004 | Hospital Ramón y Cajal | 90 | CARDIAC, GENERAL | 2 |
| HOSP-005 | Hospital Clínico San Carlos | 110 | NEURO, BURN, GENERAL | 3 |
| HOSP-006 | Hospital Puerta de Hierro | 80 | TRAUMA, GENERAL | 2 |

---

# 19. KPIs y Analytics

## 19.1 KPIs operativos en tiempo real

| KPI | Descripción | Target |
|---|---|---|
| Tiempo medio de respuesta | Desde creación hasta asignación | < 8 min (SAMUR) |
| Compliance < 8 min | % de incidentes respondidos en < 8 min | > 85% |
| Compliance < 15 min | % de incidentes respondidos en < 15 min | > 95% |
| Vehículos disponibles | Vehículos IDLE / Total habilitados | > 40% |
| Utilización de flota | Vehículos en servicio / Total | Óptimo: 60-70% |
| Incidentes activos | Incidentes OPEN + ASSIGNED + EN_ROUTE | — |
| Tiempo medio resolución | Desde creación hasta resolución | — |

## 19.2 Analytics (4 gráficos)

1. **Incidentes por tipo**: Barras agrupadas por los 16 tipos
2. **Distribución por severidad**: Gráfico de tarta 1-5
3. **Distribución horaria**: Líneas mostrando incidentes por hora del día
4. **Tiempo de respuesta por severidad**: Barras comparando tiempos por nivel 1-5

## 19.3 Exportación

- **CSV**: Exportación directa desde Analytics y AuditLog
- **PDF**: Generado con jsPDF + html2canvas, incluye gráficos

## 19.4 Snapshots

`POST /api/kpis/snapshot` guarda el estado actual de KPIs en la base de datos para análisis temporal.

---

# 20. Monitorización (Prometheus + Alertmanager)

## 20.1 Métricas exportadas (`/metrics`)

| Métrica | Tipo | Labels | Descripción |
|---|---|---|---|
| `http_requests_total` | Counter | method, endpoint, status | Peticiones HTTP totales |
| `http_request_duration_seconds` | Histogram | method, endpoint | Duración de peticiones |
| `incidents_created_total` | Counter | — | Incidentes creados |
| `incidents_resolved_total` | Counter | — | Incidentes resueltos |
| `available_vehicles_count` | Gauge | — | Vehículos IDLE disponibles |
| `database_connections_active` | Gauge | — | Conexiones BD activas |

## 20.2 Reglas de alerta

| Alerta | Condición | Severidad |
|---|---|---|
| Alta latencia | p95 > 2s durante 5 min | Warning |
| Baja tasa resolución | < 1 resolución en 30 min | Warning |
| Bajo combustible | Vehículo con fuel < 15% | Warning |
| Tasa de errores HTTP | > 5% de errores 5xx en 5 min | Critical |

## 20.3 Configuración Prometheus

```yaml
scrape_configs:
  - job_name: 'kairos-backend'
    metrics_path: /metrics
    static_configs:
      - targets: ['host.docker.internal:5001']
    scrape_interval: 15s
```

---

# 21. Comunicación en Tiempo Real

## 21.1 WebSocket (`/ws/live`)

- Broadcast cada 2 segundos con el estado completo
- Payload: vehículos, incidentes, hospitales
- Autenticación por token JWT en query string
- Reconexión automática en el frontend

## 21.2 Polling fallback (`/api/live`)

- GET request con filtro opcional `?city=Madrid`
- Mismo payload que WebSocket
- Usado cuando WebSocket no está disponible

## 21.3 Chat operativo

Sistema de chat multi-canal para comunicación entre operadores:

| Canal | Propósito |
|---|---|
| general | Comunicación general |
| despacho | Coordinación de despacho |
| médico | Consultas médicas |

Endpoints:
- `GET /api/chat/channels` — Listar canales
- `GET /api/chat/messages?channel=general` — Obtener mensajes
- `POST /api/chat/messages` — Enviar mensaje

---

# 22. Sistema de Roles y Permisos (RBAC)

## 22.1 Matriz de permisos

| Funcionalidad | ADMIN | OPERATOR | DOCTOR | VIEWER |
|---|---|---|---|---|
| Dashboard (mapa) | ✅ | ✅ | ✅ | ✅ |
| Ver incidentes | ✅ | ✅ | ✅ | ✅ |
| Crear incidentes | ✅ | ❌ | ❌ | ❌ |
| Asignar vehículos | ✅ | ✅ | ❌ | ❌ |
| Resolver incidentes | ✅ | ✅ | ❌ | ❌ |
| Analytics / KPIs | ✅ | ✅ | ✅ | ✅ |
| AI Insights | ✅ | ✅ | ❌ | ❌ |
| Hospitales | ✅ | ✅ | ❌ | ❌ |
| ePCR / Pacientes | ✅ | ✅ | ✅ | ❌ |
| Tripulaciones | ✅ | ✅ | ❌ | ❌ |
| Auditoría | ✅ | ❌ | ❌ | ❌ |
| Ciberseguridad | ✅ | ❌ | ❌ | ❌ |
| Gestión usuarios | ✅ | ❌ | ❌ | ❌ |
| Blockchain | ✅ | ❌ | ❌ | ❌ |
| Simulación | ✅ | ✅ | ❌ | ❌ |
| App conductor | ✅ | ✅ | ✅ | ✅ |

## 22.2 Implementación técnica

### Backend
```python
# Proteger un endpoint por rol:
@router.get("/protected")
async def endpoint(user: User = Depends(require_role(["ADMIN", "OPERATOR"]))):
    ...
```

### Frontend
```jsx
// Proteger una ruta por rol:
<RoleRoute roles={["ADMIN", "OPERATOR"]}>
  <CrewManagement />
</RoleRoute>

// Ocultar elemento de navegación:
{canAccess(["ADMIN"]) && <Link to="/audit-log">Auditoría</Link>}
```

### JWT Token
```json
{
  "sub": "admin",
  "role": "ADMIN",
  "exp": 1740000000
}
```

## 22.3 Usuarios por defecto

| Usuario | Contraseña | Rol | Acceso |
|---|---|---|---|
| `admin` | `admin123` | ADMIN | Acceso total |
| `operator` | `operator123` | OPERATOR | Despacho y operaciones |
| `doctor` | `doctor123` | DOCTOR | Clínico |
| `viewer` | `viewer123` | VIEWER | Solo lectura |

Creados automáticamente con `POST /api/auth/init-admin`.

---

# 23. Simulación y Generación de Incidentes

## 23.1 Generador de incidentes

El módulo `incident_generator.py` crea incidentes realistas con:
- Tipo ponderado por frecuencia (TRAUMA: 20%, CARDIO: 18%, etc.)
- Severidad dentro del rango del tipo
- Ubicación real en Madrid (30 direcciones reales + jitter ±200m)
- Descripción realista según tipo
- Afectados según tipo y severidad

## 23.2 Modos de simulación

| Modo | Endpoint | Descripción |
|---|---|---|
| Auto-generate (start) | `POST /simulation/auto-generate/start` | Genera incidentes automáticamente cada N segundos |
| Auto-generate (stop) | `POST /simulation/auto-generate/stop` | Detiene la generación automática |
| Generate one | `POST /simulation/generate-one` | Genera un incidente individual |
| Speed control | `POST /simulation/speed` | Ajusta velocidad: 0.5×–20× |
| Reset | `POST /simulation/reset` | Resetea simulación |

## 23.3 Control de velocidad

El multiplicador de velocidad afecta:
- Velocidad de movimiento de vehículos
- Frecuencia de generación de incidentes
- Consumo de combustible

| Velocidad | Multiplicador | Equivalencia |
|---|---|---|
| Tiempo real | 1× | 1 seg = 1 seg |
| Acelerado | 5× | 1 seg = 5 seg |
| Máximo | 20× | 1 seg = 20 seg |
| Lento | 0.5× | 1 seg = 0.5 seg |

---

# 24. Gestión de Recursos

## 24.1 DEAs (Desfibriladores Externos Automáticos)

- Geolocalizados en el mapa
- Tipo: PUBLIC, PRIVATE, TRANSPORT
- Estado: disponible/no disponible
- Seed con ubicaciones reales de Madrid

## 24.2 First Responders (Voluntarios)

- Certificación: SVB_DEA, DESA, RCP
- Alertas por proximidad al incidente
- Histórico de respuestas

## 24.3 Gasolineras

- Marca, precios, tipos de combustible
- Horario (24h o horario limitado)
- Repostaje automático cuando vehículo IDLE + fuel < 25%
- Seed con estaciones reales de Madrid

## 24.4 Agencias multi-recurso

| Agencia | Recursos |
|---|---|
| Bomberos | Autobomba, escalera, HAZMAT |
| Policía Nacional | Patrulla, antidisturbios |
| Policía Municipal | Patrulla, tráfico |
| Protección Civil | Logística, evacuación |

## 24.5 Capas GIS

| Capa | Tipo de POI |
|---|---|
| Colegios | Zonas escolares |
| Residencias | Residencias de mayores |
| HAZMAT | Zonas de materiales peligrosos |
| Metro | Estaciones de metro |
| Policía | Comisarías |
| Bomberos | Parques de bomberos |

## 24.6 Meteorología

- Condiciones: CLEAR, RAIN, STORM, FOG, SNOW, ICE
- Multiplicador de ETA por condición
- Nivel de alerta: GREEN, YELLOW, ORANGE, RED
- Widget en el dashboard con información en tiempo real

## 24.7 SSM (System Status Management)

Zonas de cobertura predefinidas para gestión del estado del sistema.

---

# 25. Referencia Completa de API

## 25.1 Resumen por categoría (131 endpoints)

| Categoría | Prefijo | Endpoints |
|---|---|---|
| Health | `/health` | 1 |
| Root/Live | `/`, `/api/live`, `/api/cities`, `/metrics` | 5 |
| Auth | `/api/auth` | 4 |
| Fleet | `/fleet` | 4 |
| Events | `/events` | 4 |
| Assignments | `/api/assignments` | 3 |
| Analytics | `/api/analytics` | 3 |
| KPIs | `/api/kpis` | 4 |
| AI | `/api/ai` | 20 |
| Blockchain | `/api/blockchain` | 12 |
| Audit | `/api/audit` | 2 |
| Hospitals | `/api/hospitals` | 3 |
| Gas Stations | `/api/gas-stations` | 5 |
| Crews | `/api/crews` | 8 |
| ePCR | `/api/epcr` | 9 |
| MCI | `/api/mci` | 7 |
| Resources | `/api/resources` | 17 |
| Security | `/api/security` | 9 |
| Simulation | `/simulation` | 8 |
| Digital Twin | `/digital-twin` | 4 |
| Chat | `/api/chat` | 3 |
| Alerts | `/api/alerts` | 2 |
| WebSocket | `/ws/live` | 1 |
| **TOTAL** | | **~131** |

## 25.2 Documentación interactiva

- **Swagger UI**: http://localhost:5001/docs
- **ReDoc**: http://localhost:5001/redoc

Ambas documentaciones se generan automáticamente desde los schemas Pydantic y las docstrings de cada endpoint.

---

# 26. Testing y Calidad de Código

## 26.1 Tests backend (pytest) — 72+ tests

| Suite | Archivo | Qué cubre | Tests |
|---|---|---|---|
| Health | `test_health.py` | Endpoint `/health` | 1 |
| Auth | `test_auth.py` | Login, registro, roles, JWT, init-admin | 5 |
| Events | `test_events.py` | CRUD de incidentes, timeline, filtros | 6 |
| API | `test_api.py` | Fleet, seed, create incident, analytics, metrics | 10 |
| Live + Audit | `test_live_and_audit.py` | `/api/live`, audit logs | 4 |
| Crews | `test_crews.py` | Tripulaciones, turnos, seed | 4 |
| Operations | `test_operations.py` | Fleet vehicles, KPIs realtime | 5 |
| Security | `test_security.py` | Input scanning, password check, CSRF, headers | 8 |
| ePCR | `test_epcr.py` | Patient care reports, tracking, seed | 6 |
| Blockchain | `test_blockchain.py` | Merkle, notarización, integridad | 5 |
| Simulation | `test_simulation.py` | Auto-generación, configuración | 4 |

**Total: 11 suites, 72+ tests — todos pasando ✅**

### Configuración de tests

```ini
# pytest.ini
[pytest]
testpaths = tests
asyncio_mode = auto
```

### Fixtures (`conftest.py`)
- Base de datos SQLite in-memory para tests aislados
- Usuario admin y operator pre-creados con tokens JWT
- Rate limiting desactivado via `SECURITY_RATE_LIMIT_ENABLED=false`
- Override de `get_db` para inyección de BD de test
- Cleanup automático entre tests

## 26.2 Tests frontend (Vitest)

| Suite | Archivo | Qué cubre |
|---|---|---|
| App | `App.test.jsx` | Renderizado básico de la app |
| Login | `Login.test.jsx` | Flujo de autenticación |

### Configuración

```javascript
// vitest.config
test: {
  environment: 'jsdom',
  setupFiles: './src/test/setup.js'
}
```

## 26.3 Ejecución de tests

```bash
# Backend
cd backend
$env:PYTHONPATH = "."
python -m pytest tests/ -v

# Frontend
cd frontend
npm test
```

## 26.4 Linting

- ESLint configurado para React 19 con plugins:
  - `eslint-plugin-react-hooks`
  - `eslint-plugin-react-refresh`

---

# 27. Configuración y Variables de Entorno

## 27.1 Variables de entorno (`backend/.env`)

| Variable | Default | Descripción |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg2://twin:twin@localhost:55432/twin` | Conexión PostgreSQL |
| `REDIS_HOST` | `localhost` | Host Redis |
| `REDIS_PORT` | `6379` | Puerto Redis |
| `REDIS_DB` | `0` | Base de datos Redis |
| `SECRET_KEY` | Random 64 bytes | Clave de firma JWT |
| `ALGORITHM` | `HS256` | Algoritmo JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Expiración JWT (minutos) |
| `OPENAI_API_KEY` | — | Eliminado: todos los modelos IA son locales |
| `BSV_PRIVATE_KEY` | `""` | Clave privada BSV (opcional) |
| `BSV_NETWORK` | `main` | Red BSV: main/test |
| `ARC_URL` | `https://arc.gorillapool.io` | URL del nodo ARC BSV |
| `TICK_MS` | `500` | Intervalo del TwinEngine (ms) |
| `SECURITY_RATE_LIMIT_ENABLED` | `true` | Activar rate limiting |
| `SECURITY_BRUTE_FORCE_ENABLED` | `true` | Activar detección brute-force |
| `SECURITY_MAX_LOGIN_ATTEMPTS` | `5` | Intentos de login antes de lockout |
| `SECURITY_LOCKOUT_MINUTES` | `10` | Duración del lockout (minutos) |
| `CORS_ORIGINS` | `http://localhost:5173` | Orígenes CORS permitidos (separados por coma) |

## 27.2 Configuración del frontend

El frontend usa constantes hardcodeadas:
- `API = "http://127.0.0.1:5001"` — URL del backend
- Puerto dev: 5173 (Vite default)

---

# 28. Guía de Instalación

## 28.1 Prerrequisitos

| Software | Versión mínima |
|---|---|
| Python | 3.10 |
| Node.js | 18 |
| Docker Desktop | 24 |
| Git | 2.x |

## 28.2 Pasos de instalación

### 1. Clonar repositorio
```bash
git clone <repo-url> KAIROS_CDS && cd KAIROS_CDS
```

### 2. Iniciar infraestructura
```bash
docker compose up -d
```

### 3. Configurar backend
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate
pip install -r app/requirements.txt
```

### 4. Iniciar backend
```bash
cd backend
# Windows PowerShell:
$env:PYTHONPATH = "."
python -m uvicorn app.main:app --host 0.0.0.0 --port 5001 --reload
```

### 5. Configurar frontend
```bash
cd frontend
npm install
npm run dev  # → http://localhost:5173
```

### 6. Seed de datos iniciales
```bash
# 1. Crear usuarios
curl -X POST http://localhost:5001/api/auth/init-admin

# 2. Seed de ambulancias
curl -X POST http://localhost:5001/fleet/seed-ambulances

# 3. Seed de hospitales
curl -X POST http://localhost:5001/api/hospitals/seed

# 4. Seed de recursos
curl -X POST http://localhost:5001/api/resources/seed-all

# 5. Seed de gasolineras
curl -X POST http://localhost:5001/api/gas-stations/seed

# 6. Seed de tripulaciones
curl -X POST http://localhost:5001/api/crews/seed

# 7. (Opcional) Auto-generar incidentes
curl -X POST http://localhost:5001/simulation/auto-generate/start
```

### 7. Acceder al sistema
- **Frontend**: http://localhost:5173
- **API Docs**: http://localhost:5001/docs
- **Prometheus**: http://localhost:9090
- **Alertmanager**: http://localhost:9093

---

# 29. Rendimiento y Escalabilidad

## 29.1 Métricas de rendimiento

| Métrica | Valor típico |
|---|---|
| Tiempo de respuesta API (p50) | < 50ms |
| Tiempo de respuesta API (p95) | < 200ms |
| TwinEngine tick rate | 2 Hz (500ms) |
| WebSocket broadcast | Cada 2 segundos |
| Consultas BD por request | 1–3 queries |
| Memoria backend | ~100–200 MB |
| Memoria frontend | ~50–80 MB |

## 29.2 Estrategias de escalabilidad

| Aspecto | Estrategia actual | Escalabilidad futura |
|---|---|---|
| Base de datos | PostgreSQL single-node | Réplicas de lectura, particionamiento |
| Cache | Redis in-memory | Redis Cluster |
| Backend | Uvicorn single-process | Gunicorn multiworker, K8s pods |
| Frontend | Vite SPA | CDN + edge caching |
| Monitorización | Prometheus local | Thanos/Cortex federación |
| Blockchain | BSV single-node | Multi-node broadcast |

## 29.3 Límites conocidos

| Recurso | Límite actual |
|---|---|
| Vehículos simultáneos | ~50 (por rendimiento del TwinEngine) |
| Incidentes activos | ~200 antes de degradación |
| Eventos de seguridad en memoria | 10.000 (rotación FIFO) |
| Audit logs | Sin límite (PostgreSQL) |
| Sesiones activas | Sin límite (in-memory dict) |

---

# 30. Glosario

| Término | Definición |
|---|---|
| **BSV** | Bitcoin SV — blockchain utilizada para notarización de auditoría |
| **CDS** | Clinical Decision Support — soporte a decisiones clínicas |
| **CORS** | Cross-Origin Resource Sharing — política de seguridad del navegador |
| **CSRF** | Cross-Site Request Forgery — tipo de ataque web |
| **DEA** | Desfibrilador Externo Automático |
| **ePCR** | Electronic Patient Care Report — informe electrónico de atención al paciente |
| **ETA** | Estimated Time of Arrival — tiempo estimado de llegada |
| **GIS** | Geographic Information System — sistema de información geográfica |
| **HSTS** | HTTP Strict Transport Security — cabecera de seguridad |
| **JWT** | JSON Web Token — estándar de autenticación |
| **KPI** | Key Performance Indicator — indicador clave de rendimiento |
| **MCI** | Mass Casualty Incident — incidente con múltiples víctimas |
| **MPDS** | Medical Priority Dispatch System — sistema de priorización médica |
| **OSRM** | Open Source Routing Machine — motor de routing |
| **PostGIS** | Extensión espacial de PostgreSQL |
| **RBAC** | Role-Based Access Control — control de acceso basado en roles |
| **SAMUR** | Servicio de Asistencia Municipal de Urgencia y Rescate |
| **SAMU** | Servicio de Atención Médica Urgente |
| **SEM** | Servicios de Emergencias Médicas |
| **SSM** | System Status Management — gestión del estado del sistema |
| **START** | Simple Triage and Rapid Treatment — protocolo de triaje |
| **SVA** | Soporte Vital Avanzado — ambulancia con médico |
| **SVB** | Soporte Vital Básico — ambulancia con TES |
| **TES** | Técnico en Emergencias Sanitarias |
| **TwinEngine** | Motor de gemelo digital de KAIROS CDS |
| **VAMM** | Vehículo de Asistencia Múltiple a Múltiples víctimas |
| **VIR** | Vehículo de Intervención Rápida |
| **WS** | WebSocket — protocolo de comunicación bidireccional |
| **XSS** | Cross-Site Scripting — tipo de ataque web |

---

# Anexo A — Dependencias Python completas

```
fastapi==0.115.*
uvicorn[standard]
sqlalchemy
psycopg2-binary
geoalchemy2
pydantic
pydantic[email]
python-jose[cryptography]
passlib[bcrypt]
bcrypt
python-dotenv
python-multipart
prometheus-client
prometheus-fastapi-instrumentator
redis
hiredis
httpx
requests
pytest
pytest-asyncio
faker
# openai  ← Eliminado: 100% modelos locales
scikit-learn
pandas
numpy
joblib
Pillow
bsv-sdk
```

---

# Anexo B — Dependencias Frontend completas

### Producción
```json
{
  "date-fns": "^4.1.0",
  "html2canvas": "^1.4.1",
  "jspdf": "^3.0.1",
  "jspdf-autotable": "^5.0.2",
  "leaflet": "^1.9.4",
  "leaflet.heat": "^0.2.0",
  "leaflet.markercluster": "^1.5.3",
  "lucide-react": "^0.511.0",
  "react": "^19.1.0",
  "react-dom": "^19.1.0",
  "react-hot-toast": "^2.5.2",
  "react-router-dom": "^7.6.1",
  "recharts": "^2.15.3"
}
```

### Desarrollo
```json
{
  "@eslint/js": "^9.25.0",
  "@testing-library/jest-dom": "^6.6.3",
  "@testing-library/react": "^16.3.0",
  "@vitejs/plugin-react": "^4.4.1",
  "eslint": "^9.25.0",
  "eslint-plugin-react-hooks": "^5.2.0",
  "eslint-plugin-react-refresh": "^0.4.19",
  "globals": "^16.0.0",
  "jsdom": "^26.1.0",
  "vite": "^7.0.0",
  "vitest": "^3.1.4"
}
```

---

# Anexo C — Esquema de la base de datos (SQL)

```sql
-- Todas las tablas se crean automáticamente con SQLAlchemy
-- Base.metadata.create_all(engine) en el lifespan de FastAPI

-- Resumen de tablas:
-- vehicles           (id PK, type, subtype, status, lat, lon, speed, fuel, ...)
-- incidents          (id PK, type, severity, status, lat, lon, assigned_vehicle_id FK, ...)
-- users              (id PK serial, username UNIQUE, hashed_password, role)
-- audit_logs         (id PK serial, action, resource, blockchain_hash, ...)
-- merkle_batches     (id PK serial, merkle_root, tx_id, status)
-- hospitals          (id PK, name, capacity, current_load, specialties, level)
-- gas_stations       (id PK, brand, price, lat, lon, is_open)
-- crew_members       (id PK, name, role, certification, phone)
-- shifts             (id PK serial, crew_member_id FK, vehicle_id FK, shift_type, status)
-- patient_care_reports (id PK, incident_id FK, vitals, mpds_code, ...)
-- patient_tracking   (id PK serial, incident_id FK, current_phase, ...)
-- dea_locations      (id PK, lat, lon, location_type, is_available)
-- first_responders   (id PK, certification, is_available)
-- mci_triage         (id PK serial, tag_color, incident_id FK)
-- kpi_snapshots      (id PK serial, response times, compliance rates)
-- weather_conditions (id PK serial, condition, eta_multiplier, alert_level)
-- gis_layers         (id PK, layer_type, lat, lon, risk_level)
-- agency_resources   (id PK, agency, resource_type, status)
```

---

# Anexo D — Árbol de archivos del proyecto

```
KAIROS_CDS/
├── backend/                            # Servidor Python
│   ├── Dockerfile                      # Python 3.11-slim + requirements
│   ├── .dockerignore
│   ├── app/
│   │   ├── main.py                     # FastAPI app (300+ líneas)
│   │   ├── config.py                   # Configuración
│   │   ├── requirements.txt            # 27 dependencias
│   │   ├── api/                        # 21 routers
│   │   │   ├── ai.py                   # 20 endpoints IA
│   │   │   ├── alerts.py               # 2 endpoints alertas
│   │   │   ├── analytics.py            # 3 endpoints analytics
│   │   │   ├── assignments.py          # 3 endpoints asignación
│   │   │   ├── audit.py                # 2 endpoints auditoría
│   │   │   ├── auth.py                 # 4 endpoints autenticación
│   │   │   ├── blockchain.py           # 12 endpoints blockchain
│   │   │   ├── chat.py                 # 3 endpoints chat
│   │   │   ├── crews.py                # 8 endpoints tripulaciones
│   │   │   ├── digital_twin.py         # 4 endpoints gemelo digital
│   │   │   ├── epcr.py                 # 9 endpoints ePCR
│   │   │   ├── events.py              # 4 endpoints incidentes
│   │   │   ├── fleet.py                # 4 endpoints flota
│   │   │   ├── gas_stations.py         # 5 endpoints gasolineras
│   │   │   ├── health.py               # 1 endpoint health
│   │   │   ├── hospitals.py            # 3 endpoints hospitales
│   │   │   ├── kpis.py                 # 4 endpoints KPIs
│   │   │   ├── mci.py                  # 7 endpoints MCI
│   │   │   ├── resources.py            # 17 endpoints recursos
│   │   │   ├── security.py             # 9 endpoints seguridad
│   │   │   └── simulation.py           # 8 endpoints simulación
│   │   ├── auth/                       # Autenticación
│   │   │   ├── dependencies.py         # Guards y middleware
│   │   │   └── security.py             # JWT + bcrypt
│   │   ├── blockchain/                 # 7 módulos blockchain
│   │   │   ├── adapter.py
│   │   │   ├── batch_notarizer.py
│   │   │   ├── generate_wallet.py
│   │   │   ├── integrity.py
│   │   │   ├── merkle.py
│   │   │   └── notarizer.py
│   │   ├── core/                       # 19 módulos core
│   │   │   ├── ai_anomaly_detector.py
│   │   │   ├── ai_assignment.py
│   │   │   ├── ai_conversational_assistant.py
│   │   │   ├── ai_demand_prediction.py
│   │   │   ├── ai_eta_predictor.py
│   │   │   ├── ai_maintenance_predictor.py
│   │   │   ├── ai_recommendation_system.py
│   │   │   ├── ai_severity_classifier.py
│   │   │   ├── ai_traffic_integration.py
│   │   │   ├── ai_vision_analyzer.py
│   │   │   ├── anonymizer.py           # RGPD data anonymization
│   │   │   ├── data_collector.py       # Anon. data collection for retraining
│   │   │   ├── cybersecurity.py
│   │   │   ├── incident_generator.py
│   │   │   ├── metrics.py
│   │   │   ├── redis_client.py
│   │   │   ├── routing.py
│   │   │   ├── sim_adapter.py
│   │   │   └── twin_engine.py
│   │   ├── domain/
│   │   │   └── models.py
│   │   ├── realtime/
│   │   │   ├── ws.py
│   │   │   └── schemas.py
│   │   └── storage/
│   │       ├── db.py
│   │       ├── models_sql.py           # 18 modelos SQLAlchemy
│   │       └── repos/
│   │           ├── audit_repo.py
│   │           ├── incidents_repo.py
│   │           └── vehicles_repo.py
│   ├── models/
│   │   ├── demand_predictor.joblib
│   │   └── demand_scaler.joblib
│   └── tests/
│       ├── conftest.py
│       ├── test_api.py
│       ├── test_auth.py
│       ├── test_blockchain.py
│       ├── test_crews.py
│       ├── test_epcr.py
│       ├── test_events.py
│       ├── test_health.py
│       ├── test_live_and_audit.py
│       ├── test_operations.py
│       ├── test_security.py
│       └── test_simulation.py
│
├── frontend/                           # Cliente React
│   ├── Dockerfile                      # Multi-stage: build + Nginx
│   ├── .dockerignore
│   ├── index.html                      # OG meta tags + PWA manifest
│   ├── package.json
│   ├── vite.config.js                  # Chunk splitting configurado
│   ├── eslint.config.js
│   ├── public/
│   │   ├── manifest.json              # PWA manifest
│   │   ├── sw.js                      # Service Worker (cache offline)
│   │   ├── icon-192.png               # PWA icon 192x192
│   │   └── icon-512.png               # PWA icon 512x512
│   └── src/
│       ├── App.jsx
│       ├── App.css
│       ├── main.jsx
│       ├── index.css
│       ├── components/
│       │   ├── Layout.jsx
│       │   ├── ChatWidget.jsx
│       │   ├── ChatWidget.css
│       │   └── mapIcons.js
│       ├── context/
│       │   └── AuthContext.jsx
│       ├── pages/                      # 15 páginas
│       │   ├── Dashboard.jsx           # 2245 líneas
│       │   ├── IncidentList.jsx
│       │   ├── CreateIncident.jsx
│       │   ├── Analytics.jsx
│       │   ├── KPIs.jsx
│       │   ├── AIInsights.jsx
│       │   ├── AuditLog.jsx
│       │   ├── CrewManagement.jsx
│       │   ├── HospitalDashboard.jsx
│       │   ├── ParamedicView.jsx
│       │   ├── PatientTracking.jsx
│       │   ├── SecurityDashboard.jsx
│       │   ├── DriverMobile.jsx
│       │   ├── DriverLogin.jsx
│       │   └── Login.jsx
│       ├── styles/                     # 14 CSS files
│       │   ├── Dashboard.css
│       │   ├── Login.css
│       │   ├── Layout.css
│       │   ├── IncidentList.css
│       │   ├── Analytics.css
│       │   ├── AuditLog.css
│       │   ├── CreateIncident.css
│       │   ├── CrewManagement.css
│       │   ├── DriverMobile.css
│       │   ├── HospitalDashboard.css
│       │   ├── KPIs.css
│       ├── hooks/
│       │   └── useIncidentNotifications.js  # Push notifications nativas
│       │   ├── ParamedicView.css
│       │   ├── PatientTracking.css
│       │   └── SecurityDashboard.css
│       ├── utils/
│       │   └── statusLabels.js
│       └── test/
│           ├── App.test.jsx
│           ├── Login.test.jsx
│           └── setup.js
│
├── monitoring/
│   ├── prometheus.yml
│   ├── alert.rules.yml
│   └── alertmanager.yml
│
├── docker-compose.yml
├── package.json                        # Root (workspace scripts)
├── .github/
│   └── workflows/
│       └── ci.yml                      # CI: lint + tests (Redis service)
├── .dockerignore                       # Excluye node_modules, .git, etc.
├── LICENSE                             # MIT License
├── README.md                           # Documentación principal
└── FICHA_TECNICA_KAIROS_CDS.md         # Este documento
```

---

# Anexo E — Changelog v1.0.0

### Mejoras de producción

- **PWA completa**: `manifest.json`, Service Worker con cache offline, iconos 192x512px. Instalable en dispositivos móviles
- **Content-Security-Policy**: Header CSP configurable que restringe orígenes de scripts, estilos, imágenes y conexiones
- **CORS configurable**: Orígenes permitidos via variable de entorno `CORS_ORIGINS`
- **Docker full-stack**: Dockerfiles multi-stage para backend (Python slim) y frontend (Nginx), con health checks en cascada (db → redis → backend → frontend)
- **Vite chunk splitting**: Bundles separados por dominio (vendor-react 47KB, vendor-charts 421KB, vendor-map 149KB, vendor-utils 598KB). Reducción de bundle principal de 846KB a 39KB
- **ErrorBoundary + Lazy Loading**: Todas las páginas cargan con `React.lazy()` + `Suspense`, errores de render capturados con fallback UI
- **Loading Skeletons**: Placeholders animados en Dashboard, IncidentList, Analytics mientras cargan datos
- **Browser Notifications**: Notificaciones push nativas del navegador para incidentes nuevos
- **Open Graph + Twitter Cards**: Meta tags OG y Twitter para shared links en redes sociales
- **CI/CD**: Pipeline GitHub Actions con Redis service, lint enforced, tests automatizados
- **`.dockerignore`**: Archivos optimizados para builds Docker reproducibles
- **`LICENSE`**: Licencia MIT

### Correcciones de calidad

- **72+ tests pasando**: 11 suites de tests backend con in-memory SQLite, rate limiting desactivable para tests via `SECURITY_RATE_LIMIT_ENABLED`
- **Frontend lint**: ESLint con 0 errores críticos. Plugins `react-hooks` y `react-refresh` configurados
- **Rate limiting configurable**: Wired `SECURITY_RATE_LIMIT_ENABLED` en SecurityMiddleware para desactivar en tests/desarrollo
- **Password policy en tests**: Contraseñas de test actualizadas para cumplir política (mayúsculas requeridas)
- **Accesibilidad**: `aria-label`, `role`, `aria-live` en componentes clave del frontend

### Correcciones funcionales

- **Gestión de tripulaciones**: Turnos adaptativos según hora del día (DIA/NOCHE auto-detectado), filtros corregidos, ciclo de vida con finalización de turnos
- **Resolución de incidentes**: Auto-creación de ePCR y Patient Tracking al resolver (manual y automático)
- **TwinEngine**: Decremento correcto de carga hospitalaria al resolver, creación automática de registros clínicos
- **Panel de ciberseguridad**: Todos los endpoints reescritos con cuerpos JSON Pydantic, respuestas alineadas con frontend
- **Modo oscuro móvil**: 30+ reglas CSS para dark mode completo en la app conductor
- **Flujo de asignación IA**: `confirmAssignment()` ahora recibe `incidentId` como parámetro, formulario inline para override
- **Hospitales**: Auto-seed al cargar vacío, ambulancias en camino incluyen estado EN_ROUTE
- **Patient Tracking**: Seed de pacientes demo, avance de fase, toggle para incluir altas

### Nuevos endpoints

- `POST /api/crews/shifts/{id}/end` — Finalizar turno activo
- `POST /api/epcr/seed-demo-patients` — Seed de pacientes demo
- `GET /api/epcr/all-tracking-full` — Incluir pacientes dados de alta

### Mejoras de seguridad

- Modelos Pydantic para todos los POST de seguridad (`ScanInputBody`, `CheckPasswordBody`, `BlockIpBody`)
- IPs bloqueadas almacenan motivo y fecha
- Verificador de contraseñas con entropía y lista detallada de errores
- Escaneo de inputs retorna amenazas estructuradas

---

**KAIROS CDS v1.0.0** — Digital Twin for Emergency Fleet Management  
*Febrero 2026 — HPE GreenLake Cloud Platform*

---

> **NOTA CI/CD:**
> - El archivo de dependencias del backend es `backend/app/requirements.txt`.
> - El archivo de dependencias del frontend es `frontend/package-lock.json`.
> - En GitHub Actions, los paths en `.github/workflows/ci.yml` deben ser relativos al working-directory de cada job:
>   - Backend: `app/requirements.txt` (working-directory: `backend`)
>   - Frontend: `package-lock.json` (working-directory: `frontend`)
> - Si ves errores de "unable to cache dependencies" o "No file matched to requirements.txt", revisa los paths en el workflow.
