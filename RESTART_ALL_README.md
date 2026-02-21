# RESTART ALL - KAIROS CDS

Reinicia completamente todos los procesos del sistema KAIROS CDS sin perder datos.

---

## 🚀 Quick Start

### Windows
```bash
# Opción 1: Doble clic (interfaz gráfica)
restart-all.bat

# Opción 2: Línea de comandos
cmd /c restart-all.bat
```

### Linux / macOS
```bash
bash restart-all.sh
```

---

## ¿Qué Hace Este Script?

El script ejecuta los siguientes pasos en orden:

| Paso | Acción | Descripción |
|------|--------|-------------|
| 1️⃣  | Kill Vite Dev Server | Mata procesos en puertos 5173 y 5174 |
| 2️⃣  | Docker Restart | Reinicia todos los containers (`docker compose restart`) |
| 3️⃣  | Health Check | Espera a que el backend responda en `/health` |
| 4️⃣  | Frontend Launch | Lanza el dev server de React/Vite en segundo plano |
| 5️⃣  | Summary | Muestra URLs y credenciales de acceso |

---

## 📋 Pre-requisitos

- ✅ Docker y Docker Compose instalados y funcionando
- ✅ Node.js 18+ y npm instalados
- ✅ Proyecto ya inicializado (primero ejecutar `run-all.bat` o `run-all.sh`)
- ✅ El directorio actual debe ser el raíz de KAIROS CDS

---

## 🔄 Diferencias: Restart vs Run-All

| Feature | `run-all.bat` | `restart-all.bat` |
|---------|---------------|-------------------|
| **Crea containers** | ✅ Sí | ❌ No |
| **Destruye datos** | ❌ No (auto-skip) | ❌ No |
| **Reinicia servicios** | ✅ (`docker compose up`) | ✅ (`docker compose restart`) |
| **Carga seeds** | ✅ (si no existen) | ❌ No (reutiliza datos) |
| **Tiempo de inicio** | 🐌 30-60s | ⚡ 5-10s |
| **Cuándo usarlo** | Primera vez / setup | Reinicio limpio sin reset |

---

## 🌍 URLs Después del Restart

Una vez completado, accede a:

```
📱 Frontend:   http://localhost:5173
🔧 Backend:    http://localhost:5001
📚 API Docs:   http://localhost:5001/docs
📊 Prometheus: http://localhost:9090
⚠️  Alertmanager: http://localhost:9093
```

---

## 👤 Credenciales por Defecto

Después de la primera ejecución con `run-all.bat`, usa estas credenciales:

| Username | Password | Rol | Permisos |
|----------|----------|-----|----------|
| `admin` | `admin123` | ADMIN | Acceso completo |
| `operator` | `operator123` | OPERATOR | Despacho de ambulancias |
| `doctor` | `doctor123` | DOCTOR | Clínica/ePCR |
| `viewer` | `viewer123` | VIEWER | Solo lectura |

---

## 🛠️ Troubleshooting

### "Backend did not respond"
```bash
# Verifica que Docker esté ejecutando
docker compose ps

# Mira los logs del backend
docker compose logs backend

# Si falla completamente, reinicia Docker
docker compose down -v
run-all.bat  # Ejecuta setup limpio
```

### "Port 5173 is already in use"
El script intenta matar procesos automáticamente. Si aún está en uso:

**Windows:**
```bash
netstat -ano | findstr ":5173"
taskkill /PID <PID> /F
```

**Linux/macOS:**
```bash
fuser -k 5173/tcp
```

### "docker compose command not found"
Instala Docker Desktop desde https://www.docker.com/products/docker-desktop

---

## 📊 Docker Services Restarted

```
Container          Status      Port(s)
─────────────────────────────────────
kairos-db          Up ✅       5432
kairos-redis       Up ✅       6379
kairos-backend     Up ✅       5001
kairos-prometheus  Up ✅       9090
kairos-alertmgr    Up ✅       9093
```

Verifica con:
```bash
docker compose ps
```

---

## 💾 Data Persistence

✅ **Datos PRESERVADOS después de restart:**
- ✅ Usuarios (admin, operator, doctor, viewer)
- ✅ Vehículos (8 ambulancias)
- ✅ Incidentes (histórico)
- ✅ Hospitales, recursos, estaciones de gasolina
- ✅ Turnos de personal

❌ **Si necesitas borrar TODO y empezar de cero:**
```bash
docker compose down -v  # Destruye volúmenes
run-all.bat             # Reinicia del cero (tarda 30-60s)
```

---

## ⚙️ Comportamiento Técnico

### 1️⃣ Kill Vite Server
```bash
# Windows: mata procesos en 5173 y 5174
# Linux/macOS: fuser -k 5173/tcp 2>/dev/null || true
```

### 2️⃣ Docker Compose Restart
```bash
docker compose restart
```
- **NO** destruye volúmenes (`-v`)
- **Detiene** cada container y lo vuelve a iniciar
- La DB y datos persisten

### 3️⃣ Health Check Loop
```bash
# Polling a http://localhost:5001/health
# Máximo: 30 intentos × 2s = 60 segundos
```

### 4️⃣ Frontend Dev Server
```bash
cd frontend
npm run dev &  # En segundo plano
```

---

## 📝 Logs & Debugging

Ver logs en vivo:
```bash
# Backend
docker compose logs -f backend

# Frontend (otra terminal)
cd frontend && npm run dev

# Redis
docker compose logs -f redis

# Base de datos
docker compose logs -f db
```

---

## 🔗 Related Documentation

- 📖 [`RUN_ALL_README.md`](./RUN_ALL_README.md) - Setup inicial del proyecto
- 📖 [`MEMORY.md`](./MEMORY.md) - Quick reference y configuración
- 📖 [`docker-compose.yml`](./docker-compose.yml) - Arquitectura de servicios

---

## 🆘 Need Help?

```bash
# Verificar estado de Docker
docker compose ps

# Ver configuración de red
docker compose config

# Acceder a la consola del backend
docker compose exec backend bash

# Limpiar todo (incluyendo datos)
docker compose down -v
```

---

**Version:** 1.0
**Last Updated:** 2025-02-21
**Compatible with:** KAIROS CDS v1.0.0+
