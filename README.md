# KAIROS CDS

**Digital Twin for Emergency Fleet Management** — v1.0.0

> Real-time emergency fleet management with AI, blockchain auditing, and advanced security.

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![React 19](https://img.shields.io/badge/react-19-61dafb)
![FastAPI](https://img.shields.io/badge/fastapi-0.115-009688)
![PostgreSQL 16](https://img.shields.io/badge/postgresql-16%20%2B%20PostGIS-336791)
![Docker](https://img.shields.io/badge/docker-compose-2496ed)

---

## 🚀 Quick Start

### First Time Setup (60 seconds)

```bash
# Windows
SETUP.bat

# Linux/macOS
bash SETUP.sh
```

Automatically:
- ✅ Starts 6 Docker containers (PostgreSQL, Redis, Backend, Frontend, Prometheus, Alertmanager)
- ✅ Initializes database & test data
- ✅ Starts incident auto-generation
- ✅ Opens access URLs

### Access URLs

| Service | URL |
|---------|-----|
| **Frontend** | http://localhost:5173 |
| **API** | http://localhost:5001 |
| **Swagger Docs** | http://localhost:5001/docs |
| **Prometheus** | http://localhost:9090 |
| **Alertmanager** | http://localhost:9093 |

### Default Credentials

```
admin    / admin123    → Full access
operator / operator123 → Fleet & dispatch
doctor   / doctor123   → Patient & clinical
viewer   / viewer123   → Read-only
```

---

## ✨ Key Features

- ✅ **Real-time Dashboard** — Leaflet map with fleet tracking, incidents, hospitals, heatmaps
- ✅ **Fleet Management** — 8 ambulances (SVB, SVA, VIR, VAMM, SAMU) with fuel routing
- ✅ **10 AI Modules** — Local sklearn models: severity, demand, ETA, anomalies, maintenance, vision, chat, traffic, recommendations, assignment
- ✅ **Blockchain** — BSV + Merkle trees for immutable audit trail
- ✅ **Enterprise Security** — JWT+RBAC, AES-256-GCM encryption, HIBP password check, rate limiting, CSRF, 11+ security headers
- ✅ **118 API Endpoints** — FastAPI with Swagger docs
- ✅ **Patient Care** — ePCR (Electronic Patient Care Report) + MCI triage (START protocol)
- ✅ **Crew Management** — Adaptive shift scheduling (Day/Night/24h rotations)
- ✅ **Hospital Occupancy** — Real-time occupancy tracking with live updates
- ✅ **Monitoring** — Prometheus metrics + Alertmanager alerts

---

## 📊 Tech Stack

```
Frontend:       React 19 + Vite + Leaflet
Backend:        FastAPI (Python 3.10+)
Database:       PostgreSQL 16 + PostGIS + Redis 7
Monitoring:     Prometheus + Alertmanager
Blockchain:     BSV (Bitcoin SV)
Deployment:     Docker Compose
```

---

## 🛑 Common Commands

```bash
# Restart services (5-10 seconds, keeps data)
docker compose restart

# View logs
docker compose logs -f backend        # API logs
docker compose logs -f frontend       # Frontend logs

# Stop everything (keeps data)
docker compose down

# Reset everything (⚠️ deletes data)
docker compose down -v
SETUP.bat (or bash SETUP.sh)

# View all services
docker compose ps
```

---

## 📖 Documentation

### For Technical Details
See `TECHNICAL_SUMMARY.md` for:
- Complete architecture diagram
- Database schema (PostgreSQL + PostGIS)
- All 118 API endpoints
- Security implementation details
- AI module descriptions

### For Troubleshooting

| Problem | Solution |
|---------|----------|
| API not responding | `docker compose logs backend` |
| Port already in use | Kill process: `lsof -ti:5001 \| xargs kill` (macOS/Linux) |
| Data lost | Run `docker compose down -v` then `SETUP.bat` again |
| Docker not running | Install [Docker Desktop](https://www.docker.com/products/docker-desktop) |
| Logs too verbose | `docker compose logs --tail=50 backend` |

### For Security Details
See `SECURITY_ANALYSIS.md` for:
- Enterprise security assessment (8.5/10)
- All implemented protections
- Compliance & recommendations
- Penetration testing insights

---

## 🏗️ Project Structure

```
KAIROS_CDS/
├── backend/               # FastAPI: 118 endpoints, 10 AI modules, 15+ routers
├── frontend/              # React 19: 15+ pages, Leaflet maps, Security dashboard
├── monitoring/            # Prometheus & Alertmanager configs
├── cyber-claude/          # Security scanning & analysis toolkit
├── docker-compose.yml     # 6 services configuration
├── SETUP.bat / SETUP.sh   # One-command setup (Windows/Unix)
├── README.md              # This file
├── TECHNICAL_SUMMARY.md   # Full architecture & API reference
└── SECURITY_ANALYSIS.md   # Security assessment & recommendations
```

---

## 🤝 Support

For issues or questions:
1. Check logs: `docker compose logs backend`
2. Review `TECHNICAL_SUMMARY.md` for architecture details
3. Visit API docs at http://localhost:5001/docs

---

**Made with ❤️ for emergency management professionals**
