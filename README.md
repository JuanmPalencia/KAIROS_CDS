<p align="center">
  <img src="frontend/src/assets/logo_kairos.png" alt="KAIROS CDS" width="120" />
</p>

<h1 align="center">KAIROS CDS</h1>
<h3 align="center">Digital Twin for Emergency Fleet Management — Madrid, Spain</h3>

<p align="center">
  <img src="https://img.shields.io/badge/version-1.0.0-blue?style=flat-square" alt="Version" />
  <img src="https://img.shields.io/badge/python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/react-19-61DAFB?style=flat-square&logo=react&logoColor=black" alt="React" />
  <img src="https://img.shields.io/badge/fastapi-0.115-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/postgresql-16+PostGIS-4169E1?style=flat-square&logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/redis-7-DC382D?style=flat-square&logo=redis&logoColor=white" alt="Redis" />
  <img src="https://img.shields.io/badge/docker-compose-2496ED?style=flat-square&logo=docker&logoColor=white" alt="Docker" />
  <img src="https://img.shields.io/badge/blockchain-BSV-EAB300?style=flat-square" alt="BSV" />
  <img src="https://img.shields.io/badge/security-8.5%2F10-brightgreen?style=flat-square" alt="Security" />
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License" />
</p>

<p align="center">
  Real-time simulation, monitoring, and optimization of emergency ambulance fleets<br/>
  powered by <strong>10 local AI modules</strong>, <strong>OSRM street routing</strong>, <strong>blockchain auditing</strong>, and <strong>enterprise-grade security</strong>.
</p>

<p align="center">
  <a href="https://www.youtube.com/watch?v=_HiGhmS0Gmo" target="_blank">
    <img src="https://img.shields.io/badge/▶%20Demo%20Video-YouTube-FF0000?style=for-the-badge&logo=youtube&logoColor=white" alt="Demo Video" />
  </a>
</p>

---

## Overview

KAIROS CDS is a **digital twin platform** that simulates and manages emergency medical service (EMS) fleets in real time. It combines artificial intelligence, OSRM street-level routing, geospatial tracking, blockchain-based audit trails, and a comprehensive cybersecurity layer into a single production-ready system contextualized for the **Comunidad de Madrid**.

<table>
<tr>
<td width="50%">

**Core Capabilities**
- Real-time vehicle tracking on interactive Leaflet maps
- OSRM street routing (real Madrid roads, 250 waypoints, 200-route cache)
- Automatic ambulance dispatch with AI optimization
- Hospital occupancy monitoring (live load/capacity)
- Blockchain-notarized audit trail (BSV mainnet, Merkle batch)
- Full cybersecurity suite with real-time threat detection

</td>
<td width="50%">

**Project Metrics**
| Metric | Value |
|--------|-------|
| API Endpoints | 134 REST + 1 WebSocket |
| AI Modules | 10 (100% local, sklearn) |
| Frontend Pages | 15 |
| Dashboard Components | 13 |
| Custom React Hooks | 5 |
| Database Tables | 18 |
| Docker Services | 6 |
| Test Suites | 13 (72+ tests) |
| Security Score | 8.5 / 10 |

</td>
</tr>
</table>

---

## Quick Start

