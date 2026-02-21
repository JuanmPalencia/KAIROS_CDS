# KAIROS CDS - QUICKSTART

## ⚡ Inicio Rápido (30 segundos)

### Windows
```
run-all.bat
```
Haz doble clic. ¡Listo!

### Linux / macOS
```bash
bash run-all.sh
# o
python3 run_all.py
```

---

## 🌐 URLs Después de Ejecutar

| Servicio | URL |
|----------|-----|
| Frontend | http://localhost:5173 |
| Backend | http://localhost:5001 |
| API Docs | http://localhost:5001/docs |
| Prometheus | http://localhost:9090 |
| Alertmanager | http://localhost:9093 |

---

## 🔐 Login Credentials

```
admin    / admin123
operator / operator123
doctor   / doctor123
viewer   / viewer123
```

---

## ✅ ¿Qué Hace el Script?

1. ✅ Levanta Docker Compose
2. ✅ Espera Backend
3. ✅ Obtiene Token JWT
4. ✅ **Verifica** si datos existen
5. ✅ **Carga** solo lo que falta
6. ✅ Inicia auto-generación de incidentes
7. ✅ Muestra acceso al sistema

**Idempotente**: Puedes ejecutar múltiples veces sin problemas.

---

## 📊 Datos que se Cargan

- **Usuarios**: admin, operator, doctor, viewer
- **Flota**: 8 ambulancias (SVB, SVA, VIR, VAMM, SAMU)
- **Gasolineras**: 8 (GAS-001 a GAS-008)
- **Hospitales**: Principales ciudades españolas
- **Tripulaciones**: Crews con turnos adaptativos
- **Incidentes**: Auto-generación cada ~30 segundos

---

## 🛠️ Comandos Útiles

```bash
# Ver logs en tiempo real
docker compose logs -f backend

# Detener todo
docker compose down

# Reiniciar
docker compose restart

# Limpiar BD
docker compose down -v
```

---

## 📚 Documentación Completa

Ver: `RUN_ALL_README.md`

---

¡Disfruta! 🚑
