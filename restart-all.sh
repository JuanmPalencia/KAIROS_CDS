#!/bin/bash
# ============================================================================
# restart-all.sh - Reinicia todos los procesos de KAIROS CDS (Linux/macOS)
# ============================================================================
# Funcionalidad:
# 1. Mata el proceso Vite dev server (puertos 5173 o 5174)
# 2. Reinicia servicios Docker (sin borrar datos)
# 3. Espera a que el backend responda en /health
# 4. Lanza el frontend dev server en segundo plano
# 5. Muestra URLs de acceso

set -e

echo ""
echo "============================================================================"
echo " KAIROS CDS - RESTART ALL PROCESSES (Linux/macOS)"
echo "============================================================================"
echo ""

# --- 1. Matar procesos del dev server en puertos 5173 y 5174 ---
echo "[1/4] Killing Vite dev server (ports 5173, 5174)..."
fuser -k 5173/tcp 2>/dev/null || true
fuser -k 5174/tcp 2>/dev/null || true
sleep 1

# --- 2. Reiniciar servicios Docker ---
echo "[2/4] Restarting Docker services..."
docker compose restart
sleep 2

# --- 3. Esperar a que el backend responda en /health ---
echo "[3/4] Waiting for backend health..."
MAX_ATTEMPTS=30
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    ATTEMPT=$((ATTEMPT + 1))

    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5001/health 2>/dev/null || echo "000")

    if [ "$HTTP_CODE" = "200" ]; then
        echo "Backend is ready!"
        sleep 1
        break
    fi

    echo "  Attempt $ATTEMPT/$MAX_ATTEMPTS - waiting..."
    sleep 2
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo "ERROR: Backend did not respond after $MAX_ATTEMPTS attempts"
    exit 1
fi

# --- 4. Lanzar frontend dev server ---
echo "[4/4] Starting frontend dev server..."
cd frontend
npm run dev &
cd ..
sleep 3

# --- 5. Mostrar resumen ---
echo ""
echo "============================================================================"
echo " RESTART COMPLETED SUCCESSFULLY"
echo "============================================================================"
echo ""
echo " Frontend Dev Server: http://localhost:5173"
echo "                      (or http://localhost:5174 if 5173 is busy)"
echo ""
echo " Backend API:        http://localhost:5001"
echo " API Docs:           http://localhost:5001/docs"
echo ""
echo " Docker Status:      Run 'docker compose ps' to verify all services"
echo ""
echo " Default Credentials:"
echo "   admin    / admin123  (Admin)"
echo "   operator / operator123 (Operator)"
echo "   doctor   / doctor123 (Doctor)"
echo "   viewer   / viewer123 (Viewer)"
echo ""
echo "============================================================================"
echo ""