> **Prerequisites:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) + [Python 3.10+](https://www.python.org/downloads/)

```bash
git clone https://github.com/JuanmPalencia/KAIROS_CDS.git
cd KAIROS_CDS
python3 run_all.py
```

**That's it.** The script handles everything: Docker services, database initialization, data seeding, and incident auto-generation.

| Command | Description |
|---------|-------------|
| `python3 run_all.py` | Start all services (preserves existing data) |
| `python3 run_all.py --reset` | Full reset with confirmation (wipes all data) |
| `python3 run_all.py --security` | Run cyber-claude security scan |
| `python3 run_all.py --logs` | View live service logs |
| `python3 run_all.py --stop` | Stop all services |

### Access

| Service | URL |
|---------|-----|
| **Dashboard** | [http://localhost:5173](http://localhost:5173) |
| **API Docs (Swagger)** | [http://localhost:5001/docs](http://localhost:5001/docs) |
| **Prometheus** | [http://localhost:9090](http://localhost:9090) |
| **Alertmanager** | [http://localhost:9093](http://localhost:9093) |

### Default Credentials

| User | Password | Role |
|------|----------|------|
| `admin` | `admin123` | ADMIN — Full access |
| `operator` | `operator123` | OPERATOR — Dispatch |
| `doctor` | `doctor123` | DOCTOR — Clinical |
| `viewer` | `viewer123` | VIEWER — Read-only |

---

## Architecture

```
                          +-------------------+
                          |   React 19 SPA    |
                          |   Leaflet + Recharts
                          +--------+----------+
                                   |  HTTP polling (5s) + WebSocket
                          +--------v----------+
                          |   FastAPI Backend  |
                          |   134 endpoints    |
                          |   21 routers       |
                          |   TwinEngine 1500ms|
                          +--------+----------+
                                   |
              +--------------------+--------------------+
              |                    |                    |
    +---------v------+   +--------v-------+   +--------v--------+
    | PostgreSQL 16  |   |   Redis 7      |   | BSV Blockchain  |
    | + PostGIS      |   | sessions/cache |   | Merkle batching |
    +----------------+   +----------------+   +-----------------+
                                   |
                          +--------v----------+
                          |   OSRM Routing    |
                          |   (real streets)  |
                          +-------------------+
```

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React 19 + Leaflet 1.9 + Recharts | Real-time dashboard, interactive maps, analytics |
| **Backend** | FastAPI 0.115 + SQLAlchemy 2.0 + Pydantic v2 | REST API, WebSocket, business logic |
| **Twin Engine** | Async loop, TICK_MS=1500, OSRM routing | Vehicle movement, incident lifecycle, hospital load |
| **AI Engine** | scikit-learn (6 trained + 4 rule-based) | Classification, prediction, anomaly detection |
| **Database** | PostgreSQL 16 + PostGIS | Geospatial data, 18 relational tables |
| **Cache** | Redis 7 | Session management, rate limiting |
| **Routing** | OSRM (router.project-osrm.org) | Real Madrid street routes, 250 waypoints, 200-entry LRU cache |
| **Blockchain** | BSV + Merkle Trees | Immutable audit trail via WhatsOnChain |
| **Monitoring** | Prometheus + Alertmanager | Metrics collection, 4 alert rules |
| **Security** | Custom middleware stack | JWT, RBAC, AES-256-GCM, rate limiting, threat detection |

---

## TwinEngine — How It Works

The TwinEngine runs as an asyncio task, ticking every **1 500 ms**:

1. **Startup cleanup**: Resolves stale incidents and resets stuck vehicles from previous sessions
2. **Assignment**: Assigns nearest IDLE vehicle + nearest hospital to each OPEN incident
3. **Routing**: Calls OSRM for real street routes (ambulance → incident → hospital), falls back to multi-turn deterministic route if OSRM is unavailable
4. **Movement**: Updates vehicle GPS position along waypoints each tick
5. **Arrival detection**: Detects arrival at incident (~33m radius OR route progress threshold)
6. **On-scene**: 12 ticks (~18s) at the incident before departing to hospital
7. **Resolution**: Hospital load updated, PatientCareReport + PatientTracking records created, vehicle returns to IDLE

**Performance optimizations:**
- `/api/live` endpoint: 2s in-memory cache (reduces DB load ~80%)
- OSRM route cache: 200 LRU entries (routes within ~11m reuse cached result)
- Hospital cache: refreshed every 10 ticks (~15s), not on every tick
- Incident cap: max 15 open incidents simultaneously (prevents CPU overload)

---

## AI Modules

All models run **locally** with scikit-learn. No external AI API dependencies.

| # | Module | Algorithm | Purpose |
|---|--------|-----------|---------|
| 1 | **Severity Classifier** | TF-IDF + RandomForest | Classify incident severity (LOW/MEDIUM/HIGH/CRITICAL) |
| 2 | **Chat Assistant** | TF-IDF + LogisticRegression | Natural language intent detection for operator chat |
| 3 | **Vision Analyzer** | TF-IDF + LinearSVC | Emergency scene classification from text descriptions |
| 4 | **Demand Predictor** | RandomForest Regressor | Predict incident hotspots by zone and time |
| 5 | **ETA Predictor** | GradientBoosting Regressor | Estimate ambulance arrival times |
| 6 | **Anomaly Detector** | IsolationForest | Detect unusual vehicle/incident patterns |
| 7 | **Maintenance Predictor** | Rule-based thresholds | Predict vehicle maintenance needs |
| 8 | **Traffic Integration** | Rule-based by hour/day | Real-time traffic factor estimation (1.0–2.5x multiplier) |
| 9 | **Recommendation Engine** | Profile-based filtering | Personalized operator action suggestions |
| 10 | **Assignment Optimizer** | Multi-criteria scoring | Optimal vehicle-to-incident matching (distance 40%, type 25%, fuel 20%, trust 15%) |

**Train models:**
```bash
cd backend && python train_all_models.py
```

---

## Security

KAIROS CDS achieves an **8.5/10 security rating** (audited by [cyber-claude](./cyber-claude/)):

| Feature | Implementation |
|---------|---------------|
| **Authentication** | JWT HS256 (30 min expiry) + OAuth2 + HIBP password breach detection |
| **Authorization** | RBAC with 4 roles and granular per-endpoint permission checks |
| **Encryption** | AES-256-GCM for PII fields + bcrypt password hashing |
| **Brute-force Protection** | 5 attempts/min lockout (10 min block) per IP |
| **Rate Limiting** | 5/min (login), 3/min (register), 120/min (general); polling excluded |
| **Security Headers** | 11 headers (HSTS+preload, CSP, X-Frame-Options, CORP, COOP, etc.) |
| **Input Scanning** | SQLi, XSS, path traversal detection on all POST/PUT/PATCH bodies |
| **Audit Trail** | Hash chain + blockchain-notarized logs (BSV mainnet + Merkle batching) |
| **Session Management** | JWT blacklist in Redis + active session tracking (2000 events in memory) |

---

## Blockchain

Audit logs are notarized on the **BSV mainnet** using OP_RETURN transactions with Merkle tree batching.

- **Broadcast:** ARC API (gorillapool.io)
- **Verification:** [WhatsOnChain](https://whatsonchain.com)
- **Batch interval:** 30 minutes (configurable via `BLOCKCHAIN_BATCH_INTERVAL_MIN`)
- **Cost:** ~$0.01/day for 1000+ audit logs (Merkle batching)
- **Fallback:** Local JSONL ledger when offline

---

## Project Structure

```
KAIROS_CDS/
├── backend/
│   ├── app/
│   │   ├── api/              # 21 routers (134 endpoints)
│   │   ├── auth/             # JWT + RBAC (dependencies.py, security.py)
│   │   ├── blockchain/       # BSV adapter, Merkle trees, batch notarizer
│   │   ├── core/             # TwinEngine, OSRM routing, 10 AI modules,
│   │   │                     # cybersecurity, anonymizer, metrics, Redis
│   │   ├── storage/          # SQLAlchemy models (18 tables) + repos
│   │   └── main.py           # FastAPI app + middleware + lifespan
│   ├── datasets/             # Training data (CSV)
│   ├── models/               # Trained ML models (.joblib)
│   ├── tests/                # 13 test suites (72+ tests)
│   └── train_all_models.py   # One-command model training
├── frontend/
│   ├── src/
│   │   ├── pages/            # 15 pages
│   │   ├── components/
│   │   │   ├── dashboard/    # 13 dashboard sub-components
│   │   │   └── *.jsx         # 6 standalone components
│   │   ├── hooks/            # 5 custom hooks
│   │   ├── utils/            # 3 utility modules
│   │   ├── styles/           # 18+ CSS files (dark mode)
│   │   └── config.js         # API base URL
│   └── Dockerfile
├── cyber-claude/             # Integrated security analysis tool
├── monitoring/               # Prometheus + Alertmanager configs
├── docker-compose.yml        # 6 services with healthchecks
├── run_all.py                # Single entry point for all operations
├── FICHA_TECNICA_KAIROS_CDS.md  # Full technical specification (30 sections)
└── README.md
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [`FICHA_TECNICA_KAIROS_CDS.md`](./FICHA_TECNICA_KAIROS_CDS.md) | Complete technical specification (30 sections, all modules detailed) |
| [`cyber-claude/README.md`](./cyber-claude/README.md) | Security analysis tool documentation |
| [`localhost:5001/docs`](http://localhost:5001/docs) | Interactive API documentation (Swagger UI) |

---

## Tech Stack

<p>
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/React_19-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React" />
  <img src="https://img.shields.io/badge/PostgreSQL_16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/PostGIS-4CAF50?style=for-the-badge" alt="PostGIS" />
  <img src="https://img.shields.io/badge/Redis_7-DC382D?style=for-the-badge&logo=redis&logoColor=white" alt="Redis" />
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker" />
  <img src="https://img.shields.io/badge/OSRM-0078D4?style=for-the-badge" alt="OSRM" />
  <img src="https://img.shields.io/badge/scikit--learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white" alt="sklearn" />
  <img src="https://img.shields.io/badge/Leaflet-199900?style=for-the-badge&logo=leaflet&logoColor=white" alt="Leaflet" />
  <img src="https://img.shields.io/badge/Prometheus-E6522C?style=for-the-badge&logo=prometheus&logoColor=white" alt="Prometheus" />
  <img src="https://img.shields.io/badge/BSV_Blockchain-EAB300?style=for-the-badge" alt="BSV" />
</p>

---

## License

MIT License. See [LICENSE](./LICENSE) for details.

---

<p align="center">
  <strong>KAIROS CDS</strong> — Built for emergency management professionals<br/>
  <sub>HPE GreenLake CDS Challenge 2026</sub>
</p>
