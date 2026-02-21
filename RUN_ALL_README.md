# KAIROS CDS - Run All Scripts

Este documento explica cómo usar los scripts de inicialización automática para ejecutar KAIROS CDS.

## 📋 Descripción General

Los scripts `run-all` hacen lo siguiente:

1. **Levanta Docker Compose** - Inicia todos los servicios (backend, frontend, DB, Redis, etc.)
2. **Verifica datos existentes** - Comprueba si usuarios, flota, hospitales, etc. ya existen
3. **Carga datos solo si es necesario** - Si faltan datos, los carga automáticamente
4. **Inicia auto-generación de incidentes** - Sistema empieza a generar emergencias simuladas
5. **Muestra información de acceso** - URLs, credenciales y estado del sistema

## 🚀 Uso Rápido

### Windows (Recomendado)

Simplemente haz doble clic en:
```
run-all.bat
```

O desde PowerShell/CMD:
```cmd
.\run-all.bat
```

### Linux / macOS

```bash
# Opción 1: Python (Recomendado - más completo)
python3 run_all.py

# Opción 2: Bash
chmod +x run-all.sh
./run-all.sh
```

---

## 🔍 ¿Qué Hace Exactamente?

### Paso 1: Verificar Docker
```bash
docker compose ps
```
- Si Docker está levantado → continúa
- Si no está levantado → lo inicia automáticamente

### Paso 2: Esperar Backend (hasta 30 intentos)
```bash
curl http://localhost:5001/docs
```
- Verifica cada 2 segundos si el backend está disponible
- Máximo espera: ~60 segundos

### Paso 3: Obtener Token de Autenticación
```bash
POST /api/auth/login
body: username=admin&password=admin123
```
- Obtiene JWT token para hacer requests autenticados

### Paso 4: Cargar Datos (SOLO SI NO EXISTEN)

#### 4.1 Usuarios
```bash
POST /api/auth/init-admin
```
- Si retorna `"already exist"` → omite
- Si es nuevo → crea admin, operator, doctor, viewer

#### 4.2 Flota
```bash
POST /fleet/seed-ambulances
```
- Si retorna `"count":0` → omite (ya existen)
- Si es nuevo → crea 8 ambulancias (SVB, SVA, VIR, VAMM, SAMU)

#### 4.3 Hospitales
```bash
POST /api/hospitals/seed
Authorization: Bearer {token}
```
- Crea hospitales españoles si no existen

#### 4.4 Recursos
```bash
POST /api/resources/seed-all
Authorization: Bearer {token}
```
- DEAs (desfibriladores)
- GIS layers
- Weather integration
- Agencies (Bomberos, Policía)
- SSM zones

#### 4.5 Gasolineras
```bash
POST /api/gas-stations/seed
Authorization: Bearer {token}
```
- Crea 8 gasolineras (GAS-001 a GAS-008)

#### 4.6 Tripulaciones
```bash
POST /api/crews/seed
Authorization: Bearer {token}
```
- Crea crew members con roles
- Asigna turnos adaptativos

### Paso 5: Auto-Generación de Incidentes
```bash
POST /simulation/auto-generate/start
Authorization: Bearer {token}
```
- Inicia generación automática de emergencias
- Intervalo: ~30 segundos entre incidentes
- 14 tipos de incidentes disponibles
- Asignación IA automática de vehículos

---

## ✅ Salida Esperada

### Caso 1: Primera ejecución (datos no existen)

```
✅ Usuarios creados
✅ Flota inicializada: 8 ambulancias
✅ Hospitales inicializados
✅ Recursos inicializados (DEA, GIS, weather, agencias, SSM)
✅ Gasolineras inicializadas: 8
✅ Tripulaciones inicializadas
✅ Auto-generación iniciada (intervalo: ~30 segundos)
```

### Caso 2: Re-ejecutación (datos ya existen)

