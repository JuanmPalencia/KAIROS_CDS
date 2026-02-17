# KAIROS CDS — Digital Twin for Emergency Fleet Management

> **v1.0.0** · Gemelo Digital de gestión de flotas de emergencia con IA, blockchain, ciberseguridad y monitorización en tiempo real.

[![CI](https://github.com/JuanmPalencia/KAIROS_CDS/actions/workflows/ci.yml/badge.svg)](https://github.com/JuanmPalencia/KAIROS_CDS/actions)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![React 19](https://img.shields.io/badge/react-19-61dafb)
![FastAPI](https://img.shields.io/badge/fastapi-0.115-009688)
![PostgreSQL 16](https://img.shields.io/badge/postgresql-16%20%2B%20PostGIS-336791)

---

## Tabla de contenidos

1. [Descripción](#descripción)
2. [Arquitectura](#arquitectura)
3. [Requisitos previos](#requisitos-previos)
4. [Inicio rápido](#inicio-rápido)
5. [Estructura del proyecto](#estructura-del-proyecto)
6. [Funcionalidades](#funcionalidades)
7. [Módulos de IA](#módulos-de-ia)
8. [Blockchain y Auditoría](#blockchain-y-auditoría)
9. [Referencia de API](#referencia-de-api)
10. [Frontend — Páginas](#frontend--páginas)
11. [Monitorización](#monitorización)
12. [Tests](#tests)
13. [Variables de entorno](#variables-de-entorno)
14. [Roles y permisos](#roles-y-permisos)

---

## Descripción

**KAIROS CDS** es un sistema de gemelo digital en tiempo real para la gestión de flotas de emergencia (ambulancias SVA, SVB, VIR, VAMM, SAMU). Diseñado para operar a nivel nacional con filtros por ciudad/región, integra:

- **Dashboard operativo** con mapa Leaflet, heatmaps, rutas OSRM y capas GIS.
- **10 módulos de Inteligencia Artificial** — 100% modelos locales (sklearn), con pipeline de anonimización RGPD y reentrenamiento continuo. Clasificación de severidad, predicción de demanda, ETA, detección de anomalías, mantenimiento predictivo, visión por computador, asistente conversacional, tráfico, recomendaciones y asignación inteligente.
- **Blockchain BSV** — Notarización de auditoría con árboles Merkle y difusión on-chain.
- **Monitorización Prometheus + Alertmanager** — Métricas HTTP, flota y alertas.
- **RBAC** — Control de acceso basado en roles (ADMIN, OPERATOR, DOCTOR, VIEWER).

---

## Arquitectura

```
┌──────────────────────────────────────────────────────────────────────┐
│                        KAIROS CDS — v1.0                            │
├────────────────┬──────────────────────┬──────────────────────────────┤
│  React 19      │   FastAPI 0.115      │  Infraestructura             │
│  + Vite 7      │   Python 3.10+       │                              │
│  + Leaflet     │                      │  PostgreSQL 16 + PostGIS     │
│  + Recharts    │   TwinEngine         │  Redis 7                     │
│  + lucide-react│   (asyncio loop)     │  Prometheus + Alertmanager   │
│                │                      │  BSV Blockchain              │
│  12 páginas    │   118 endpoints      │                              │
│  Dark mode     │   10 módulos IA      │                              │
│  City filter   │   WebSocket /ws/live │                              │
└────────────────┴──────────────────────┴──────────────────────────────┘
```

---

## Requisitos previos

| Herramienta    | Versión | Instalación                               |
| -------------- | -------- | ------------------------------------------ |
| Python         | ≥ 3.10  | https://python.org                         |
| Node.js        | ≥ 18    | https://nodejs.org                         |
| Docker Desktop | ≥ 24    | https://docker.com/products/docker-desktop |
| Git            | ≥ 2.x   | https://git-scm.com                        |

---

## Inicio rápido

### Opción A — Docker (recomendado)

```bash
git clone <repo-url> KAIROS_CDS && cd KAIROS_CDS
cp backend/.env.example backend/.env    # Configurar variables
cp frontend/.env.example frontend/.env
docker compose up -d --build            # Todo: DB + Redis + Backend + Frontend + Monitoring
# → Frontend: http://localhost:5173
# → Backend:  http://localhost:5001/docs
```

### Opción B — Desarrollo local

#### 1. Infraestructura

```bash
git clone <repo-url> KAIROS_CDS && cd KAIROS_CDS
docker compose up -d db redis prometheus alertmanager
```

#### 2. Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate   |  Linux/Mac: source .venv/bin/activate
pip install -r app/requirements.txt
```

#### 3. Arrancar backend

```bash
cd backend
# Windows PowerShell:
$env:PYTHONPATH = "."
python -m uvicorn app.main:app --host 0.0.0.0 --port 5001 --reload
```

#### 4. Frontend

```bash
cd frontend
npm install
npm run dev           # → http://localhost:5173
```

### 5. Seed de datos iniciales

```bash
# 1. Crear usuario admin
curl -X POST http://localhost:5001/api/auth/init-admin

# 2. Seed de flota (ambulancias españolas: SVB, SVA, VIR, VAMM, SAMU)
curl -X POST http://localhost:5001/fleet/seed-ambulances

# 3. Seed de hospitales
curl -X POST http://localhost:5001/api/hospitals/seed

# 4. Seed de recursos (DEAs, gasolineras, agencias, first responders, GIS)
curl -X POST http://localhost:5001/api/resources/seed-all
curl -X POST http://localhost:5001/api/gas-stations/seed

# 5. Seed de tripulaciones
curl -X POST http://localhost:5001/api/crews/seed

# 6. (Opcional) Iniciar generación automática de incidentes
curl -X POST http://localhost:5001/simulation/auto-generate/start
```

### 6. Credenciales por defecto

| Usuario      | Contraseña     | Rol      | Acceso principal                                          |
| ------------ | --------------- | -------- | --------------------------------------------------------- |
| `admin`    | `admin123`    | ADMIN    | Acceso total: usuarios, auditoría, blockchain, IA, flota |
| `operator` | `operator123` | OPERATOR | Despacho: incidentes, asignaciones, flota, tripulaciones  |
| `doctor`   | `doctor123`   | DOCTOR   | Clínico: hospitales, ePCR, pacientes, AI insights        |
| `viewer`   | `viewer123`   | VIEWER   | Solo lectura: dashboard, incidentes, analytics, KPIs      |

> ⚠️ Cambiar en producción. Configurar `SECRET_KEY` vía variable de entorno.

---

## Estructura del proyecto

```
KAIROS_CDS/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI app + lifespan + WebSocket
│   │   ├── config.py                  # Variables de entorno
│   │   ├── api/                       # 18 routers (118 endpoints)
│   │   │   ├── ai.py                  #   IA: 20 endpoints
│   │   │   ├── alerts.py              #   Alertas Prometheus
│   │   │   ├── analytics.py           #   Dashboard analytics + response-times
│   │   │   ├── assignments.py         #   Asignación IA de vehículos
│   │   │   ├── audit.py               #   Log de auditoría + export CSV
│   │   │   ├── auth.py                #   Login, registro, RBAC
│   │   │   ├── blockchain.py          #   Merkle + verificación BSV
│   │   │   ├── crews.py               #   Tripulaciones y turnos
│   │   │   ├── epcr.py                #   ePCR (Electronic Patient Care Report)
│   │   │   ├── events.py              #   CRUD incidentes + timeline
│   │   │   ├── fleet.py               #   Flota: seed + CRUD vehículos
│   │   │   ├── gas_stations.py        #   Gasolineras + repostaje
│   │   │   ├── health.py              #   Health check
│   │   │   ├── hospitals.py           #   CRUD hospitales
│   │   │   ├── kpis.py                #   KPIs en tiempo real + snapshots
│   │   │   ├── mci.py                 #   MCI: triaje START + pre-arrival
│   │   │   ├── resources.py           #   DEA, GIS, weather, agencies, SSM
│   │   │   └── simulation.py          #   Generación automática incidentes
│   │   ├── auth/
│   │   │   ├── dependencies.py        #   get_current_user, require_role
│   │   │   └── security.py            #   JWT + bcrypt
│   │   ├── blockchain/
│   │   │   ├── adapter.py             #   WhatsOnChain BSV adapter
│   │   │   ├── batch_notarizer.py     #   Merkle batch notarization
│   │   │   ├── generate_wallet.py     #   BSV wallet generation
│   │   │   ├── integrity.py           #   Chain integrity verification
│   │   │   ├── merkle.py              #   Merkle tree implementation
│   │   │   └── notarizer.py           #   Single-record notarization
│   │   ├── core/
│   │   │   ├── ai_anomaly_detector.py #   Isolation Forest anomaly detection
│   │   │   ├── ai_assignment.py       #   Optimal vehicle assignment
│   │   │   ├── ai_conversational_assistant.py  # TF-IDF + LogisticRegression intent classifier
│   │   │   ├── ai_demand_prediction.py#   Random Forest demand hotspots
│   │   │   ├── ai_eta_predictor.py    #   Gradient Boosting ETA
│   │   │   ├── ai_maintenance_predictor.py    # Predictive maintenance
│   │   │   ├── ai_recommendation_system.py    # Operator recommendations
│   │   │   ├── ai_severity_classifier.py      # TF-IDF + RandomForest severity classifier
│   │   │   ├── ai_traffic_integration.py      # Traffic-aware routing
│   │   │   ├── ai_vision_analyzer.py  #   Pillow + SVM scene analysis
│   │   │   ├── incident_generator.py  #   Synthetic incident generator
│   │   │   ├── metrics.py             #   Prometheus counters/histograms
│   │   │   ├── routing.py             #   OSRM routing integration
│   │   │   ├── sim_adapter.py         #   Simulation adapter
│   │   │   ├── twin_engine.py         #   Digital Twin engine (asyncio)
│   │   │   ├── anonymizer.py          #   RGPD data anonymization
│   │   │   └── data_collector.py      #   Anonymized data collection for retraining
│   │   ├── domain/
│   │   │   └── models.py              #   Pydantic DTOs
│   │   ├── realtime/
│   │   │   ├── ws.py                  #   WebSocket manager
│   │   │   └── schemas.py             #   WS schemas (reserved v2)
│   │   └── storage/
│   │       ├── db.py                  #   SQLAlchemy engine + session
│   │       ├── models_sql.py          #   40+ SQLAlchemy models
│   │       └── repos/                 #   Repository pattern
│   │           ├── audit_repo.py
│   │           ├── incidents_repo.py
│   │           └── vehicles_repo.py
│   ├── Dockerfile                     #   Containerización backend
│   ├── train_all_models.py            #   Entrenamiento unificado de 6 modelos IA
│   ├── datasets/                      #   Datasets CSV para entrenamiento
│   │   ├── severity_dataset.csv       #   Emergencias médicas etiquetadas
│   │   ├── chat_intents_dataset.csv   #   Intents de chat etiquetados
│   │   └── vision_scenes_dataset.csv  #   Escenas de emergencia etiquetadas
│   ├── .env.example                   #   Variables de entorno (template)
│   ├── tests/
│   │   ├── conftest.py                #   Fixtures (SQLite in-memory, auth)
│   │   ├── test_api.py
│   │   ├── test_auth.py
│   │   ├── test_events.py
│   │   ├── test_health.py
│   │   ├── test_live_and_audit.py
│   │   ├── test_crews.py              #   Tripulaciones y turnos
│   │   ├── test_security.py           #   Ciberseguridad (11 tests)
│   │   ├── test_operations.py         #   Hospitales, flota, analytics
│   │   ├── test_simulation.py         #   Simulación + Digital Twin
│   │   ├── test_blockchain.py         #   Blockchain + Merkle
│   │   └── test_epcr.py               #   ePCR + Patient Tracking
│   └── models/                        #   ML models (.joblib)
│
├── frontend/
│   ├── Dockerfile                     #   Multi-stage build (Node 20)
│   ├── .env.example                   #   VITE_API_URL template
│   ├── src/
│   │   ├── App.jsx                    #   Router + lazy loading + ErrorBoundary
│   │   ├── config.js                  #   API_BASE centralizada
│   │   ├── main.jsx                   #   Entry point
│   │   ├── components/
│   │   │   ├── Layout.jsx             #   Nav + city filter + dark mode + a11y
│   │   │   ├── ErrorBoundary.jsx      #   Captura errores de componentes
│   │   │   ├── LoadingFallback.jsx    #   Spinner para Suspense
│   │   │   ├── Skeleton.jsx           #   Loading skeletons (table/cards/KPI)
│   │   │   └── mapIcons.js            #   Leaflet SVG icons
│   │   ├── hooks/
│   │   │   └── useIncidentNotifications.js  # Browser notifications + audio
│   │   ├── context/
│   │   │   └── AuthContext.jsx        #   JWT auth provider
│   │   ├── pages/                     #   15 páginas
│   │   │   ├── Dashboard.jsx          #   Mapa + flota + incidentes
│   │   │   ├── IncidentList.jsx       #   Lista con filtros de estado
│   │   │   ├── CreateIncident.jsx     #   Formulario + IA classifier
│   │   │   ├── Analytics.jsx          #   4 gráficos + export CSV/PDF
│   │   │   ├── KPIs.jsx               #   KPIs tiempo real + compliance
│   │   │   ├── AIInsights.jsx         #   Dashboard IA + chat
│   │   │   ├── AuditLog.jsx           #   Auditoría + blockchain
│   │   │   ├── CrewManagement.jsx     #   Tripulaciones y turnos
│   │   │   ├── HospitalDashboard.jsx  #   Estado de hospitales
│   │   │   ├── ParamedicView.jsx      #   Vista paramédico + ePCR
│   │   │   ├── PatientTracking.jsx    #   Tracking de pacientes
│   │   │   └── Login.jsx              #   Autenticación
│   │   ├── styles/                    #   14 archivos CSS (dark mode + responsive)
│   │   └── test/                      #   Vitest + Testing Library
│   └── vite.config.js
│
├── monitoring/
│   ├── prometheus.yml                 #   Scrape config
│   ├── alert.rules.yml                #   Alert rules
│   └── alertmanager.yml               #   Notification config
│
├── docker-compose.yml                 #   Full-stack: DB+Redis+Backend+Frontend+Monitoring
└── .github/workflows/ci.yml           #   CI pipeline
```

---

## Funcionalidades

### Operaciones en tiempo real

- **Dashboard con mapa** — Leaflet con capas: vehículos, incidentes, hospitales, gasolineras, DEAs, heatmap, rutas OSRM, agencies
- **TwinEngine** — Motor de gemelo digital async: ciclo OPEN → ASSIGNED → EN_ROUTE → TO_HOSPITAL → RESOLVED con progreso de ruta en tiempo real
- **WebSocket** `/ws/live` — Broadcast de estado cada 2 s
- **Polling** `/api/live` — Fallback REST con filtro por ciudad
- **Filtro por ciudad/región** — Selector global en la barra de navegación, filtra Dashboard, Analytics, KPIs e Incidentes

### Gestión de incidentes

- Creación manual y automática (simulador configurable)
- 14 tipos de incidentes (CARDIO, RESPIRATORY, NEUROLOGICAL, TRAUMA, BURN, POISONING, OBSTETRIC, PEDIATRIC, PSYCHIATRIC, FALL, ALLERGIC, DIABETIC, DROWNING, GENERAL)
- Timeline completo por incidente
- Asignación IA de vehículo óptimo
- Clasificación automática de severidad (1–5)

### Flota de emergencia española

- 5 subtipos reales: **SVB** (Soporte Vital Básico), **SVA** (Soporte Vital Avanzado), **VIR** (Intervención Rápida), **VAMM** (Asistencia Múltiple), **SAMU** (Atención Urgente)
- Consumo de combustible realista, repostaje en gasolineras cercanas
- KPIs por vehículo: tiempo medio, casos atendidos, combustible

### KPIs y Analytics

- **KPIs en tiempo real** — Tiempos de respuesta, compliance SAMUR (<8 min / <15 min), utilización de flota
- **Snapshots** — Guardado periódico de estado de KPIs
- **Analytics** — 4 gráficos: incidentes por tipo, por severidad, distribución horaria, tiempo de respuesta por severidad
- **Export** — CSV y PDF desde analytics

### Gestión de recursos

- Hospitales con camas, especialidades y carga en tiempo real
- DEAs (desfibriladores) geolocalizados
- Gasolineras con precios y horarios
- First Responders (ciudadanos voluntarios)
- Agencias multi-recurso (Bomberos, Policía, etc.)
- Capas GIS configurables
- Meteorología con multiplicador de ETA
- SSM (System Status Management) zones

### Atención al paciente

- **ePCR** — Electronic Patient Care Report con constantes vitales
- **MCI** — Triaje START para incidentes con múltiples víctimas
- **MPDS** — Protocolos pre-arrival por tipo de incidente
- **Patient Tracking** — Seguimiento de fase del paciente

### Tripulaciones

- Gestión de crew members con roles y certificaciones (Médico, Enfermero, TES, Conductor)
- Turnos adaptativos según hora del día (Día/Noche/Guardia 24h), con ciclo de vida: ACTIVE → COMPLETED
- Asignación de tripulación a vehículos con finalización de turno
- Seed automático con 12 crew members y asignaciones a 8 vehículos

### Seguridad y Ciberseguridad

- JWT con expiración configurable
- RBAC: ADMIN, OPERATOR, DOCTOR, VIEWER
- Panel de ciberseguridad: eventos de seguridad, sesiones activas, IPs bloqueadas, firewall
- Rate limiting, detección de brute-force, escaneo de inputs (SQL injection, XSS, path traversal)
- Protección CSRF, gestión de sesiones, bloqueo/desbloqueo de IPs
- Herramientas de seguridad: escáner de amenazas, verificador de fortaleza de contraseñas
- Auditoría completa de todas las acciones
- Blockchain BSV con árboles Merkle para inmutabilidad

---

## Módulos de IA

| #  | Módulo                               | Archivo                            | Descripción                                               |
| -- | ------------------------------------- | ---------------------------------- | ---------------------------------------------------------- |
| 1  | **Clasificación de severidad** | `ai_severity_classifier.py`      | TF-IDF + RandomForest — clasifica severidad 1–5          |
| 2  | **Predicción de demanda**      | `ai_demand_prediction.py`        | Random Forest → hotspot zones por hora/día               |
| 3  | **Predicción de ETA**          | `ai_eta_predictor.py`            | Gradient Boosting con distancia, velocidad, hora, tráfico |
| 4  | **Detección de anomalías**    | `ai_anomaly_detector.py`         | Isolation Forest sobre métricas de vehículos/incidentes  |
| 5  | **Mantenimiento predictivo**    | `ai_maintenance_predictor.py`    | Predicción de fallos por km, combustible, horas de uso    |
| 6  | **Visión por computador**      | `ai_vision_analyzer.py`          | Pillow + TF-IDF + SVM — análisis de escenas de emergencia|
| 7  | **Asistente conversacional**    | `ai_conversational_assistant.py` | TF-IDF + LogisticRegression — clasificador de intents     |
| 8  | **Integración de tráfico**    | `ai_traffic_integration.py`      | Condiciones de tráfico en tiempo real + ajuste ETA        |
| 9  | **Recomendaciones**             | `ai_recommendation_system.py`    | Aprendizaje de decisiones del operador                     |
| 10 | **Asignación inteligente**     | `ai_assignment.py`               | Optimización: distancia + fuel + trust_score + severidad  |

> 🔒 **100% local** — ningún módulo requiere API keys externas (OpenAI, etc.).  
> 🔄 **Aprendizaje continuo** — los datos operativos se anonimizan (RGPD) y alimentan los datasets de reentrenamiento.  
> 📊 **Modelos entrenables** — `python train_all_models.py` entrena los 6 modelos desde datasets CSV.

### Anonimización y Aprendizaje Continuo (RGPD)

El sistema implementa un **pipeline automático de mejora continua** que cumple con el RGPD:

```
  Dato operativo  ─→  Anonimizador (RGPD)  ─→  Dataset CSV  ─→  Reentrenamiento
  (incidente/chat/     (supresión PII,          (append          (POST /api/ai/retrain
   imagen)              generalización,          automático)       o train_all_models.py)
                        perturbación)
```

| Capa              | Técnica                                      | Ejemplo                                |
| ----------------- | -------------------------------------------- | --------------------------------------- |
| **Supresión**     | Eliminación total de campos PII              | nombre, DNI, teléfono, email → borrado |
| **Generalización**| Reducción de precisión                       | coord. 40.4168 → 40.42; edad 42 → 30-44 |
| **Perturbación**  | Ruido gaussiano ±5%                         | FC 80 → 78; TAS 120 → 122             |
| **Scrubbing**     | Regex contra texto libre                     | "paciente Juan Pérez" → "[NOMBRE_ANON]"|

Archivos clave:
- `app/core/anonymizer.py` — Motor de anonimización (18 patrones PII)
- `app/core/data_collector.py` — Recolector thread-safe con append a CSV

### Endpoints de IA

| Método  | Endpoint                                     | Descripción                        |
| -------- | -------------------------------------------- | ----------------------------------- |
| `GET`  | `/api/ai/status`                           | Estado de todos los módulos        |
| `GET`  | `/api/ai/insights/dashboard`               | Dashboard con métricas de IA       |
| `POST` | `/api/ai/severity/classify`                | Clasificar severidad de texto       |
| `GET`  | `/api/ai/demand/hotspots`                  | Zonas de alta demanda predichas     |
| `POST` | `/api/ai/demand/train`                     | Entrenar predictor de demanda       |
| `GET`  | `/api/ai/eta/predict/{v}/{i}`              | ETA para vehículo→incidente       |
| `POST` | `/api/ai/eta/train`                        | Entrenar predictor de ETA           |
| `GET`  | `/api/ai/anomalies/vehicles`               | Anomalías en vehículos            |
| `GET`  | `/api/ai/anomalies/incidents`              | Anomalías en incidentes            |
| `GET`  | `/api/ai/anomalies/system-health`          | Salud del sistema                   |
| `POST` | `/api/ai/anomalies/train`                  | Entrenar detector de anomalías     |
| `GET`  | `/api/ai/maintenance/predict/{v}`          | Predicción mantenimiento vehículo |
| `GET`  | `/api/ai/maintenance/fleet-schedule`       | Schedule de mantenimiento flota     |
| `POST` | `/api/ai/vision/analyze-incident`          | Analizar imagen de incidente        |
| `POST` | `/api/ai/vision/analyze-scene-safety`      | Evaluar seguridad de escena         |
| `POST` | `/api/ai/chat`                             | Enviar mensaje al asistente         |
| `POST` | `/api/ai/chat/clear`                       | Limpiar historial de chat           |
| `GET`  | `/api/ai/traffic/route`                    | Ruta optimizada por tráfico        |
| `GET`  | `/api/ai/recommendations/personalized/{i}` | Recomendaciones por incidente       |
| `GET`  | `/api/ai/recommendations/profile`          | Perfil del operador                 |
| `GET`  | `/api/ai/datasets/stats`                   | Estadísticas datasets reentrenamiento |
| `POST` | `/api/ai/retrain`                          | Re-entrenar todos los modelos       |

---

## Blockchain y Auditoría

El sistema implementa un **registro inmutable de auditoría** usando árboles Merkle y la blockchain BSV:

1. Cada acción genera un `AuditLog` con hash SHA-256.
2. Los registros se agrupan en lotes Merkle (`MerkleBatch`).
3. La raíz Merkle se notariza opcionalmente en BSV vía WhatsOnChain.
4. Cualquier usuario puede verificar la integridad de un registro.

| Método  | Endpoint                                       | Descripción                  |
| -------- | ---------------------------------------------- | ----------------------------- |
| `GET`  | `/api/blockchain/verify/{hash}`              | Verificar hash (público)     |
| `GET`  | `/api/blockchain/verify-by-id/{id}`          | Verificar por audit_id        |
| `GET`  | `/api/blockchain/status`                     | Estado del sistema blockchain |
| `GET`  | `/api/blockchain/records`                    | Registros recientes           |
| `POST` | `/api/blockchain/merkle/batch`               | Crear lote Merkle             |
| `POST` | `/api/blockchain/merkle/broadcast/{id}`      | Difundir a BSV                |
| `POST` | `/api/blockchain/merkle/batch-and-broadcast` | Batch + broadcast             |
| `GET`  | `/api/blockchain/merkle/pending`             | Registros pendientes          |
| `GET`  | `/api/blockchain/merkle/proof/{id}`          | Proof Merkle de un registro   |
| `GET`  | `/api/blockchain/merkle/verify/{id}`         | Verificar proof Merkle        |
| `GET`  | `/api/blockchain/merkle/batches`             | Listar batches                |

---

## Referencia de API

**131 endpoints** organizados en 21 routers. Documentación interactiva:

- **Swagger UI** → http://localhost:5001/docs
- **ReDoc** → http://localhost:5001/redoc

### Resumen por categoría

| Categoría   | Prefijo                        | Endpoints | Descripción                            |
| ------------ | ------------------------------ | --------- | --------------------------------------- |
| Health       | `/health`                    | 1         | Health check                            |
| Auth         | `/api/auth`                  | 4         | Login, registro, init-admin, me         |
| Fleet        | `/fleet`                     | 3         | Seed, CRUD vehículos                   |
| Events       | `/events`                    | 4         | CRUD incidentes + timeline              |
| Assignments  | `/api/assignments`           | 3         | Sugerencia IA + confirmar + resolver    |
| Analytics    | `/api/analytics`             | 3         | Dashboard, áreas, response-times       |
| KPIs         | `/api/kpis`                  | 4         | Realtime, history, snapshot, by-vehicle |
| AI           | `/api/ai`                    | 20        | 10 módulos de IA                       |
| Blockchain   | `/api/blockchain`            | 11        | Verificación + Merkle                  |
| Audit        | `/api/audit`                 | 2         | Logs + export CSV                       |
| Hospitals    | `/api/hospitals`             | 3         | CRUD + seed                             |
| Gas Stations | `/api/gas-stations`          | 4         | CRUD + nearest + refuel                 |
| Crews        | `/api/crews`                 | 8         | Members + shifts + seed + end shift   |
| ePCR         | `/api/epcr`                  | 9         | Patient Care Reports + tracking       |
| MCI          | `/api/mci`                   | 6         | Triaje START + pre-arrival              |
| Resources    | `/api/resources`             | 13        | DEA, GIS, weather, agencies, SSM        |
| Simulation   | `/simulation`                | 8         | Generación + velocidad de simulación |
| Security     | `/api/security`              | 9         | Ciberseguridad + firewall + tools      |
| Digital Twin | `/digital-twin`              | 4         | Telemetría + what-if                  |
| Chat         | `/api/chat`                  | 3         | Chat operativo multi-canal             |
| Live         | `/api/live`, `/api/cities` | 2         | Polling + filtro ciudades               |

---

## Frontend — Páginas

| Página                       | Ruta                  | Descripción                                                                    |
| ----------------------------- | --------------------- | ------------------------------------------------------------------------------- |
| **Dashboard**           | `/`                 | Mapa principal con flota, incidentes, rutas, heatmap, capas GIS, weather widget |
| **Lista de Incidentes** | `/incidents`        | Tabla con filtros de estado (OPEN/ASSIGNED/RESOLVED) y city filter              |
| **Crear Incidente**     | `/create-incident`  | Formulario con 14 tipos, severidad, geolocalización, IA severity classifier    |
| **Analytics**           | `/analytics`        | 4 gráficos (tipo, severidad, horario, response-time) + export CSV/PDF          |
| **KPIs**                | `/kpis`             | Tiempo respuesta, compliance SAMUR, flota, incidentes, tabla por vehículo      |
| **AI Insights**         | `/ai-insights`      | Dashboard IA: anomalías, mantenimiento, demanda, chat conversacional           |
| **Auditoría**          | `/audit`            | Log paginado + export CSV + verificación blockchain por hash                   |
| **Tripulaciones**       | `/crews`            | Gestión de miembros, turnos, roles y certificaciones                           |
| **Hospitales**          | `/hospitals`        | Dashboard con camas, especialidades, carga en tiempo real                       |
| **Vista Paramédico**   | `/paramedic`        | ePCR: constantes vitales, MPDS protocols, vista de campo                        |
| **Patient Tracking**    | `/patient-tracking` | Estado y fase de pacientes en curso                                             |
| **Seguridad**         | `/security`       | Panel de ciberseguridad: eventos, sesiones, firewall, herramientas                  |
| **App Conductor**     | `/driver`         | Interfaz móvil para conductores de ambulancia                                        |
| **Login**               | `/login`            | Autenticación con JWT                                                          |

### Características UI transversales

- **Dark mode** — Toggle en la barra de navegación, persiste en localStorage
- **City filter** — Selector global de ciudad que filtra datos en Dashboard, Analytics, KPIs e Incidentes
- **Responsive** — Grid adaptativo en todas las páginas con breakpoints 768px y 480px
- **Accesibilidad (a11y)** — Skip-to-content link, ARIA labels/roles, semántica HTML, focus-visible
- **Code splitting** — React.lazy + Suspense para todas las páginas, reducción de bundle inicial
- **ErrorBoundary** — Captura de errores con fallback UI amigable y opción de reintentar
- **Loading skeletons** — Componentes Skeleton (tabla, cards, KPI) con shimmer animation
- **Browser notifications** — Alertas nativas del navegador para incidentes de severidad 4-5 con audio
- **Toast notifications** — react-hot-toast para feedback no intrusivo
- **Configuración centralizada** — API_BASE en `config.js`, sin URLs hardcodeadas

---

## Monitorización

```yaml
# docker-compose.yml incluye:
Prometheus   → http://localhost:9090    # Métricas
Alertmanager → http://localhost:9093    # Alertas
```

### Métricas exportadas (`/metrics`)

| Métrica                          | Tipo      | Descripción                                |
| --------------------------------- | --------- | ------------------------------------------- |
| `http_requests_total`           | Counter   | Peticiones HTTP por método/endpoint/status |
| `http_request_duration_seconds` | Histogram | Duración de peticiones                     |
| `incidents_created_total`       | Counter   | Incidentes creados                          |
| `incidents_resolved_total`      | Counter   | Incidentes resueltos                        |
| `available_vehicles_count`      | Gauge     | Vehículos disponibles                      |
| `database_connections_active`   | Gauge     | Conexiones BD activas                       |

### Alertas configuradas

- Alta latencia de respuesta (>2 s p95)
- Baja tasa de resolución de incidentes
- Vehículos con bajo combustible
- Errores HTTP rate >5 %

---

## Tests

```bash
# Backend (pytest)
cd backend
$env:PYTHONPATH = "."          # Windows PowerShell
python -m pytest tests/ -v

# Frontend (vitest)
cd frontend
npm test
```

### Cobertura de tests (72 tests)

| Área            | Archivo                    | Tests | Qué cubre                                           |
| ---------------- | -------------------------- | ----- | ---------------------------------------------------- |
| Health           | `test_health.py`         | 1     | `/health` endpoint                                 |
| Auth             | `test_auth.py`           | 4     | Login, registro, roles                               |
| Events           | `test_events.py`         | 3     | CRUD incidentes                                      |
| API              | `test_api.py`            | 3     | Fleet, live data                                     |
| Live + Audit     | `test_live_and_audit.py` | 3     | `/api/live`, audit logs                            |
| Crews            | `test_crews.py`          | 5     | Seed, miembros, turnos, fin de turno                 |
| Security         | `test_security.py`       | 11    | Dashboard, SQLi, XSS, CSRF, passwords, sesiones     |
| Operations       | `test_operations.py`     | 8     | Hospitales, flota, analytics, KPIs, ciudades         |
| Simulation       | `test_simulation.py`     | 6     | Generación, velocidad, what-if, fleet health         |
| Blockchain       | `test_blockchain.py`     | 6     | Status, records, Merkle, audit logs                  |
| ePCR             | `test_epcr.py`           | 5     | MPDS, tracking, pacientes demo                       |
| Frontend         | `App.test.jsx`           | 1     | Renderizado básico                                  |
| Frontend         | `Login.test.jsx`         | 1     | Flujo de login                                       |

---

## Variables de entorno

Crear `backend/.env` (incluido en `.gitignore`):

```env
# Base de datos
DATABASE_URL=postgresql+psycopg2://twin:twin@localhost:55432/twin

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# JWT
SECRET_KEY=tu-clave-secreta-segura-aqui

# BSV Blockchain (opcional)
BSV_PRIVATE_KEY=...
BSV_NETWORK=mainnet

# Nota: NO se requiere OPENAI_API_KEY — todos los modelos IA son locales (sklearn)
```

---

## Roles y permisos

| Rol                | Dashboard | Incidentes   | Crear incid. | Asignar | Analytics / KPIs | AI Insights | Hospitales | ePCR / Pacientes | Tripulaciones | Auditoría | Admin |
| ------------------ | --------- | ------------ | ------------ | ------- | ---------------- | ----------- | ---------- | ---------------- | ------------- | ---------- | ----- |
| **ADMIN**    | ✅        | ✅           | ✅           | ✅      | ✅               | ✅          | ✅         | ✅               | ✅            | ✅         | ✅    |
| **OPERATOR** | ✅        | ✅ (lectura) | ❌           | ✅      | ✅               | ✅          | ✅         | ✅               | ✅            | ❌         | ❌    |
| **DOCTOR**   | ✅        | ✅ (lectura) | ❌           | ❌      | ✅               | ❌          | ❌         | ✅               | ❌            | ❌         | ❌    |
| **VIEWER**   | ✅        | ✅ (lectura) | ❌           | ❌      | ✅               | ❌          | ❌         | ❌               | ❌            | ❌         | ❌    |

### Implementación técnica

- **Backend**: `require_role(["ADMIN", "OPERATOR"])` en FastAPI Depends
- **Frontend**: `<RoleRoute roles={[...]}>`  protege rutas; `canAccess` oculta navegación
- **JWT**: Token con `sub` (username) + `role`, expiración configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`
- **Seed**: `POST /api/auth/init-admin` crea los 4 usuarios demo automáticamente

---

> **NOTA CI/CD:**
> - El archivo de dependencias del backend es `backend/app/requirements.txt`.
> - El archivo de dependencias del frontend es `frontend/package-lock.json`.
> - Si usas GitHub Actions, asegúrate de que los paths en `.github/workflows/ci.yml` sean relativos al working-directory de cada job:
>   - Backend: `app/requirements.txt` (working-directory: `backend`)
>   - Frontend: `package-lock.json` (working-directory: `frontend`)
> - Si ves errores de "unable to cache dependencies" o "No file matched to requirements.txt", revisa los paths en el workflow.

---

## Docker — Despliegue completo

El proyecto incluye Dockerfiles para backend y frontend con despliegue one-command:

```bash
# Levantar todo el stack
docker compose up -d --build

# Verificar servicios
docker compose ps

# Ver logs
docker compose logs -f backend frontend
```

| Servicio     | Puerto | Descripción           |
| ------------ | ------ | ---------------------- |
| PostgreSQL   | 55432  | Base de datos + PostGIS|
| Redis        | 6379   | Cache + pub/sub        |
| Backend      | 5001   | API FastAPI            |
| Frontend     | 5173   | SPA React (serve)      |
| Prometheus   | 9090   | Métricas              |
| Alertmanager | 9093   | Alertas                |

---

> KAIROS CDS v1.0.0 — Digital Twin for Emergency Fleet Management
