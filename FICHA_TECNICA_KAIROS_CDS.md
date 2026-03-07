# KAIROS CDS — Ficha Técnica Completa

## Sistema de Gemelo Digital para Gestión de Flotas de Emergencia

**Versión:** 1.0.0
**Fecha:** Marzo 2026
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
9. [Sistema de Routing (OSRM)](#9-sistema-de-routing-osrm)
10. [Módulos de Inteligencia Artificial](#10-módulos-de-inteligencia-artificial)
11. [Sistema de Ciberseguridad](#11-sistema-de-ciberseguridad)
12. [Blockchain y Auditoría Inmutable](#12-blockchain-y-auditoría-inmutable)
13. [Frontend — React 19](#13-frontend--react-19)
14. [Gestión de Incidentes](#14-gestión-de-incidentes)
15. [Gestión de Flota](#15-gestión-de-flota)
16. [Gestión de Tripulaciones y Turnos](#16-gestión-de-tripulaciones-y-turnos)
17. [Atención al Paciente (ePCR)](#17-atención-al-paciente-epcr)
18. [Sistema Hospitalario](#18-sistema-hospitalario)
19. [KPIs y Analytics](#19-kpis-y-analytics)
20. [Monitorización — Prometheus y Alertmanager](#20-monitorización--prometheus-y-alertmanager)
21. [Comunicación en Tiempo Real](#21-comunicación-en-tiempo-real)
22. [Sistema de Roles y Permisos (RBAC)](#22-sistema-de-roles-y-permisos-rbac)
23. [Simulación y Generación Automática de Incidentes](#23-simulación-y-generación-automática-de-incidentes)
24. [Gestión de Recursos Multi-Agencia](#24-gestión-de-recursos-multi-agencia)
25. [Referencia Completa de API](#25-referencia-completa-de-api)
26. [Testing y Calidad de Código](#26-testing-y-calidad-de-código)
27. [Configuración y Variables de Entorno](#27-configuración-y-variables-de-entorno)
28. [Guía de Instalación](#28-guía-de-instalación)
29. [Rendimiento y Escalabilidad](#29-rendimiento-y-escalabilidad)
30. [Glosario Técnico](#30-glosario-técnico)

---

# 1. Resumen Ejecutivo

KAIROS CDS (Clinical Decision Support) es una plataforma de **gemelo digital en tiempo real** para la gestión integral de Servicios de Emergencias Médicas (SEM). Simula, monitoriza y optimiza la operación de flotas de ambulancias a nivel de ciudad, integrando diez módulos de inteligencia artificial completamente locales, blockchain BSV para auditoría inmutable, un panel de ciberseguridad con detección activa de amenazas y monitorización con Prometheus + Alertmanager.

El sistema fue desarrollado como entrega para el **HPE GreenLake CDS Challenge 2026**, contextualizando la operación de flotas en la Comunidad de Madrid (España), siguiendo estándares SAMUR, SUMMA 112 y SAMU europeos.

## 1.1 Capacidades principales

| Capacidad | Descripción |
|---|---|
| **Gemelo Digital** | Motor asíncrono (TwinEngine) que simula el ciclo de vida completo de cada incidente: asignación, routing, movimiento en tiempo real, llegada, atención y resolución. Tick de 1 500 ms. |
| **Routing Real** | Integración con OSRM (Open Source Routing Machine) para rutas reales por calles de Madrid. 2 intentos (8 s / 12 s timeout), caché de 200 rutas, hasta 250 waypoints. Fallback multi-vuelta determinista cuando OSRM no responde. |
| **IA Integrada** | 10 módulos 100 % locales (scikit-learn): clasificación de severidad, predicción de demanda, ETA, detección de anomalías, mantenimiento predictivo, análisis de visión, asistente conversacional, integración de tráfico, motor de recomendaciones, optimización de asignación. Sin dependencias de APIs externas (sin OpenAI, sin cloud ML). |
| **Anonimización RGPD** | Pipeline automático de anonimización (supresión + generalización + perturbación de coordenadas) para datos de pacientes, cumpliendo el Reglamento General de Protección de Datos. |
| **Blockchain BSV** | Notarización on-chain de registros de auditoría mediante árboles Merkle y difusión ARC API. Scheduler automático cada 30 minutos (configurable). Fallback a ledger JSONL local cuando el nodo está offline. |
| **Ciberseguridad** | Rate limiting en 5 niveles, protección brute-force (5 intentos / 10 min lockout), escaneo de inputs (SQLi, XSS, path traversal), CSRF, JWT blacklist + sesiones activas, firewall de IPs, cifrado AES-256-GCM en campos PII, HIBP breach check, detección de anomalías por IP y horario, security score 0-100. |
| **Monitorización** | Prometheus + Alertmanager con métricas HTTP (requests, latencia, conexiones DB) y 4 reglas de alerta. |
| **RBAC** | 4 roles: ADMIN, OPERATOR, DOCTOR, VIEWER, con 22 permisos granulares controlados por FastAPI Depends(). |

## 1.2 Métricas del proyecto

| Métrica | Valor |
|---|---|
| Endpoints API REST | 134 |
| Endpoint WebSocket | 1 (/ws/live) |
| Routers API registrados | 21 |
| Páginas frontend | 15 |
| Componentes React standalone | 6 |
| Componentes Dashboard | 13 |
| Custom hooks React | 5 |
| Utilidades frontend | 3 |
| Modelos SQLAlchemy (tablas) | 18 |
| Módulos de IA | 10 |
| Módulos blockchain | 6 |
| Archivos CSS | 18+ |
| Dependencias Python | 26 principales |
| Dependencias npm | 24 (13 prod + 11 dev) |
| Servicios Docker | 6 |
| Suites de tests automatizados | 13 (72+ tests) |
| Score de seguridad | 8.5 / 10 |

---

# 2. Visión General del Sistema

## 2.1 Problema que resuelve

Los Servicios de Emergencias Médicas enfrentan desafíos operativos críticos que impactan directamente en la supervivencia de los pacientes:

| Problema | Impacto |
|---|---|
| **Asignación manual de recursos** | No considera tráfico, especialización del vehículo, carga hospitalaria ni historial del paciente. Tiempos de respuesta superiores a los 8 min (SAMUR urbano) o 15 min (extrarradio). |
| **Falta de visibilidad unificada** | Los gestores operan con información fragmentada: flota en un sistema, hospitales en otro, incidentes en papel o radio. |
| **Ausencia de predicción** | Sin modelos de demanda, los recursos no se preposicionan en zonas de mayor probabilidad de incidentes. |
| **Auditoría insuficiente** | Las decisiones operativas no quedan registradas de forma inmutable, dificultando la mejora continua y el cumplimiento legal. |
| **Seguridad limitada** | Los sistemas heredados carecen de protección activa frente a amenazas modernas (brute force, inyección, exfiltración de datos de pacientes). |

## 2.2 Solución KAIROS CDS

KAIROS CDS aborda cada problema con un enfoque de sistema integrado:

1. **Gemelo Digital con IA**: El TwinEngine replica el estado operativo en tiempo real. La IA asigna vehículos y hospitales considerando distancia, tipo de vehículo, severidad del incidente, carga hospitalaria y condiciones de tráfico.
2. **Dashboard unificado**: Mapa interactivo Leaflet con capas GIS, rutas en tiempo real, heatmaps de severidad, estado de toda la flota e indicadores hospitalarios — todo en una sola pantalla.
3. **Predicción de demanda**: El módulo de predicción de demanda anticipa zonas de alta incidencia por franja horaria y día de la semana, permitiendo preposicionamiento preventivo.
4. **Blockchain BSV**: Cada acción operativa relevante queda notarizada en la blockchain BSV mediante árboles Merkle, garantizando inmutabilidad legal.
5. **Ciberseguridad proactiva**: Middleware de seguridad activa que detecta y bloquea ataques en tiempo real, con panel visual de amenazas, eventos de seguridad y herramientas de análisis.

## 2.3 Flujo operativo principal

```
Incidente creado (manual por operador / automático por generador)
        │
        ▼
IA clasifica severidad (LOW / MEDIUM / HIGH / CRITICAL)
        │
        ▼
TwinEngine asigna vehículo IDLE más próximo + hospital más cercano
        │
        ▼
OSRM calcula ruta real por calles (ambulancia → incidente → hospital)
        │
        ▼
Vehículo EN_ROUTE: mueve por waypoints reales en cada tick (1 500 ms)
        │
        ▼
Llegada a incidente → fase AT_INCIDENT (~18 s de atención en escena)
        │
        ▼
Traslado a hospital → TO_HOSPITAL → llegada detectada por posición + progreso
        │
        ▼
Resolución: hospital actualiza carga, se crea PCR + PatientTracking
Vehículo vuelve a IDLE
        │
        ▼
Auditoría registrada → Merkle batch → BSV blockchain (cada 30 min)
```

## 2.4 Contexto geográfico

El sistema está preconfigurado para operar en **Madrid y área metropolitana**, con:
- Coordenadas bounding box: 40.28°N–40.65°N / 3.52°W–3.92°W
- 8 vehículos iniciales con base en ubicaciones reales de la Comunidad de Madrid
- 6 hospitales reales: La Paz, Gregorio Marañón, 12 de Octubre, La Princesa, Ramón y Cajal, Clínico San Carlos
- 8 gasolineras (Repsol, Cepsa, BP, etc.)
- 12 ubicaciones DEA (desfibriladores) en transporte público, espacios públicos y privados
- 7 recursos multi-agencia: Bomberos, Policía Nacional, Protección Civil, Guardia Civil, Cruz Roja

---

# 3. Arquitectura de Software

## 3.1 Diagrama de arquitectura de alto nivel

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         KAIROS CDS v1.0.0                                    │
├──────────────────────┬───────────────────────────┬──────────────────────────-┤
│  CAPA DE PRESENTACIÓN│  CAPA DE DOMINIO          │  INFRAESTRUCTURA          │
│                      │                           │                           │
│  React 19 + Vite 7   │  FastAPI 0.115 (ASGI)    │  PostgreSQL 16 + PostGIS  │
│  15 páginas          │  SQLAlchemy 2.0           │  Redis 7-alpine           │
│  13 comp. dashboard  │  Pydantic v2              │  Prometheus + Alertmanager│
│  6 comp. standalone  │  uvicorn                  │  BSV Blockchain (mainnet) │
│  5 hooks custom      │                           │  OSRM (routing público)   │
│  3 utilidades        │  21 routers / 134 endpoints│                          │
│  Leaflet 1.9 (maps)  │  TwinEngine (async loop)  │  Docker Compose           │
│  Recharts (charts)   │  10 módulos IA (sklearn)  │  6 servicios              │
│  lucide-react (icons)│  Cybersecurity middleware │  4 volúmenes persistentes │
│  WebSocket + polling │  Blockchain BSV adapter   │                           │
│                      │  Blockchain batch scheduler│                          │
└──────────────────────┴───────────────────────────┴───────────────────────────┘
```

## 3.2 Patrones de diseño aplicados

| Patrón | Dónde se aplica |
|---|---|
| **Repository Pattern** | `storage/repos/audit_repo.py`, `vehicles_repo.py`, `incidents_repo.py` — abstracción completa de la capa de persistencia |
| **Dependency Injection** | FastAPI `Depends()` para sesiones DB, autenticación JWT, verificación de roles y permisos |
| **Observer / Pub-Sub** | WebSocket broadcast + TwinEngine publica cambios de estado que el frontend consume vía polling y WS |
| **Strategy Pattern** | Los 10 módulos IA son intercambiables; el router de IA selecciona la estrategia correcta por tipo de consulta |
| **Middleware Chain** | Pila: CORS → SecurityMiddleware → SecurityHeadersMiddleware → MetricsMiddleware → Routers |
| **Event Sourcing** | Auditoría completa con hash-chain: cada log referencia el anterior, garantizando integridad secuencial |
| **Digital Twin** | Réplica virtual del estado operativo completo con bucle asíncrono (TwinEngine.run()) |
| **Cache-Aside** | Caché en memoria para `/api/live` (TTL 2 s), rutas OSRM (LRU 200 entradas), hospitales (TTL 10 ticks) |

## 3.3 Capas de la aplicación

```
┌────────────────────────────────────────────────┐
│  PRESENTACIÓN  (React 19 + Vite)               │
│  Páginas, componentes, hooks, utilidades        │
│  Leaflet maps + Recharts + lucide-react         │
├────────────────────────────────────────────────┤
│  TRANSPORTE  (FastAPI + WebSocket)             │
│  21 routers, validación Pydantic, JWT auth      │
│  Middleware: CORS, Security, Metrics            │
├────────────────────────────────────────────────┤
│  DOMINIO  (core/)                              │
│  TwinEngine, 10 módulos IA, Blockchain adapter  │
│  Cybersecurity, Anonymizer, Routing (OSRM)      │
│  Redis client, Metrics (Prometheus)             │
├────────────────────────────────────────────────┤
│  PERSISTENCIA  (storage/)                       │
│  SQLAlchemy 2.0, 18 modelos, Repos pattern      │
│  PostgreSQL 16 + PostGIS                        │
├────────────────────────────────────────────────┤
│  INFRAESTRUCTURA  (Docker)                     │
│  PostgreSQL, Redis, Prometheus, Alertmanager    │
│  OSRM (API pública externa)                     │
└────────────────────────────────────────────────┘
```

## 3.4 Flujo de una petición HTTP autenticada

```
Cliente HTTP/Browser
    │  Authorization: Bearer <JWT>
    ▼
CORS Middleware (preflight OPTIONS resuelto aquí)
    ▼
SecurityMiddleware
    ├─ Verifica IP no bloqueada
    ├─ Rate limiting por IP + ruta
    ├─ Detección brute-force en /auth/login
    └─ Escaneo de payload (SQLi / XSS / path traversal)
    ▼
SecurityHeadersMiddleware
    └─ Inyecta 11 cabeceras de seguridad en respuesta
    ▼
MetricsMiddleware
    └─ Registra latencia y contador en Prometheus
    ▼
FastAPI Router
    ├─ Depends(get_db) — sesión SQLAlchemy
    ├─ Depends(get_current_user) — validación JWT
    └─ Depends(require_role(...)) — verificación RBAC
    ▼
Handler Function → Lógica de negocio
    ▼
Repository → SQLAlchemy → PostgreSQL
    ▼
Response JSON {data, error, status}
```

---

# 4. Stack Tecnológico

## 4.1 Backend

| Tecnología | Versión | Función |
|---|---|---|
| Python | 3.10+ | Lenguaje principal del backend |
| FastAPI | 0.115 | Framework web ASGI con soporte nativo para async, Pydantic v2 y WebSockets |
| uvicorn | latest | Servidor ASGI de alto rendimiento con hot-reload en desarrollo |
| SQLAlchemy | 2.0 | ORM relacional con soporte async; mapeo de 18 modelos |
| Pydantic | v2 | Validación de datos y serialización de esquemas en todos los endpoints |
| psycopg2-binary | latest | Driver PostgreSQL para SQLAlchemy |
| python-jose | latest | Generación y validación de tokens JWT (HS256) |
| passlib + bcrypt | latest | Hashing de contraseñas con BCrypt |
| redis-py | latest | Cliente Redis para sesiones, rate limiting y pub/sub |
| scikit-learn | latest | Motor de los 10 módulos de IA (100 % local) |
| joblib | latest | Serialización y carga de modelos sklearn entrenados |
| numpy | latest | Operaciones matemáticas para modelos IA |
| python-dotenv | latest | Carga de variables de entorno desde `.env` |
| cryptography | latest | Cifrado AES-256-GCM de campos PII + generación de claves |
| prometheus-client | latest | Exposición de métricas en `/metrics` para Prometheus |
| requests | latest | Cliente HTTP para llamadas externas (HIBP, BSV ARC API) |
| bsvlib | latest | Generación de transacciones BSV, wallets y OP_RETURN |

## 4.2 Frontend

| Tecnología | Versión | Función |
|---|---|---|
| React | 19 | Framework SPA con hooks funcionales y Context API |
| Vite | 7 | Bundler y servidor de desarrollo con HMR instantáneo |
| React Router DOM | 6 | Enrutamiento SPA con rutas protegidas por rol (RoleRoute) |
| Leaflet | 1.9 | Mapas interactivos con capas GIS, markers personalizados y popups |
| react-leaflet | latest | Wrapper React para Leaflet |
| Recharts | 2.x | Gráficos de KPIs, analítica y líneas de tiempo de seguridad |
| lucide-react | latest | Biblioteca de iconos SVG |
| axios | latest | Cliente HTTP para comunicación con el backend |

## 4.3 Infraestructura

| Servicio | Imagen / Tecnología | Función |
|---|---|---|
| PostgreSQL | postgis/postgis:16-3.4 | Base de datos relacional principal con extensión PostGIS para datos geoespaciales |
| Redis | redis:7-alpine | Caché de sesiones, pub/sub para eventos en tiempo real, rate limiting |
| Prometheus | prom/prometheus:latest | Recolección de métricas del backend cada 15 s |
| Alertmanager | prom/alertmanager:latest | Gestión de alertas con reglas configurables (4 reglas activas) |
| OSRM | router.project-osrm.org (API pública) | Cálculo de rutas reales por calles de Madrid |
| BSV | Mainnet vía ARC API (gorillapool.io) | Blockchain para notarización de auditoría |

---

# 5. Infraestructura y Despliegue

## 5.1 Docker Compose — Servicios

El sistema completo se despliega con un único `docker compose up`. El fichero `docker-compose.yml` define 6 servicios con healthchecks, dependencias ordenadas y volúmenes persistentes.

### Servicio: db

```yaml
image: postgis/postgis:16-3.4
ports: 55432:5432
volumes: twin_db:/var/lib/postgresql/data
healthcheck:
  test: pg_isready -U twin
  interval: 10s / timeout: 5s / retries: 5
```

Base de datos principal. La extensión PostGIS permite almacenar y consultar datos geoespaciales (coordenadas de vehículos, incidentes, hospitales). El puerto externo 55432 evita conflictos con instalaciones locales de PostgreSQL.

### Servicio: redis

```yaml
image: redis:7-alpine
ports: 6379:6379
volumes: redis_data:/data
healthcheck:
  test: redis-cli ping
  interval: 10s / timeout: 3s / retries: 5
```

Usado para: almacenamiento de sesiones JWT activas, rate limiting por IP, pub/sub de eventos en tiempo real.

### Servicio: backend

```yaml
build: ./backend
ports: 5001:5001
env_file: ./backend/.env
environment:
  PORT: 5001
  DATABASE_URL: postgresql+psycopg2://twin:twin@db:5432/twin
  REDIS_HOST: redis / REDIS_PORT: 6379
  CORS_ORIGINS: http://localhost:5173,...
depends_on: db (healthy), redis (healthy)
healthcheck:
  test: python -c 'urllib.request.urlopen("http://localhost:5001/health")'
  interval: 15s / timeout: 5s / retries: 5 / start_period: 20s
restart: unless-stopped
```

### Servicio: frontend

```yaml
build:
  context: ./frontend
  args:
    VITE_API_URL: http://localhost:5001
ports: 5173:5173
depends_on: backend (healthy)
restart: unless-stopped
```

El frontend se construye como SPA estática dentro del contenedor usando Vite y se sirve en producción.

### Servicios: prometheus + alertmanager

```yaml
prometheus:
  image: prom/prometheus:latest
  ports: 9090:9090
  volumes:
    - ./monitoring/prometheus.yml
    - ./monitoring/alert.rules.yml
  depends_on: alertmanager

alertmanager:
  image: prom/alertmanager:latest
  ports: 9093:9093
  volumes:
    - ./monitoring/alertmanager.yml
```

## 5.2 Puertos y URLs de acceso

| Servicio | Puerto interno | Puerto externo | URL |
|---|---|---|---|
| Frontend | 5173 | 5173 | http://localhost:5173 |
| Backend API | 5001 | 5001 | http://localhost:5001 |
| API Docs (Swagger) | 5001 | 5001 | http://localhost:5001/docs |
| PostgreSQL | 5432 | 55432 | localhost:55432 |
| Redis | 6379 | 6379 | localhost:6379 |
| Prometheus | 9090 | 9090 | http://localhost:9090 |
| Alertmanager | 9093 | 9093 | http://localhost:9093 |

## 5.3 Volúmenes persistentes

| Volumen | Contenido |
|---|---|
| `twin_db` | Datos completos de PostgreSQL (esquemas, registros, PostGIS) |
| `redis_data` | Datos de Redis (sesiones, listas) |
| `prometheus_data` | Series temporales de Prometheus (métricas históricas) |
| `alertmanager_data` | Estado de alertas de Alertmanager |

## 5.4 Script de arranque unificado (run_all.py)

El script `run_all.py` es el único punto de entrada para operar el sistema. Gestiona todo el ciclo de vida de forma idempotente:

```
python3 run_all.py              # Arranca preservando datos existentes
python3 run_all.py --reset      # Borrado completo + confirmación interactiva
python3 run_all.py --logs       # Muestra logs en tiempo real de todos los servicios
python3 run_all.py --stop       # Detiene todos los servicios
python3 run_all.py --security   # Ejecuta escaneo de seguridad con cyber-claude
```

El script verifica Docker disponible, levanta los contenedores con `docker compose up -d`, espera el healthcheck del backend (hasta 30 reintentos × 2 s = 60 s máximo), llama al endpoint de inicialización para sembrar datos si no existen, e imprime un resumen con todas las URLs de acceso.

**Idempotencia:** Si los usuarios ya existen, se omite la creación. Si la flota ya existe (count > 0), se omite el seed. Solo se carga la información faltante. La generación automática de incidentes se activa automáticamente si no está ya corriendo.

---

# 6. Base de Datos — Modelo Relacional

## 6.1 Tablas principales

El esquema completo se gestiona con SQLAlchemy `Base.metadata.create_all()` al arranque del backend. Las tablas se crean automáticamente si no existen.

| Tabla | Modelo SQLAlchemy | Descripción |
|---|---|---|
| `vehicles` | `Vehicle` | Flota de ambulancias: posición GPS, estado, combustible, tipo, subtipo |
| `incidents` | `IncidentSQL` | Incidentes: coordenadas, severidad, tipo, estado del ciclo de vida, datos de ruta |
| `hospitals` | `Hospital` | Hospitales: coordenadas, capacidad, carga actual, especialidades |
| `users` | `User` | Usuarios del sistema: credenciales hasheadas, rol, estado |
| `audit_logs` | `AuditLog` | Log de auditoría con hash chain: acción, recurso, usuario, hash SHA-256 |
| `merkle_batches` | `MerkleBatch` | Lotes blockchain: Merkle root, tx_id BSV, estado (pending/on_chain) |
| `gas_stations` | `GasStation` | Gasolineras: posición, marca, precio, horario, tipos de combustible |
| `dea_locations` | `DEALocation` | Desfibriladores: posición, disponibilidad, tipo de ubicación |
| `agency_resources` | `AgencyResource` | Recursos multi-agencia: Bomberos, Policía, Protección Civil, etc. |
| `crews` | `Crew` | Tripulaciones: miembros, turno (Día/Noche/24h), vehículo asignado |
| `patient_care_reports` | `PatientCareReport` | Informes ePCR: paciente, queja principal, hospital receptor |
| `patient_trackings` | `PatientTracking` | Seguimiento de fase del paciente: AT_SCENE, AT_HOSPITAL_ER, etc. |
| `weather_conditions` | `WeatherCondition` | Condiciones meteorológicas: temperatura, multiplicador ETA, nivel de alerta |
| `gis_pois` | `GISPOI` | Puntos de interés GIS: colegios, zonas HAZMAT, estaciones de metro, etc. |
| `events` | `Event` | Eventos operativos: tipo, severidad, descripción, timestamp |
| `alerts` | `Alert` | Alertas del sistema: fuente, mensaje, estado (activa/resuelta) |
| `mci_incidents` | `MCIIncident` | Incidentes de Múltiples Víctimas con protocolo START de triaje |
| `resource_assignments` | `ResourceAssignment` | Asignación de recursos multi-agencia a incidentes |

## 6.2 Modelo Vehicle (detalle)

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | String PK | Identificador único (ej: AMB-001) |
| `type` | String | Tipo principal (AMBULANCE, MCI_UNIT, etc.) |
| `subtype` | String | Subtipo operativo: SVB, SVA, VIR, VAMM, SAMU |
| `status` | String | Estado actual: IDLE, EN_ROUTE, ON_SCENE, MAINTENANCE |
| `lat` / `lon` | Float | Posición GPS actual |
| `speed` | Float | Velocidad actual normalizada (0.0 = parado, 1.0 = en marcha) |
| `fuel` | Float | Nivel de combustible actual (litros) |
| `tank_capacity` | Float | Capacidad del depósito (litros, default 80 L) |
| `trust_score` | Float | Puntuación de fiabilidad del vehículo (0-100) |
| `route_progress` | Float | Progreso en la ruta actual (0.0 = inicio, 1.0 = destino) |
| `enabled` | Boolean | Si el vehículo participa en la simulación |

## 6.3 Modelo IncidentSQL (detalle)

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | String PK | Identificador único (ej: INC-001) |
| `lat` / `lon` | Float | Coordenadas GPS del incidente |
| `severity` | String | Severidad: LOW, MEDIUM, HIGH, CRITICAL |
| `incident_type` | String | Tipo de incidente (14 tipos disponibles) |
| `status` | String | Estado del ciclo: OPEN, ASSIGNED, EN_ROUTE, ARRIVED, RESOLVED |
| `route_phase` | String | Fase de ruta detallada: TO_INCIDENT, AT_INCIDENT, TO_HOSPITAL, COMPLETED |
| `assigned_vehicle_id` | String FK | Vehículo asignado (null = sin asignar) |
| `assigned_hospital_id` | String FK | Hospital de destino |
| `route_data` | Text | JSON con geometría de ruta, distancia, duración, índice de waypoint de incidente |
| `description` | String | Descripción textual generada por IA |
| `address` | String | Dirección aproximada |
| `city` | String | Ciudad (usado para filtrado por ciudad) |
| `province` | String | Provincia |
| `affected_count` | Integer | Número de personas afectadas |
| `created_at` | DateTime | Timestamp de creación |
| `resolved_at` | DateTime | Timestamp de resolución |

---

# 7. Backend — FastAPI

## 7.1 Punto de entrada y ciclo de vida

El fichero `backend/app/main.py` define la aplicación FastAPI con el siguiente ciclo de vida (lifespan):

**Startup:**
1. `Base.metadata.create_all(bind=engine)` — crea tablas si no existen
2. `asyncio.create_task(twin_engine.run())` — arranca el TwinEngine
3. `asyncio.create_task(_blockchain_batch_scheduler())` — arranca el scheduler blockchain (intervalo: `BLOCKCHAIN_BATCH_INTERVAL_MIN`, default 30 min)

**Shutdown:**
1. `twin_engine.running = False` — señala parada al bucle del twin
2. Cancela las tasks asyncio del twin y del blockchain scheduler

## 7.2 Pila de middleware (orden de aplicación)

FastAPI aplica los middlewares en orden inverso al de registro (el último añadido es el primero en ejecutarse):

```
Orden de ejecución en petición entrante:
1. CORSMiddleware         — resolución de preflight OPTIONS, cabeceras CORS
2. SecurityMiddleware     — rate limit, brute-force, input scan, IP block
3. SecurityHeadersMiddleware — inyección de 11 cabeceras de seguridad
4. MetricsMiddleware      — contadores Prometheus (requests_total, latencia)
5. Router / Handler       — lógica de negocio
```

## 7.3 Endpoints globales en main.py

| Método | Path | Descripción |
|---|---|---|
| GET | `/` | Root: service info (nombre, versión, status) |
| GET | `/metrics` | Endpoint Prometheus: datos de métricas en formato text/plain |
| GET | `/api/cities` | Lista ciudades distintas presentes en incidentes y hospitales |
| GET | `/api/live` | Datos en tiempo real: vehículos, incidentes activos, métricas de flota, gasolineras, hospitales, clima. **Caché en memoria de 2 s.** |
| WS | `/ws/live` | WebSocket: push de actualizaciones del TwinEngine a todos los clientes conectados |

## 7.4 Caché de /api/live

El endpoint `/api/live` es el más consultado del sistema (polling cada 5 s desde el frontend). Para evitar 7 consultas DB por cada llamada, implementa una caché en memoria:

```python
_live_cache = {"data": None, "ts": 0, "city": None}
_LIVE_CACHE_TTL = 2.0  # segundos
```

La caché es invalidada si han pasado más de 2 segundos o si el filtro de ciudad cambia. Esto reduce la carga de la base de datos en un ~80% bajo uso normal.

## 7.5 Listado de routers registrados

| Router | Prefijo | Descripción |
|---|---|---|
| health_router | /health | Estado del sistema y componentes |
| auth_router | /api/auth | Login, registro, tokens JWT |
| fleet_router | /api/fleet | CRUD vehículos, estado, combustible |
| events_router | /api/events | Eventos operativos |
| analytics_router | /api/analytics | Analítica de operaciones |
| alerts_router | /api/alerts | Alertas del sistema |
| hospitals_router | /api/hospitals | CRUD hospitales, ocupación |
| assignments_router | /api/assignments | Asignación manual de vehículos a incidentes |
| ai_router | /api/ai | Todos los módulos IA |
| audit_router | /api/audit | Log de auditoría |
| blockchain_router | /api/blockchain | Notarización blockchain |
| gas_stations_router | /api/gas-stations | CRUD gasolineras |
| simulation_router | /simulation | Control de simulación y auto-generación |
| kpis_router | /api/kpis | KPIs operativos |
| crews_router | /api/crews | Gestión de tripulaciones |
| epcr_router | /api/epcr | Informes ePCR |
| mci_router | /api/mci | Incidentes de Múltiples Víctimas |
| resources_router | /api/resources | Recursos multi-agencia |
| chat_router | /api/chat | Asistente conversacional |
| security_router | /api/security | Panel de ciberseguridad |
| digital_twin_router | /api/digital-twin | Telemetría del gemelo digital |

---

# 8. Motor de Gemelo Digital (TwinEngine)

## 8.1 Descripción general

El TwinEngine (`backend/app/core/twin_engine.py`) es el núcleo del sistema. Es un bucle asíncrono que se ejecuta en un task asyncio independiente, actualizando el estado de toda la operación cada **1 500 ms** (configurable vía `TICK_MS`).

## 8.2 Inicialización y limpieza de arranque

Al iniciarse, el TwinEngine ejecuta una **limpieza de arranque** para garantizar consistencia del estado:

```python
# Resuelve todos los incidentes OPEN/ASSIGNED que quedaron de sesiones anteriores
_stale = db.query(IncidentSQL).filter(IncidentSQL.status.in_(["OPEN", "ASSIGNED"])).all()
for inc in _stale:
    inc.status = "RESOLVED"

# Resetea vehículos atascados a IDLE
_stuck_vehicles = db.query(Vehicle).filter(Vehicle.status != "IDLE").all()
for v in _stuck_vehicles:
    v.status = "IDLE"
    v.speed = 0.0
    v.route_progress = 0.0
```

Esto evita que reinicios del backend dejen el sistema en un estado inconsistente.

## 8.3 Ciclo principal por tick

Cada tick (1 500 ms) el TwinEngine ejecuta las siguientes fases en orden:

### Fase 1: Carga de datos

```python
vehicles = VehicleRepo.list_enabled(db)          # Solo vehículos habilitados
incidents = IncidentsRepo.list_open(db)           # Solo incidentes no RESOLVED
vehicle_map = {v.id: v for v in vehicles}         # Dict O(1) para lookups
```

### Fase 2: Refresco de caché de hospitales

La caché de hospitales se refresca cada 10 ticks (~15 s) para evitar consultas DB repetitivas:

```python
self._hospital_cache_tick += 1
if self._hospital_cache_tick >= 10 or not self._hospital_cache:
    self._refresh_hospitals(db)
```

### Fase 3: Asignación de incidentes OPEN

Para cada incidente sin vehículo asignado:

1. Busca vehículos `IDLE` habilitados
2. Selecciona el más próximo al incidente (distancia euclidiana sobre lat/lon — suficiente para comparación relativa)
3. Encuentra el hospital más próximo al incidente usando la caché
4. Calcula ruta OSRM (ambulancia → incidente → hospital)
5. Almacena `route_data` como JSON: geometría, distancia_km, duración, índice del waypoint de llegada al incidente

### Fase 4: Movimiento de vehículos

Delegado a `MockSimAdapter.step()` que actualiza la posición GPS de cada vehículo activo según su ruta y velocidad normalizadas.

### Fase 5: Detección de llegadas y transiciones de fase

Para cada incidente en fase `ASSIGNED`:

| Fase actual | Condición de transición | Acción |
|---|---|---|
| `TO_INCIDENT` | `v.route_progress >= inc_progress - 0.02` O `dist(v, inc) <= 33m` | Transición a `AT_INCIDENT`, velocidad = 0 |
| `AT_INCIDENT` | Contador >= 12 ticks (~18 s) | Transición a `TO_HOSPITAL` si hay hospital asignado; si no, RESOLVED |
| `TO_HOSPITAL` | `v.route_progress >= 0.95` O `dist(v, hosp) <= 33m` | Llama a `_resolve_incident()` |

### Fase 6: Resolución de incidentes

`_resolve_incident()` ejecuta:
1. Marca incidente como `RESOLVED`, `route_phase = COMPLETED`
2. Libera el vehículo (status `IDLE`, speed 0, progress 0)
3. Reduce la carga del hospital (`current_load -= affected_count`)
4. Crea registro `PatientCareReport` (PCR) si no existe
5. Crea registro `PatientTracking` con fase `AT_HOSPITAL_ER` o `DISCHARGED`
6. Incrementa métrica Prometheus `incidents_resolved_total`

## 8.4 Métricas del TwinEngine

| Métrica Prometheus | Tipo | Descripción |
|---|---|---|
| `available_vehicles_count` | Gauge | Número de vehículos IDLE disponibles |
| `incidents_resolved_total` | Counter | Incidentes resueltos acumulados desde el inicio |
| `http_requests_total` | Counter | Peticiones HTTP por método, endpoint y código de estado |
| `http_request_duration_seconds` | Histogram | Latencia HTTP por método y endpoint |
| `database_connections_active` | Gauge | Conexiones DB activas (0 o 1 según estado del engine) |

## 8.5 Umbral de llegada (ARRIVAL_DIST2)

```python
ARRIVAL_DIST2 = 0.0003 ** 2  # ~33 metros de radio de llegada
```

Este umbral doble (distancia geoespacial + progreso de ruta) garantiza que el sistema detecte la llegada incluso si hay pequeñas desviaciones en los waypoints OSRM.

---

# 9. Sistema de Routing (OSRM)

## 9.1 Estrategia de routing

KAIROS CDS utiliza **OSRM (Open Source Routing Machine)** como motor de routing primario para calcular rutas reales por las calles de Madrid. Si OSRM no responde, el sistema usa un algoritmo de fallback interno determinista.

## 9.2 Función _osrm_route

```python
def _osrm_route(start_lat, start_lon, end_lat, end_lon, max_points=250):
    url = "http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"

    for attempt in range(2):                  # 2 intentos
        timeout = 8 if attempt == 0 else 12   # 8 s primer intento, 12 s segundo
        try:
            resp = urllib.request.urlopen(req, timeout=timeout)
            coords = data["routes"][0]["geometry"]["coordinates"]  # [lon, lat] → [lat, lon]
            # Downsample si > 250 puntos (preserva detalle de calles)
            result = (waypoints, distance_km)
            _osrm_cache[cache_key] = result
            return result
        except Exception:
            if attempt == 0: logger.warning("Retrying...")
            else: return None, None
```

## 9.3 Caché de rutas (LRU)

Las rutas calculadas se almacenan en un diccionario en memoria:

```python
_osrm_cache: dict[str, tuple] = {}
_OSRM_CACHE_MAX = 200  # máximo de entradas
```

**Clave de caché:** Coordenadas redondeadas a 4 decimales (~11 m de precisión). Dos rutas con origen/destino dentro de ~11 m reutilizan la misma caché.

**Política de evicción:** Cuando se alcanza el límite de 200 entradas, se elimina el 25% más antiguo (primeras 50 claves en orden de inserción).

## 9.4 Algoritmo de fallback (_build_street_route)

Cuando OSRM falla (sin conexión, timeout, sin ruta encontrada), el sistema genera una ruta simulada que imita la navegación por calles de Madrid:

```python
def _build_street_route(start_lat, start_lon, end_lat, end_lon, n_points=20):
    # 2-3 waypoints intermedios con offset perpendicular a la línea recta
    # Offset máximo en el punto medio (simula rodear manzanas)
    # Semilla determinista: int((lat1 + lat2) * 10000)
    # Para rutas cortas (<0.02°): 2 giros; para largas: 3 giros
    # Resultado: 20 puntos interpolados entre waypoints
```

La distancia del fallback se calcula como Haversine × 1.4 (40% extra para simular el incremento real por rodeo de calles).

## 9.5 Ruta completa ambulancia-incidente-hospital

La ruta almacenada en `route_data` combina dos segmentos:

```
Segmento A-B: ambulancia → incidente  (OSRM o fallback)
Segmento B-C: incidente → hospital    (OSRM o fallback)

route_data = {
  "geometry": [waypoints A-B + waypoints B-C[1:]],  # sin duplicar B
  "distance_km": dist_AB + dist_BC,
  "duration_minutes": total_km / 0.8,               # ~48 km/h velocidad media
  "incident_waypoint_idx": len(waypoints_AB) - 1,   # índice de llegada al incidente
  "hospital_id": "HOSP-001"
}
```

El `incident_waypoint_idx` permite al TwinEngine detectar con precisión cuándo el vehículo ha llegado al incidente (no al hospital) dentro de la ruta completa.

---

# 10. Módulos de Inteligencia Artificial

Todos los módulos de IA se implementan en Python con **scikit-learn** y se ejecutan completamente en local. No hay dependencias de APIs externas de IA (sin OpenAI, sin Anthropic, sin cloud ML). Los modelos se entrenan con datasets sintéticos representativos de operaciones SEM y se guardan como archivos `.joblib`.

## 10.1 Catálogo de módulos

| # | Módulo | Archivo | Algoritmo Principal | Entrada → Salida |
|---|---|---|---|---|
| 1 | **Clasificador de Severidad** | `ai_severity_classifier.py` | TF-IDF + RandomForestClassifier | Descripción textual → LOW / MEDIUM / HIGH / CRITICAL |
| 2 | **Asistente Conversacional** | `ai_conversational_assistant.py` | TF-IDF + LogisticRegression | Texto libre del operador → Intención + respuesta |
| 3 | **Analizador de Visión** | `ai_vision_analyzer.py` | TF-IDF + LinearSVC | Descripción de escena → Categoría de emergencia visual |
| 4 | **Predictor de Demanda** | `ai_demand_prediction.py` | RandomForestRegressor | Zona + hora + día_semana → Demanda esperada (incidentes/h) |
| 5 | **Predictor de ETA** | `ai_eta_predictor.py` | GradientBoostingRegressor | Distancia + tráfico + tipo_vehículo → ETA (minutos) |
| 6 | **Detector de Anomalías** | `ai_anomaly_detector.py` | IsolationForest | Métricas de vehículo/incidente → Normal / Anómalo |
| 7 | **Predictor de Mantenimiento** | `ai_maintenance_predictor.py` | Reglas basadas en umbrales | Kilometraje + horas + fuel → Necesidad de mantenimiento |
| 8 | **Integración de Tráfico** | `ai_traffic_integration.py` | Reglas basadas en hora y día | Hora + día_semana + zona → Multiplicador de ETA (1.0 - 2.5x) |
| 9 | **Motor de Recomendaciones** | `ai_recommendation_system.py` | Filtrado basado en perfil | Rol del usuario + historial → Sugerencias de acción |
| 10 | **Optimizador de Asignación** | `ai_assignment.py` | Puntuación multi-criterio | Candidatos (vehículo, incidente) → Ranking ordenado |

## 10.2 Detalle: Clasificador de Severidad

El módulo más crítico del sistema. Clasifica la gravedad de un incidente a partir de su descripción textual.

**Pipeline:**
```
Texto → TfidfVectorizer(ngram_range=(1,2), max_features=5000)
     → RandomForestClassifier(n_estimators=100, class_weight='balanced')
     → Etiqueta: LOW | MEDIUM | HIGH | CRITICAL
```

**Dataset de entrenamiento:** ~500 ejemplos sintéticos por clase (2 000 total) cubriendo los 14 tipos de incidente en español, con variaciones de redacción para robustez.

**Probabilidades:** El módulo devuelve tanto la etiqueta como las probabilidades de cada clase, permitiendo mostrar confianza al operador.

## 10.3 Detalle: Optimizador de Asignación

Cuando el TwinEngine necesita asignar un vehículo a un incidente, el optimizador puntúa cada candidato considerando:

| Criterio | Peso | Descripción |
|---|---|---|
| Distancia | 40% | Inverso de la distancia Haversine vehículo-incidente |
| Tipo de vehículo | 25% | SVA > SVB > VIR para incidentes CRITICAL; VIR > SVB para tráfico |
| Nivel de combustible | 20% | Penaliza vehículos con < 20% de depósito |
| Historial de fiabilidad | 15% | Trust score del vehículo (0-100) |

## 10.4 Entrenamiento de modelos

Los 6 modelos sklearn entrenados se generan con:

```bash
cd backend
python train_all_models.py
```

Los modelos se guardan en `backend/models/` como archivos `.joblib`. Los 4 módulos basados en reglas no requieren entrenamiento.

---

# 11. Sistema de Ciberseguridad

## 11.1 Arquitectura de seguridad

KAIROS CDS implementa una seguridad de defensa en profundidad con múltiples capas. El módulo central es `backend/app/core/cybersecurity.py`.

```
Capa 1: Red          → CORS, TLS (en producción)
Capa 2: Middleware   → Rate limiting, IP blacklist, input scanning
Capa 3: Cabeceras    → 11 security headers HTTP
Capa 4: Autenticación → JWT HS256, bcrypt, HIBP breach check
Capa 5: Autorización → RBAC (4 roles, 22 permisos)
Capa 6: Datos        → AES-256-GCM en campos PII
Capa 7: Auditoría    → Hash chain + blockchain BSV
```

## 11.2 Rate Limiting

Rate limiting por IP + ruta con ventanas de tiempo deslizantes:

| Ruta | Límite | Ventana |
|---|---|---|
| `/api/auth/login` | 5 intentos | 60 s |
| `/api/auth/register` | 3 intentos | 60 s |
| `/api/auth/init-admin` | 2 intentos | 300 s |
| `/api/live` | Sin límite efectivo | — (polling del dashboard excluido) |
| Resto de rutas | 120 peticiones | 60 s |

Cuando se excede el límite, se devuelve HTTP 429 con cabeceras `Retry-After` y `X-RateLimit-*`.

## 11.3 Protección Brute-Force

```python
SECURITY_MAX_LOGIN_ATTEMPTS = 5      # intentos fallidos máximos
SECURITY_LOCKOUT_MINUTES = 10        # duración del bloqueo
```

Tras 5 intentos fallidos de login desde la misma IP en 60 s, la IP queda bloqueada durante 10 minutos. El bloqueo queda registrado en `_brute_force` (dict en memoria) y genera un evento de seguridad `BRUTE_FORCE` con severidad `CRITICAL`.

## 11.4 Escaneo de Inputs

El middleware escanea automáticamente los bodies de peticiones POST/PUT/PATCH buscando:

| Tipo de ataque | Patrones detectados |
|---|---|
| **SQL Injection** | `UNION SELECT`, `DROP TABLE`, `' OR '1'='1`, `; --`, `EXEC(`, `xp_cmdshell` |
| **XSS** | `<script>`, `javascript:`, `onerror=`, `onload=`, `eval(`, `document.cookie` |
| **Path Traversal** | `../`, `..\`, `/etc/passwd`, `C:\Windows`, `%2e%2e%2f` |

Al detectar un patrón malicioso: HTTP 400, evento `SUSPICIOUS_INPUT` con severidad `HIGH`, y logging del payload truncado.

## 11.5 Cabeceras de Seguridad HTTP

`SecurityHeadersMiddleware` inyecta las siguientes 11 cabeceras en cada respuesta:

| Cabecera | Valor | Protección |
|---|---|---|
| `Strict-Transport-Security` | `max-age=63072000; includeSubDomains; preload` | HSTS — fuerza HTTPS |
| `X-Content-Type-Options` | `nosniff` | Previene MIME sniffing |
| `X-Frame-Options` | `DENY` | Previene clickjacking |
| `X-XSS-Protection` | `1; mode=block` | XSS filter legacy |
| `Content-Security-Policy` | `default-src 'self'; script-src 'self' 'unsafe-inline'; ...` | Restringe recursos |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Controla referrer header |
| `Permissions-Policy` | `geolocation=(), camera=(), microphone=()` | Restringe APIs del navegador |
| `Cache-Control` | `no-store, no-cache, must-revalidate` | Evita caché de datos sensibles |
| `Cross-Origin-Opener-Policy` | `same-origin` | Protege contexto de navegación |
| `Cross-Origin-Resource-Policy` | `cross-origin` | Controla carga de recursos cross-origin |
| `X-Request-ID` | UUID generado por petición | Trazabilidad de requests |

## 11.6 Autenticación JWT

```python
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30     # Token expira en 30 minutos
```

- Tokens firmados con `SECRET_KEY` (generada aleatoriamente al inicio si no se configura en `.env`)
- JWT blacklist: tokens revocados en logout se almacenan en Redis con TTL = tiempo de expiración restante
- Sesiones activas: mapa `token_hash → {user, ip, created, last_seen}` con máximo `MAX_SECURITY_EVENTS = 2 000` eventos de seguridad en memoria

## 11.7 Cifrado de campos PII

Los campos de información personal identificable (PII) se cifran en reposo usando AES-256-GCM:

```python
FIELD_ENCRYPTION_KEY = os.getenv("FIELD_ENCRYPTION_KEY", "")
# Generar: python -c "import secrets,base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"
```

El módulo `backend/app/core/encryption.py` implementa:
- **Cifrado:** AES-256-GCM con nonce aleatorio de 12 bytes
- **Descifrado:** Verificación de tag de autenticación (garantía de integridad)
- **Hashing:** PBKDF2-HMAC-SHA256 para contraseñas (via bcrypt)

## 11.8 HIBP — Verificación de contraseñas comprometidas

Al crear o cambiar una contraseña, el sistema consulta la API de **HaveIBeenPwned** usando k-Anonymity (los primeros 5 caracteres del hash SHA-1 se envían; el resto se comprueba localmente), garantizando que la contraseña no aparece en bases de datos de brechas conocidas.

## 11.9 Panel de seguridad (frontend)

La página `SecurityDashboard.jsx` proporciona:

- **Tab Eventos**: Stream en tiempo real de eventos de seguridad (polling 5 s), filtrable por severidad. Incluye timeline visual de distribución horaria por colores.
- **Tab Herramientas**:
  - **Analizador de cabeceras HTTP**: Puntúa cabeceras presentes vs. requeridas (score 0-100, letra A-F)
  - **Escáner de inputs**: Detecta SQLi, XSS, path traversal con detalles del tipo de amenaza
  - **Verificador de contraseñas**: Analiza fortaleza + HIBP breach check con medidor visual
  - **Estado de IPs bloqueadas**: Lista de IPs en blacklist con motivo y timestamp
  - **Sesiones activas**: Vista de tokens JWT activos con IP y última actividad
- **Tab Analítica**: Estadísticas agregadas de amenazas, distribución por tipo y severidad.

---

# 12. Blockchain y Auditoría Inmutable

## 12.1 Arquitectura blockchain

KAIROS CDS implementa un sistema de auditoría notarizada en la **BSV (Bitcoin SV) mainnet**. Cada acción relevante del sistema genera un registro de auditoría que eventualmente se notariza on-chain mediante lotes Merkle.

## 12.2 Módulos blockchain

| Módulo | Archivo | Función |
|---|---|---|
| **AuditLog** | `storage/models_sql.py` | Modelo DB: acción, recurso, usuario, hash SHA-256, referencia al anterior |
| **AuditRepo** | `storage/repos/audit_repo.py` | Creación de logs con hash chain automático |
| **Merkle Tree** | `blockchain/merkle.py` | Construcción de árboles Merkle con SHA-256 |
| **Notarizer** | `blockchain/notarizer.py` | Creación de transacciones BSV con OP_RETURN |
| **Batch Notarizer** | `blockchain/batch_notarizer.py` | Agrupa logs pendientes en un lote Merkle y los notariza on-chain |
| **BSV Adapter** | `blockchain/adapter.py` | Interfaz con ARC API (gorillapool.io) para difusión de transacciones |

## 12.3 Flujo de notarización

```
1. AuditRepo.log() → crea AuditLog con hash SHA-256(acción + recurso + usuario + hash_anterior)
2. Scheduler (cada 30 min): batch_notarizer.create_and_broadcast_batch()
3. Recopila AuditLogs con merkle_batch_id == NULL (pendientes)
4. Construye árbol Merkle con los hashes de todos los logs del lote
5. Crea transacción BSV: OP_RETURN <merkle_root_hex>
6. Difunde vía ARC API (gorillapool.io) → tx_id recibido
7. Actualiza MerkleBatch con tx_id y estado "on_chain"
8. Enlaza todos los AuditLog del lote con el MerkleBatch
```

**Fallback offline:** Si la difusión BSV falla (sin conexión, API caída), el lote se almacena localmente en `backend/data/blockchain_ledger.jsonl` y se reintenta en el siguiente ciclo.

## 12.4 Parámetros blockchain

| Parámetro | Valor | Env var |
|---|---|---|
| Red BSV | mainnet | `BSV_NETWORK=main` |
| ARC API | https://arc.gorillapool.io | `ARC_URL` |
| Verificación | https://api.whatsonchain.com/v1/bsv/main | `WOC_BASE` |
| Intervalo de batch | 30 minutos | `BLOCKCHAIN_BATCH_INTERVAL_MIN` |
| Ledger local fallback | `backend/data/blockchain_ledger.jsonl` | — |

## 12.5 Coste estimado

Con Merkle batching, 1 000 registros de auditoría se notarizan en una única transacción BSV (una transacción OP_RETURN ≈ $0.00001). Coste estimado: **< $0.01/día** para operaciones normales.

## 12.6 Verificación de integridad

El módulo `blockchain/integrity.py` permite verificar que un registro de auditoría concreto pertenece a un lote Merkle on-chain dado, reconstruyendo la Merkle proof.

---

# 13. Frontend — React 19

## 13.1 Estructura de directorios

```
frontend/src/
├── pages/                    # 15 páginas principales
│   ├── Dashboard.jsx         # Mapa principal + KPIs en tiempo real
│   ├── Login.jsx             # Autenticación JWT
│   ├── IncidentList.jsx      # Lista y gestión de incidentes
│   ├── CreateIncident.jsx    # Formulario de creación manual de incidente
│   ├── Analytics.jsx         # Analítica de operaciones y tendencias
│   ├── AuditLog.jsx          # Visualizador del log de auditoría
│   ├── SecurityDashboard.jsx # Panel de ciberseguridad
│   ├── HospitalDashboard.jsx # Estado y ocupación de hospitales
│   ├── KPIs.jsx              # KPIs operativos en tiempo real
│   ├── CrewManagement.jsx    # Gestión de tripulaciones y turnos
│   ├── PatientTracking.jsx   # Seguimiento de pacientes
│   ├── AIInsights.jsx        # Insights de los módulos de IA
│   ├── ParamedicView.jsx     # Vista para paramédicos en campo
│   ├── DriverMobile.jsx      # Vista móvil para conductores
│   └── DriverLogin.jsx       # Login específico para conductores
│
├── components/
│   ├── dashboard/            # 13 subcomponentes del Dashboard
│   │   ├── ActiveIncidentsPanel.jsx   # Panel de incidentes activos
│   │   ├── AiAutoSuggestionsPanel.jsx # Sugerencias automáticas de IA
│   │   ├── DigitalTwinPanel.jsx       # Telemetría del gemelo digital
│   │   ├── EmergencyAlertModal.jsx    # Modal de alerta de emergencia
│   │   ├── FleetListPanel.jsx         # Lista lateral de flota
│   │   ├── IncidentDetailModal.jsx    # Modal de detalle de incidente
│   │   ├── IncidentListPanel.jsx      # Panel de lista de incidentes
│   │   ├── MapControlsToolbar.jsx     # Barra de controles del mapa
│   │   ├── MapLegend.jsx              # Leyenda del mapa
│   │   ├── MetricCards.jsx            # Tarjetas de métricas (KPIs rápidos)
│   │   ├── OpsResumePanel.jsx         # Resumen operativo
│   │   ├── SimulationControls.jsx     # Controles de simulación
│   │   └── WeatherWidget.jsx          # Widget de condiciones meteorológicas
│   ├── ChatWidget.jsx        # Widget flotante de chat con IA
│   ├── ErrorBoundary.jsx     # Captura de errores React
│   ├── Layout.jsx            # Layout base con navegación lateral
│   ├── LoadingFallback.jsx   # Pantalla de carga (Suspense fallback)
│   ├── Skeleton.jsx          # Esqueletos de carga (loading placeholders)
│   └── mapIcons.js           # Definición de iconos Leaflet custom
│
├── hooks/
│   ├── useDigitalTwin.js           # Hook para datos del gemelo digital
│   ├── useIncidentNotifications.js # Hook para notificaciones de incidentes
│   ├── useSecurityAlerts.js        # Hook para alertas de seguridad en tiempo real
│   ├── useSimulationControls.js    # Hook para controles de simulación
│   └── useWeather.js               # Hook para datos meteorológicos
│
├── utils/
│   ├── incidentUtils.jsx     # Utilidades de formateo de incidentes (badges, colores)
│   ├── statusLabels.js       # Etiquetas de estado traducidas al español
│   └── weatherUtils.js       # Utilidades para condiciones meteorológicas
│
├── context/                  # Context API (AuthContext, etc.)
├── styles/                   # 18+ archivos CSS (modo oscuro, BEM-like)
├── config.js                 # URL base de la API (VITE_API_URL)
├── App.jsx                   # Router principal + rutas protegidas
└── main.jsx                  # Entry point React 19
```

## 13.2 Dashboard principal (Dashboard.jsx)

El Dashboard es la página central del sistema. Integra:

**Mapa Leaflet con capas GIS (toggleables):**
- Marcadores de ambulancias (iconos por subtipo: SVB, SVA, VIR, VAMM, SAMU)
- Incidentes con color por severidad (rojo=CRITICAL, naranja=HIGH, amarillo=MEDIUM, verde=LOW)
- Hospitales con color por ocupación (verde <60%, naranja 60-85%, rojo >85%)
- Gasolineras (icono ⛽ con nombre y marca)
- DEA (desfibriladores, icono corazón)
- Recursos multi-agencia (Bomberos, Policía, etc.)
- Rutas OSRM en tiempo real (polilínea azul siguiendo calles reales)
- Heatmap de severidad de incidentes
- Zonas de riesgo (radio de incidentes)
- Radios de cobertura de vehículos

**Panel lateral con tabs:**
- Flota: lista de vehículos con estado, combustible y subtipo
- Incidentes activos: lista con severidad, tipo y estado de ruta
- Resumen operativo: KPIs rápidos

**Barras de control:**
- Selector de ciudad (filtro geográfico)
- Control de velocidad de simulación
- Toggle de capas GIS
- Botones de inicio/parada de auto-generación de incidentes

**Polling de datos:**
- `/api/live`: cada 5 s (vehículos, incidentes, hospitales, weather, gasolineras)
- `/simulation/auto-generate/status`: cada 8 s

## 13.3 Routing SPA y protección de rutas

Las rutas protegidas usan un componente `RoleRoute` que verifica el rol del usuario autenticado antes de renderizar la página. Las rutas sin autenticación (Login, DriverLogin) son accesibles directamente.

## 13.4 Modo oscuro

El sistema usa exclusivamente modo oscuro (dark theme) con variables CSS. Los 18 ficheros CSS implementan un diseño consistente con paleta oscura, badges de severidad visibles con `text-shadow` + `box-shadow`, y tarjetas KPI compactas.

---

# 14. Gestión de Incidentes

## 14.1 Tipos de incidentes (14 tipos)

| Tipo | Descripción |
|---|---|
| CARDIAC_ARREST | Parada cardiorrespiratoria |
| TRAUMA | Traumatismo por accidente o caída |
| STROKE | Ictus / ACV |
| RESPIRATORY | Dificultad respiratoria aguda |
| BURNS | Quemaduras |
| INTOXICATION | Intoxicación (alcohol, drogas, gases) |
| PSYCHIATRIC | Crisis psiquiátrica |
| PEDIATRIC | Emergencia pediátrica |
| OBSTETRIC | Emergencia obstétrica / parto |
| DIABETIC | Crisis diabética (hipoglucemia / hiperglucemia) |
| ALLERGIC | Reacción alérgica / anafilaxia |
| ENVIRONMENTAL | Emergencia ambiental (insolación, hipotermia) |
| VEHICLE_ACCIDENT | Accidente de tráfico |
| MASS_CASUALTY | Incidente de Múltiples Víctimas (activa protocolo MCI) |

## 14.2 Niveles de severidad

| Severidad | Color | Criterio |
|---|---|---|
| CRITICAL | Rojo | Riesgo vital inmediato; recursos avanzados requeridos |
| HIGH | Naranja | Situación grave; atención en <8 min |
| MEDIUM | Amarillo | Situación moderada; atención en <15 min |
| LOW | Verde | Situación estable; atención no urgente |

## 14.3 Ciclo de vida de un incidente

```
OPEN → (TwinEngine asigna vehículo) → ASSIGNED
     → (Vehículo en ruta) → status permanece ASSIGNED, route_phase = TO_INCIDENT
     → (Llegada al incidente) → route_phase = AT_INCIDENT (18 s en escena)
     → (Traslado al hospital) → route_phase = TO_HOSPITAL
     → (Llegada al hospital) → RESOLVED, route_phase = COMPLETED
```

## 14.4 Límite de incidentes activos

Para proteger el rendimiento del sistema (especialmente en Railway y entornos con recursos limitados), el generador automático limita los incidentes activos a **15 simultáneos** (OPEN + ASSIGNED). Si se alcanza el límite, el generador pausa hasta que se resuelva alguno.

## 14.5 API de incidentes

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/api/live` | Incidentes activos (no RESOLVED) con datos de ruta |
| POST | `/simulation/generate-one` | Genera un incidente aleatorio inmediatamente |
| POST | `/simulation/auto-generate/start` | Inicia generación automática (30 s ±30% jitter) |
| POST | `/simulation/auto-generate/stop` | Detiene generación automática |
| GET | `/simulation/auto-generate/status` | Estado del generador (running, count, interval) |
| POST | `/simulation/reset` | Limpia todos los incidentes y resetea la flota |
| GET | `/simulation/incident-types` | Lista los 14 tipos de incidente disponibles |

---

# 15. Gestión de Flota

## 15.1 Tipos y subtipos de vehículos

| Subtipo | Nombre completo | Capacidad |
|---|---|---|
| SVB | Soporte Vital Básico | 2 técnicos TEAT; material BLS |
| SVA | Soporte Vital Avanzado | 1 médico + 1 enfermero + 1 TEAT; desfibrilador, ventilador |
| VIR | Vehículo de Intervención Rápida | 1 médico; primera respuesta rápida sin camilla |
| VAMM | Vehículo de Apoyo a Mando y Movilización | Coordinación y logística en campo |
| SAMU | Servicio de Atención Médica Urgente | Unidad médica avanzada; pacientes críticos |

## 15.2 Flota inicial (8 vehículos)

| ID | Subtipo | Base operativa |
|---|---|---|
| AMB-001 | SVA | Zona norte Madrid |
| AMB-002 | SVB | Zona sur Madrid |
| AMB-003 | VIR | Centro Madrid |
| AMB-004 | VAMM | Este Madrid |
| AMB-005 | SAMU | Hospital La Paz |
| AMB-006 | SVB | Zona oeste Madrid |
| AMB-007 | SVA | Getafe |
| AMB-008 | VIR | Alcalá de Henares |

## 15.3 API de flota

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/api/fleet` | Lista todos los vehículos con estado completo |
| GET | `/api/fleet/{id}` | Detalle de un vehículo específico |
| PUT | `/api/fleet/{id}` | Actualizar propiedades del vehículo |
| PATCH | `/api/fleet/{id}/status` | Cambiar estado del vehículo |
| PATCH | `/api/fleet/{id}/fuel` | Actualizar nivel de combustible |
| POST | `/api/fleet/{id}/enable` | Habilitar vehículo en la simulación |
| POST | `/api/fleet/{id}/disable` | Deshabilitar vehículo de la simulación |

---

# 16. Gestión de Tripulaciones y Turnos

## 16.1 Sistema de turnos

| Turno | Duración | Horario típico |
|---|---|---|
| Día (D) | 12 horas | 07:00 - 19:00 |
| Noche (N) | 12 horas | 19:00 - 07:00 |
| 24h (24) | 24 horas | Guardia completa |

## 16.2 Composición de tripulaciones

Cada tripulación (`Crew`) consta de:
- 2-4 miembros (médico, enfermero, TEAT, conductor)
- Asignación a un vehículo específico
- Turno activo (D/N/24h)
- Estado de disponibilidad

## 16.3 API de tripulaciones

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/api/crews` | Lista todas las tripulaciones |
| POST | `/api/crews` | Crear nueva tripulación |
| PUT | `/api/crews/{id}` | Actualizar tripulación |
| DELETE | `/api/crews/{id}` | Eliminar tripulación |
| GET | `/api/crews/{id}/schedule` | Horario de la tripulación |

---

# 17. Atención al Paciente (ePCR)

## 17.1 Informe ePCR (PatientCareReport)

El ePCR (Electronic Patient Care Report) es el registro digital completo de la atención a un paciente. Se crea automáticamente al resolverse un incidente.

| Campo | Descripción |
|---|---|
| `id` | PCR-XXX (generado con contador en memoria, sin N+1 queries) |
| `incident_id` | Incidente asociado |
| `vehicle_id` | Vehículo que atendió al paciente |
| `patient_name` | Nombre del paciente (anonimizado automáticamente con RGPD) |
| `chief_complaint` | Queja principal (descripción del incidente) |
| `receiving_hospital_id` | Hospital receptor |

## 17.2 Seguimiento del paciente (PatientTracking)

| Fase | Descripción |
|---|---|
| `AT_SCENE` | Paciente en escena de emergencia |
| `IN_TRANSIT` | Traslado al hospital |
| `AT_HOSPITAL_ER` | Ingresado en urgencias del hospital |
| `DISCHARGED` | Alta hospitalaria |

## 17.3 Anonimización automática RGPD

El módulo `backend/app/core/anonymizer.py` implementa:
- **Supresión**: Eliminación de campos directamente identificativos (DNI, teléfono)
- **Generalización**: Edad → rango de edad; código postal → zona
- **Perturbación de coordenadas**: Offset aleatorio de ±0.001° (~111 m) en coordenadas de pacientes

---

# 18. Sistema Hospitalario

## 18.1 Hospitales configurados (6)

| Hospital | Especialidades principales |
|---|---|
| Hospital La Paz | Trauma, Cardiología, Pediatría, Neurología |
| Hospital Gregorio Marañón | Urgencias, Cardiología, Trauma |
| Hospital 12 de Octubre | Oncología, Cardiología, Trauma |
| Hospital La Princesa | Neurología, Medicina Interna |
| Hospital Ramón y Cajal | Neurocirugía, Trauma, Cardiología |
| Hospital Clínico San Carlos | Urgencias, Medicina Interna, Cardiología |

## 18.2 Gestión de ocupación en tiempo real

El TwinEngine actualiza la carga hospitalaria automáticamente:

- **Al asignar** un incidente: el hospital receptor incrementa `current_load += affected_count`
- **Al resolver** un incidente: `current_load = max(0, current_load - affected_count)`

El endpoint `/api/live` incluye el estado de todos los hospitales con:
- `current_load`: pacientes actuales
- `capacity`: capacidad máxima
- `availability_pct`: porcentaje disponible = `(1 - current_load/capacity) × 100`
- `emergency_level`: nivel de emergencia del hospital (NORMAL/ALERT/CRITICAL)

## 18.3 Indicadores visuales en el mapa

| Ocupación | Color del marcador | Estado |
|---|---|---|
| < 60% | Verde | Disponible |
| 60% - 85% | Naranja | Ocupado |
| > 85% | Rojo | Saturado |

---

# 19. KPIs y Analytics

## 19.1 KPIs operativos principales

| KPI | Descripción | Objetivo |
|---|---|---|
| **Tiempo de Respuesta Medio** | Tiempo desde creación del incidente hasta llegada del vehículo | < 8 min (urbano) |
| **Disponibilidad de Flota** | % de vehículos IDLE sobre total habilitados | > 30% |
| **Tasa de Resolución** | Incidentes resueltos / incidentes totales en período | > 95% |
| **Ocupación Hospitalaria Media** | Promedio de `availability_pct` de todos los hospitales | > 20% disponible |
| **Combustible Medio** | Nivel de combustible promedio de la flota activa | > 40% del depósito |
| **Incidentes por Hora** | Tasa de generación de incidentes en la última hora | Configurable |

## 19.2 Analytics avanzados

La página `Analytics.jsx` y el router `/api/analytics` proveen:

- Distribución de incidentes por tipo y severidad (barras + pie chart)
- Tendencias temporales (incidentes por hora del día, por día de la semana)
- Mapa de calor de densidad de incidentes por zona
- Historial de tiempos de respuesta con percentiles (P50, P90, P99)
- Rendimiento por vehículo (incidentes atendidos, tiempo medio de respuesta)
- Exportación de datos a CSV para análisis externo

---

# 20. Monitorización — Prometheus y Alertmanager

## 20.1 Métricas expuestas

El endpoint `/metrics` expone en formato Prometheus:

| Métrica | Tipo | Etiquetas | Descripción |
|---|---|---|---|
| `http_requests_total` | Counter | method, endpoint, status | Total de peticiones HTTP |
| `http_request_duration_seconds` | Histogram | method, endpoint | Latencia de peticiones |
| `database_connections_active` | Gauge | — | Conexiones DB activas |
| `available_vehicles_count` | Gauge | — | Vehículos disponibles (IDLE) |
| `incidents_resolved_total` | Counter | — | Incidentes resueltos acumulados |

## 20.2 Configuración de Prometheus

`monitoring/prometheus.yml` configura el scrape del backend cada **15 s**:

```yaml
scrape_configs:
  - job_name: 'kairos-backend'
    static_configs:
      - targets: ['backend:5001']
    scrape_interval: 15s
    metrics_path: /metrics
```

## 20.3 Reglas de alerta (Alertmanager)

`monitoring/alert.rules.yml` define 4 reglas de alerta:

| Alerta | Condición | Severidad |
|---|---|---|
| `HighResponseLatency` | p95 de latencia > 2 s durante 5 min | warning |
| `HighErrorRate` | Tasa de errores HTTP 5xx > 5% durante 5 min | critical |
| `LowVehicleAvailability` | Vehículos disponibles < 2 durante 10 min | warning |
| `BackendDown` | Backend sin respuesta durante 1 min | critical |

---

# 21. Comunicación en Tiempo Real

## 21.1 WebSocket /ws/live

El endpoint WebSocket permite al TwinEngine empujar actualizaciones a todos los clientes conectados sin polling:

```python
@app.websocket("/ws/live")
async def ws_live(ws: WebSocket):
    await ws_manager.connect(ws)
    while True:
        await asyncio.sleep(30)  # Keep-alive sin exigir mensajes del cliente
```

El `WSManager` gestiona múltiples conexiones simultáneas y realiza broadcast a todos los clientes conectados cada vez que el TwinEngine completa un tick.

## 21.2 Polling del frontend

Para garantizar robustez ante desconexiones WebSocket, el frontend también usa polling HTTP:

| Endpoint | Intervalo | Datos |
|---|---|---|
| `/api/live` | 5 s | Vehículos, incidentes, hospitales, weather, gasolineras |
| `/simulation/auto-generate/status` | 8 s | Estado del generador automático |
| `/api/security/events` | 5 s | Eventos de seguridad en tiempo real |
| `/api/hospitals` | 15 s | Estado completo de hospitales |

---

# 22. Sistema de Roles y Permisos (RBAC)

## 22.1 Roles definidos

| Rol | Descripción | Permisos |
|---|---|---|
| **ADMIN** | Acceso completo al sistema | read, write, delete, manage_users, view_analytics |
| **OPERATOR** | Despachador de emergencias | read, write, view_analytics |
| **DOCTOR** | Personal clínico | read, view_clinical, write_epcr |
| **VIEWER** | Solo lectura (observador) | read |

## 22.2 Implementación técnica

```python
# FastAPI Dependency para verificación de roles
def require_role(*roles: str):
    def checker(current_user = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(403, "Insufficient permissions")
        return current_user
    return checker

# Uso en endpoints
@router.delete("/api/fleet/{id}")
async def delete_vehicle(
    id: str,
    user = Depends(require_role("ADMIN"))
):
    ...
```

## 22.3 Credenciales por defecto

| Usuario | Contraseña | Rol |
|---|---|---|
| `admin` | `admin123` | ADMIN |
| `operator` | `operator123` | OPERATOR |
| `doctor` | `doctor123` | DOCTOR |
| `viewer` | `viewer123` | VIEWER |

---

# 23. Simulación y Generación Automática de Incidentes

## 23.1 Generador de incidentes

El módulo `backend/app/core/incident_generator.py` genera incidentes sintéticos realistas para Madrid:

- **Coordenadas**: Distribuidas dentro del bounding box de Madrid (40.28°N-40.65°N / 3.52°W-3.92°W) con densidad mayor en el centro
- **Tipo**: Seleccionado aleatoriamente de los 14 tipos con pesos de probabilidad (CARDIAC_ARREST y TRAUMA son más frecuentes)
- **Severidad**: Clasificada por el módulo de IA (TF-IDF + RandomForest) a partir de la descripción generada
- **Descripción**: Generada de forma procedural según el tipo de incidente
- **Afectados**: 1-5 personas con distribución ponderada (mayoría incidentes individuales)
- **Dirección**: Generada con calles y números ficticios pero verosímiles de Madrid

## 23.2 Comportamiento del auto-generador

```python
_auto_gen_interval = 30  # segundos base
MAX_OPEN = 15            # incidentes OPEN+ASSIGNED máximos simultáneos

# En cada ciclo:
1. Cuenta incidentes activos (OPEN + ASSIGNED)
2. Si >= 15: espera sin generar
3. Si < 15: genera uno, registra en DB, crea AuditLog
4. Espera: interval × jitter (jitter ∈ [0.7, 1.3])
# Resultado: entre 21 s y 39 s entre incidentes (realismo operativo)
```

## 23.3 Identificación de incidentes

Los IDs de incidentes se generan de forma segura sin condiciones de carrera:

```python
max_num = db.execute(
    text("SELECT COALESCE(MAX(CAST(SUBSTRING(id FROM 5) AS INTEGER)), 0) FROM incidents")
).scalar() or 0
inc_id = f"INC-{max_num + 1:03d}"
```

---

# 24. Gestión de Recursos Multi-Agencia

## 24.1 Agencias configuradas

| Agencia | Tipo de recursos |
|---|---|
| Bomberos de Madrid | Camión de bomberos, USAR (Búsqueda y Rescate) |
| Policía Nacional | Patrulla policial, Unidad de apoyo |
| Guardia Civil | Patrulla de carretera, Helicóptero |
| Protección Civil | Vehículo de apoyo, Puesto de mando avanzado |
| Cruz Roja | Ambulancia voluntaria, Equipo de apoyo psicológico |

## 24.2 Estados de recursos

| Estado | Descripción |
|---|---|
| `AVAILABLE` | Recurso disponible para despacho |
| `DISPATCHED` | Recurso despachado a un incidente |
| `ON_SCENE` | Recurso presente en la escena |
| `RETURNING` | Regresando a base |
| `UNAVAILABLE` | Fuera de servicio / mantenimiento |

## 24.3 API de recursos

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/api/resources` | Lista todos los recursos multi-agencia |
| POST | `/api/resources` | Registrar nuevo recurso |
| PATCH | `/api/resources/{id}/dispatch` | Despachar recurso a incidente |
| PATCH | `/api/resources/{id}/status` | Actualizar estado del recurso |

---

# 25. Referencia Completa de API

## 25.1 Autenticación

Todos los endpoints protegidos requieren cabecera:
```
Authorization: Bearer <access_token>
```

El token se obtiene con:
```
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=admin&password=admin123
```

Respuesta:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "role": "ADMIN"
}
```

## 25.2 Endpoints por módulo

### Autenticación (/api/auth)

| Método | Path | Auth | Descripción |
|---|---|---|---|
| POST | `/api/auth/login` | No | Login; devuelve JWT |
| POST | `/api/auth/register` | ADMIN | Crear nuevo usuario |
| POST | `/api/auth/logout` | Sí | Invalida token (JWT blacklist) |
| GET | `/api/auth/me` | Sí | Perfil del usuario autenticado |
| POST | `/api/auth/init-admin` | No | Inicializar primer admin (solo si no existe) |

### Flota (/api/fleet)

| Método | Path | Auth | Descripción |
|---|---|---|---|
| GET | `/api/fleet` | Sí | Lista toda la flota |
| GET | `/api/fleet/{id}` | Sí | Detalle de un vehículo |
| PUT | `/api/fleet/{id}` | OPERATOR+ | Actualizar vehículo |
| PATCH | `/api/fleet/{id}/status` | OPERATOR+ | Cambiar estado |
| PATCH | `/api/fleet/{id}/fuel` | OPERATOR+ | Actualizar combustible |
| POST | `/api/fleet/seed` | ADMIN | Sembrar flota inicial |

### Simulación (/simulation)

| Método | Path | Auth | Descripción |
|---|---|---|---|
| POST | `/simulation/reset` | ADMIN | Reset completo del sistema |
| POST | `/simulation/auto-generate/start` | OPERATOR+ | Iniciar auto-generación |
| POST | `/simulation/auto-generate/stop` | OPERATOR+ | Detener auto-generación |
| GET | `/simulation/auto-generate/status` | Sí | Estado del generador |
| POST | `/simulation/generate-one` | OPERATOR+ | Generar un incidente inmediato |
| GET | `/simulation/incident-types` | Sí | Lista de 14 tipos de incidente |

### Hospitales (/api/hospitals)

| Método | Path | Auth | Descripción |
|---|---|---|---|
| GET | `/api/hospitals` | Sí | Lista hospitales con ocupación |
| GET | `/api/hospitals/{id}` | Sí | Detalle de hospital |
| PUT | `/api/hospitals/{id}` | ADMIN | Actualizar hospital |
| GET | `/api/hospitals/{id}/occupancy` | Sí | Ocupación actual |

### IA (/api/ai)

| Método | Path | Auth | Descripción |
|---|---|---|---|
| POST | `/api/ai/classify-severity` | Sí | Clasificar severidad de incidente |
| POST | `/api/ai/predict-eta` | Sí | Predecir ETA |
| POST | `/api/ai/predict-demand` | Sí | Predicción de demanda por zona |
| POST | `/api/ai/detect-anomaly` | Sí | Detectar anomalías en métricas |
| POST | `/api/ai/recommend` | Sí | Recomendaciones para operador |
| POST | `/api/ai/analyze-vision` | Sí | Análisis de descripción de escena |
| GET | `/api/ai/maintenance` | Sí | Predicciones de mantenimiento |
| POST | `/api/ai/optimal-assignment` | OPERATOR+ | Asignación óptima vehículo-incidente |

### Seguridad (/api/security)

| Método | Path | Auth | Descripción |
|---|---|---|---|
| GET | `/api/security/events` | ADMIN | Eventos de seguridad recientes |
| GET | `/api/security/blocked-ips` | ADMIN | IPs bloqueadas actualmente |
| DELETE | `/api/security/blocked-ips/{ip}` | ADMIN | Desbloquear IP |
| GET | `/api/security/sessions` | ADMIN | Sesiones JWT activas |
| POST | `/api/security/scan-input` | Sí | Escanear texto para amenazas |
| POST | `/api/security/check-password` | Sí | Verificar fortaleza + HIBP |
| GET | `/api/security/headers-analysis` | Sí | Análisis de cabeceras HTTP (score A-F) |
| GET | `/api/security/score` | Sí | Security score del sistema (0-100) |

### Blockchain (/api/blockchain)

| Método | Path | Auth | Descripción |
|---|---|---|---|
| POST | `/api/blockchain/notarize` | ADMIN | Notarizar batch pendiente ahora |
| GET | `/api/blockchain/batches` | ADMIN | Lista de lotes Merkle |
| GET | `/api/blockchain/verify/{batch_id}` | Sí | Verificar integridad de un lote |
| GET | `/api/blockchain/status` | Sí | Estado del nodo blockchain |

### Auditoría (/api/audit)

| Método | Path | Auth | Descripción |
|---|---|---|---|
| GET | `/api/audit` | ADMIN | Log de auditoría paginado |
| GET | `/api/audit/{id}` | ADMIN | Entrada de auditoría con hash |
| GET | `/api/audit/export` | ADMIN | Exportar log en CSV |

---

# 26. Testing y Calidad de Código

## 26.1 Suites de tests

El proyecto incluye 13 suites de tests con 72+ tests automatizados:

| Suite | Archivo | Tests | Cobertura |
|---|---|---|---|
| Auth | `tests/test_auth.py` | ~8 | Login, JWT, roles, HIBP |
| Fleet | `tests/test_fleet.py` | ~6 | CRUD vehículos, estado |
| Incidents | `tests/test_incidents.py` | ~8 | Ciclo de vida, severidad |
| AI Modules | `tests/test_ai.py` | ~10 | Los 10 módulos IA |
| Blockchain | `tests/test_blockchain.py` | ~6 | Merkle, notarización |
| Security | `tests/test_security.py` | ~8 | Rate limit, brute-force, escaneo |
| Hospitals | `tests/test_hospitals.py` | ~5 | CRUD, ocupación |
| KPIs | `tests/test_kpis.py` | ~4 | Cálculo de métricas |
| Crews | `tests/test_crews.py` | ~5 | Gestión de tripulaciones |
| ePCR | `tests/test_epcr.py` | ~4 | Informes de paciente |
| Analytics | `tests/test_analytics.py` | ~4 | Analítica y exportación |

## 26.2 Ejecución de tests

```bash
cd backend
pytest tests/ -v                    # Todos los tests
pytest tests/test_auth.py -v        # Solo autenticación
pytest tests/ --cov=app --cov-report=html  # Con cobertura HTML
```

## 26.3 Verificación de sintaxis

```bash
# Backend
python -m py_compile backend/app/main.py
python -m py_compile backend/app/core/twin_engine.py

# Frontend
cd frontend && npm run build        # Build completo (detecta errores JS/JSX)
```

---

# 27. Configuración y Variables de Entorno

## 27.1 Variables de entorno del backend

El fichero `backend/.env` contiene la configuración sensible. Se carga automáticamente con `python-dotenv`.

| Variable | Default | Descripción |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg2://twin:twin@localhost:55432/twin` | URL de conexión PostgreSQL |
| `REDIS_URL` | — | URL completa de Redis (alternativa a REDIS_HOST/PORT) |
| `REDIS_HOST` | `localhost` | Host de Redis |
| `REDIS_PORT` | `6379` | Puerto de Redis |
| `REDIS_DB` | `0` | Base de datos Redis |
| `SECRET_KEY` | Generada aleatoriamente | Clave de firma JWT (cambiar en producción) |
| `ALGORITHM` | `HS256` | Algoritmo JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Expiración de tokens JWT |
| `TICK_MS` | `1500` | Intervalo del ciclo del TwinEngine (ms) |
| `SECURITY_RATE_LIMIT_ENABLED` | `true` | Habilitar rate limiting |
| `SECURITY_BRUTE_FORCE_ENABLED` | `true` | Habilitar detección brute-force |
| `SECURITY_MAX_LOGIN_ATTEMPTS` | `5` | Intentos de login antes del bloqueo |
| `SECURITY_LOCKOUT_MINUTES` | `10` | Duración del bloqueo de IP |
| `TRUSTED_PROXY_COUNT` | `0` | Proxies de confianza (Railway/nginx: 1) |
| `FIELD_ENCRYPTION_KEY` | — | Clave AES-256 base64 para cifrado PII |
| `BSV_PRIVATE_KEY` | — | Clave privada BSV para notarización |
| `BSV_NETWORK` | `main` | Red BSV: `main` o `testnet` |
| `ARC_URL` | `https://arc.gorillapool.io` | URL del ARC API para difusión BSV |
| `BLOCKCHAIN_BATCH_INTERVAL_MIN` | `30` | Intervalo de batch blockchain (minutos) |
| `CORS_ORIGINS` | — | Orígenes CORS adicionales (comma-separated) |

## 27.2 Variables de entorno del frontend

Configuradas en `frontend/.env` o como args de build en Docker:

| Variable | Default | Descripción |
|---|---|---|
| `VITE_API_URL` | `http://localhost:5001` | URL base del backend |

---

# 28. Guía de Instalación

## 28.1 Requisitos previos

| Requisito | Versión mínima | Notas |
|---|---|---|
| Docker Desktop | 24.0+ | Incluye Docker Compose v2 |
| Python | 3.10+ | Solo para run_all.py (no para el backend en Docker) |
| Git | Cualquiera | Para clonar el repositorio |

## 28.2 Instalación paso a paso

### Paso 1: Clonar el repositorio

```bash
git clone https://github.com/JuanmPalencia/KAIROS_CDS.git
cd KAIROS_CDS
```

### Paso 2: Arrancar el sistema

```bash
python3 run_all.py
```

El script ejecuta automáticamente:
1. Verifica que Docker está disponible y corriendo
2. `docker compose up -d` — levanta los 6 servicios
3. Espera hasta que el backend responde en `/health` (máx. 60 s)
4. Llama a `/api/auth/init-admin` — crea el usuario admin si no existe
5. Llama a `/api/fleet/seed` — siembra la flota si está vacía
6. Llama a `/simulation/auto-generate/start` — activa la generación automática
7. Muestra las URLs de acceso

### Paso 3: Acceder al sistema

| URL | Descripción |
|---|---|
| http://localhost:5173 | Dashboard frontend (React) |
| http://localhost:5001/docs | Documentación interactiva API (Swagger UI) |
| http://localhost:9090 | Prometheus |
| http://localhost:9093 | Alertmanager |

### Paso 4: Login

Credenciales por defecto:
```
admin / admin123     → Acceso completo
operator / operator123 → Despacho de emergencias
```

## 28.3 Reset completo (borrar todos los datos)

```bash
python3 run_all.py --reset
```

Pide confirmación interactiva antes de ejecutar `docker compose down -v` (borra volúmenes) + `docker compose up -d` + re-seed.

## 28.4 Instalación manual (sin Docker)

Para desarrollo local sin Docker:

```bash
# Backend
cd backend
pip install -r requirements.txt
# Configurar DATABASE_URL y REDIS_URL en .env
uvicorn app.main:app --host 0.0.0.0 --port 5001 --reload

# Frontend (en otro terminal)
cd frontend
npm install
npm run dev
```

---

# 29. Rendimiento y Escalabilidad

## 29.1 Optimizaciones implementadas

| Optimización | Descripción | Impacto |
|---|---|---|
| **Caché /api/live** | TTL 2 s en memoria, evita 7 queries DB por poll | -80% carga DB bajo polling normal |
| **Caché OSRM** | LRU de 200 rutas, evita llamadas repetidas a API externa | Rutas frecuentes: 0 ms (vs 3-8 s) |
| **Hospital cache** | Refresca cada 10 ticks (~15 s) en lugar de por tick | -90% queries de hospitales |
| **Vehicle map dict** | Lookup O(1) por vehículo_id en lugar de O(n) scan | Escala bien con flotas grandes |
| **PCR counter** | Contador en memoria inicializado una vez, sin COUNT(*) por incidente | Elimina query COUNT por resolución |
| **TICK_MS = 1500** | Tick 1.5 s en lugar de 0.5 s — reduce carga de DB + OSRM | -66% ciclos de simulación |
| **Incidente cap = 15** | Máximo 15 incidentes activos simultáneos | Previene sobrecarga de CPU |
| **Cleanup en arranque** | Resuelve incidentes stale y resetea vehículos atascados | Estado consistente tras reinicios |
| **Batch Merkle** | Agrupa N audit logs en 1 transacción blockchain | -99% coste blockchain |

## 29.2 Métricas de rendimiento observadas

| Métrica | Valor típico |
|---|---|
| Latencia `/api/live` (con caché) | < 5 ms |
| Latencia `/api/live` (sin caché, ~7 queries) | 15-40 ms |
| Latencia OSRM (primera vez) | 3-8 s (API pública) |
| Latencia OSRM (con caché) | < 1 ms |
| Memoria del backend (Docker) | ~200-350 MB |
| CPU del backend en tick | < 5% (host moderno) |
| Throughput API | ~200 req/s (limitado por rate limiter a 120/min por IP) |

## 29.3 Escalabilidad horizontal

Aunque el sistema actual es monolítico por diseño (HPE CDS Challenge), está preparado para escalar:

| Componente | Estrategia de escalado |
|---|---|
| Backend | Múltiples réplicas uvicorn detrás de nginx; sesiones en Redis (ya implementado) |
| Base de datos | Read replicas PostgreSQL; partición de tablas por fecha en audit_logs |
| TwinEngine | Sharding por ciudad/región; cada instancia gestiona un subconjunto de la flota |
| Frontend | CDN estático (Vite build) + edge caching |

---

# 30. Glosario Técnico

| Término | Definición |
|---|---|
| **ARC API** | API de difusión de transacciones BSV (gorillapool.io) |
| **AVC / Ictus** | Accidente Vascular Cerebral; emergencia neurológica de tiempo-crítico |
| **BCrypt** | Algoritmo de hashing de contraseñas con salt incorporado y factor de coste ajustable |
| **BLS** | Basic Life Support: soporte vital básico (RCP, desfibrilación automática) |
| **BSV** | Bitcoin SV: blockchain de alto throughput usada para notarización de auditoría |
| **DEA** | Desfibrilador Externo Automático |
| **ePCR** | Electronic Patient Care Report: informe electrónico de atención al paciente |
| **HIBP** | HaveIBeenPwned: servicio de verificación de contraseñas comprometidas en brechas |
| **IsolationForest** | Algoritmo de ML no supervisado para detección de anomalías basado en árboles |
| **JWT** | JSON Web Token: estándar de tokens de autenticación firmados digitalmente |
| **Leaflet** | Biblioteca JavaScript open-source para mapas interactivos |
| **MCI** | Mass Casualty Incident: incidente con múltiples víctimas que requiere protocolo START |
| **Merkle Tree** | Estructura de datos de hash donde cada nodo padre es el hash de sus hijos; garantiza integridad |
| **OSRM** | Open Source Routing Machine: motor de routing geoespacial sobre grafos de calles (OSM) |
| **PII** | Personally Identifiable Information: datos de identificación personal sujetos a RGPD |
| **PostGIS** | Extensión de PostgreSQL para datos geoespaciales (geometrías, proyecciones, índices espaciales) |
| **RBAC** | Role-Based Access Control: control de acceso basado en roles |
| **RGPD** | Reglamento General de Protección de Datos (GDPR en inglés) |
| **SAMUR** | Servicio de Asistencia Municipal de Urgencias y Rescate (Madrid) |
| **SAMU** | Servicio de Atención Médica Urgente |
| **SEM** | Servicio de Emergencias Médicas |
| **START** | Simple Triage And Rapid Treatment: protocolo de triaje en MCI |
| **SUMMA 112** | Servicio de Urgencias Médicas de la Comunidad de Madrid |
| **SVA** | Soporte Vital Avanzado: ambulancia medicalizada con médico y enfermero |
| **SVB** | Soporte Vital Básico: ambulancia de TEAT sin médico |
| **TwinEngine** | Motor central del gemelo digital: bucle asíncrono de 1 500 ms que gestiona el ciclo de vida completo de la simulación |
| **VIR** | Vehículo de Intervención Rápida: respuesta médica en vehículo ligero |
| **VAMM** | Vehículo de Apoyo a Mando y Movilización: coordinación logística de campo |
| **WhatsOnChain** | Explorador de bloques de BSV para verificación de transacciones on-chain |
| **WS** | WebSocket: protocolo de comunicación bidireccional full-duplex sobre TCP |

---

*KAIROS CDS v1.0.0 — HPE GreenLake CDS Challenge 2026*
*Documentación técnica generada en Marzo 2026*