```
ℹ️  Usuarios ya existen - omitiendo
ℹ️  Flota ya existe - omitiendo
ℹ️  Hospitales ya existen - omitiendo
ℹ️  Recursos ya existen - omitiendo
ℹ️  Gasolineras ya existen - omitiendo
ℹ️  Tripulaciones ya existen - omitiendo
ℹ️  Auto-generación ya está en ejecución
```

---

## 🌐 Acceso Después de la Inicialización

Una vez que el script termina, puedes acceder a:

| Servicio | URL | Descripción |
|----------|-----|-------------|
| **Frontend** | http://localhost:5173 | Dashboard en React |
| **Backend API** | http://localhost:5001 | API REST FastAPI |
| **API Docs** | http://localhost:5001/docs | Swagger interactivo |
| **Prometheus** | http://localhost:9090 | Métricas y alertas |
| **Alertmanager** | http://localhost:9093 | Gestión de alertas |

---

## 🔐 Credenciales de Login

Usa estas credenciales en http://localhost:5173:

| Usuario | Contraseña | Rol | Acceso |
|---------|-----------|-----|--------|
| `admin` | `admin123` | ADMIN | Panel completo + usuarios + auditoría |
| `operator` | `operator123` | OPERATOR | Despacho + asignaciones |
| `doctor` | `doctor123` | DOCTOR | ePCR + pacientes + hospitales |
| `viewer` | `viewer123` | VIEWER | Dashboard (solo lectura) |

---

## 📊 Datos que se Cargan

### Usuarios (4)
- admin (ADMIN)
- operator (OPERATOR)
- doctor (DOCTOR)
- viewer (VIEWER)

### Flota (8 ambulancias)
- SVB-001, SVB-002, SVB-003 (Soporte Vital Básico)
- SVA-001, SVA-002 (Soporte Vital Avanzado)
- VIR-001 (Intervención Rápida)
- VAMM-001 (Asistencia Múltiple)
- SAMU-001 (Atención Urgencia)

### Gasolineras (8)
- GAS-001 a GAS-008

### Hospitales
- Hospitales españoles principales

### Otros Recursos
- DEAs (desfibriladores) geolocalizados
- Capas GIS configurables
- Integración meteorológica
- Agencias (Bomberos, Policía)
- SSM zones (System Status Management)

### Tripulaciones
- 12+ crew members
- Roles: Médico, Enfermero, TES, Conductor
- Turnos adaptativos: Día, Noche, Guardia 24h

### Incidentes (Auto-generados)
- 14 tipos: CARDIO, RESPIRATORY, TRAUMA, BURN, POISONING, OBSTETRIC, PEDIATRIC, PSYCHIATRIC, FALL, ALLERGIC, DIABETIC, DROWNING, GENERAL, NEUROLOGICAL
- Generación automática cada ~30 segundos
- Asignación IA automática

---

## 🔧 Solución de Problemas

### El script no corre en Windows
```
Error: El archivo script.py no se reconoce como un programa interno
```

**Solución:** Usa `run-all.bat` en su lugar (diseñado específicamente para Windows)

### Docker no está instalado
```
Error: docker: command not found
```

**Solución:** Instala Docker Desktop desde https://docker.com/products/docker-desktop

### Backend no responde después de 30 intentos
```
Error: Backend no respondió después de 30 intentos
```

**Solución:**
```bash
# Ver logs del backend
docker compose logs backend

# Reiniciar servicios
docker compose restart backend
```

### Token de autenticación no se obtiene
```
ERROR: No se pudo obtener token de autenticación
```

**Solución:**
1. Verifica que los usuarios se crearon correctamente
2. Prueba con credenciales manuales en http://localhost:5001/docs

### Puerto ya está en uso
```
Error: port is already allocated
```

**Solución:**
```bash
# Liberar puertos
docker compose down

# O cambiar puertos en docker-compose.yml
```

---

## 📝 Archivos de Script Disponibles

### `run-all.bat` (Windows)
- Formato: Batch (.bat)
- Mejor para: Windows PowerShell / CMD
- Ventaja: Nativo para Windows

### `run-all.sh` (Linux/macOS)
- Formato: Bash
- Mejor para: Linux / macOS / WSL
- Ventaja: Portable entre sistemas UNIX

### `run_all.py` (Multiplataforma - Recomendado)
- Formato: Python 3
- Mejor para: Todos los sistemas operativos
- Ventaja: Más robusto, mejor manejo de errores
- Requisito: `python3` + librerías (requests)

---

## 🔄 Flujo de Ejecución

```
┌─────────────────────────────────────┐
│   Ejecutar run-all.sh / .bat / .py  │
└──────────────┬──────────────────────┘
               │
        ┌──────▼──────┐
        │ Docker UP?  │
        └──────┬──────┘
        NO │   │ YES
    ┌───────┘   └───────────────┐
    │                           │
    ▼                           ▼
 Start Docker              Wait Backend
    │                       (max 30 retry)
    └───────────┬───────────────┘
                │
        ┌───────▼───────┐
        │ Backend OK?   │
        └───────┬───────┘
                │
        ┌───────▼────────┐
        │ Get JWT Token  │
        └───────┬────────┘
                │
   ┌────────────▼────────────┐
   │  Check Data Exists      │
   │  ────────────────       │
   │  • Users?               │
   │  • Fleet?               │
   │  • Hospitals?           │
   │  • Resources?           │
   │  • Gas Stations?        │
   │  • Crews?               │
   └────────────┬────────────┘
                │
    ┌───────────▼───────────┐
    │ Load Missing Data     │
    │ (Idempotent)          │
    └───────────┬───────────┘
                │
    ┌───────────▼──────────────┐
    │ Start Incident           │
    │ Auto-Generation          │
    └───────────┬──────────────┘
                │
        ┌───────▼───────┐
        │ Print Summary │
        │ & URLs        │
        └───────┬───────┘
                │
    ┌───────────▼───────────┐
    │  ✨ System Ready ✨    │
    │                       │
    │ Frontend: :5173       │
    │ Backend:  :5001       │
    │ API Docs: :5001/docs  │
    └───────────────────────┘
```

---

## 📞 Información Adicional

### Logs en Tiempo Real
```bash
# Backend
docker compose logs -f backend

# Frontend
docker compose logs -f frontend

# Todo
docker compose logs -f
```

### Detener Todo
```bash
docker compose down
```

### Limpiar y Reiniciar
```bash
# Eliminar volúmenes (borra BD)
docker compose down -v

# Levantar nuevamente
python3 run_all.py
# o
./run-all.sh
# o
run-all.bat
```

### Ver Métricas
```bash
# Prometheus
http://localhost:9090

# Alertas
http://localhost:9093
```

---

## ✨ Características del Sistema

Una vez inicializado, KAIROS CDS incluye:

✅ **Dashboard en tiempo real** - Mapa Leaflet con actualización cada 2s via WebSocket
✅ **10 módulos de IA** - Severity, Demand, ETA, Anomalies, Maintenance, Vision, Chat, Traffic, Recommendations, Assignment
✅ **Blockchain BSV** - Auditoría inmutable con Merkle trees
✅ **Ciberseguridad** - JWT, RBAC, encryption AES-256-GCM, HIBP breach check, rate limiting
✅ **ePCR/MCI** - Electronic Patient Care Report + MCI Triage (START protocol)
✅ **Tripulaciones** - Gestión de crews con turnos adaptativos
✅ **Analytics** - KPIs, snapshots, export CSV/PDF
✅ **Monitorización** - Prometheus + Alertmanager

---

## 🎯 Próximos Pasos

1. Accede a http://localhost:5173
2. Loguéate con `admin` / `admin123`
3. Ve al Dashboard
4. Verás ambulancias en tiempo real
5. Los incidentes se generan cada ~30s
6. Asigna manualmente o usa la IA

¡Disfruta de KAIROS CDS! 🚑🗺️
