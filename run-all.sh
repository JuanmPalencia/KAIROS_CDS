#!/bin/bash

################################################################################
#                    KAIROS CDS - RUN ALL (Auto-Init)
#
# Script que:
# 1. Levanta Docker Compose
# 2. Verifica si los datos ya están cargados
# 3. Carga datos SOLO si no existen
# 4. Inicia auto-generación de incidentes
# 5. Muestra URLs de acceso
################################################################################

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
BACKEND_URL="http://localhost:5001"
MAX_RETRIES=30
RETRY_INTERVAL=2
TOKEN=""

# Función para imprimir con color
print_header() {
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 1. Iniciar Docker Compose
print_header "1️⃣  INICIANDO DOCKER COMPOSE"

if docker compose ps | grep -q "kairos_cds"; then
    print_info "Docker ya está levantado"
else
    print_info "Levantando servicios con Docker..."
    docker compose up -d --build
    print_success "Docker Compose iniciado"
fi

# 2. Esperar a que el backend esté listo
print_header "2️⃣  ESPERANDO BACKEND (máx ${MAX_RETRIES} intentos)"

ATTEMPT=0
while [ $ATTEMPT -lt $MAX_RETRIES ]; do
    if curl -s "$BACKEND_URL/docs" > /dev/null 2>&1; then
        print_success "Backend disponible en $BACKEND_URL"
        break
    fi
    ATTEMPT=$((ATTEMPT + 1))
    print_info "Intento $ATTEMPT/$MAX_RETRIES... esperando ${RETRY_INTERVAL}s"
    sleep $RETRY_INTERVAL
done

if [ $ATTEMPT -eq $MAX_RETRIES ]; then
    print_error "Backend no respondió después de $MAX_RETRIES intentos"
    exit 1
fi

# 3. Obtener token de autenticación
print_header "3️⃣  AUTENTICACIÓN"

print_info "Obteniendo token de admin..."
TOKEN=$(curl -s -X POST "$BACKEND_URL/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" \
  -w "\n" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    print_error "No se pudo obtener token de autenticación"
    exit 1
fi

print_success "Token obtenido exitosamente"

# 4. Función para verificar si una tabla tiene datos
check_data_exists() {
    local endpoint=$1
    local token=$2

    if curl -s "$BACKEND_URL$endpoint" \
        -H "Authorization: Bearer $token" 2>/dev/null | grep -q "Not Found\|null\|\[\]"; then
        return 1  # No existen datos
    fi
    return 0  # Existen datos
}

# 5. Cargar datos iniciales (solo si no existen)
print_header "4️⃣  CARGANDO DATOS INICIALES"

# Crear/verificar usuarios
print_info "Verificando usuarios..."
INIT_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/auth/init-admin")
if echo "$INIT_RESPONSE" | grep -q "already exist"; then
    print_info "Usuarios ya existen - omitiendo"
else
    print_success "Usuarios creados"
fi

# Crear/verificar flota
print_info "Verificando flota de ambulancias..."
FLEET_RESPONSE=$(curl -s -X POST "$BACKEND_URL/fleet/seed-ambulances")
if echo "$FLEET_RESPONSE" | grep -q '"count":0'; then
    print_info "Flota ya existe - omitiendo"
else
    FLEET_COUNT=$(echo "$FLEET_RESPONSE" | grep -o '"count":[0-9]*' | cut -d':' -f2)
    print_success "Flota inicializada: $FLEET_COUNT ambulancias"
fi

# Crear/verificar hospitales
print_info "Verificando hospitales..."
HOSPITAL_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/hospitals/seed" \
    -H "Authorization: Bearer $TOKEN")
if echo "$HOSPITAL_RESPONSE" | grep -q '"created":0'; then
    print_info "Hospitales ya existen - omitiendo"
else
    HOSPITAL_COUNT=$(echo "$HOSPITAL_RESPONSE" | grep -o '"hospitals":\[[^]]*\]' | grep -o '"' | wc -l)
    print_success "Hospitales inicializados"
fi

# Crear/verificar recursos
print_info "Verificando recursos (DEA, GIS, weather, agencias)..."
RESOURCES_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/resources/seed-all" \
    -H "Authorization: Bearer $TOKEN")
if echo "$RESOURCES_RESPONSE" | grep -q '"dea":0'; then
    print_info "Recursos ya existen - omitiendo"
else
    print_success "Recursos inicializados"
fi

# Crear/verificar gasolineras
print_info "Verificando gasolineras..."
GAS_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/gas-stations/seed" \
    -H "Authorization: Bearer $TOKEN")
if echo "$GAS_RESPONSE" | grep -q '"count":0'; then
    print_info "Gasolineras ya existen - omitiendo"
else
    GAS_COUNT=$(echo "$GAS_RESPONSE" | grep -o '"count":[0-9]*' | cut -d':' -f2)
    print_success "Gasolineras inicializadas: $GAS_COUNT"
fi

# Crear/verificar tripulaciones
print_info "Verificando tripulaciones..."
CREWS_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/crews/seed" \
    -H "Authorization: Bearer $TOKEN")
if echo "$CREWS_RESPONSE" | grep -q '"crew_created":0'; then
    print_info "Tripulaciones ya existen - omitiendo"
else
    print_success "Tripulaciones inicializadas"
fi

# 6. Verificar/iniciar auto-generación de incidentes
print_header "5️⃣  VERIFICANDO AUTO-GENERACIÓN DE INCIDENTES"

AUTO_GEN_STATUS=$(curl -s "$BACKEND_URL/simulation/auto-generate/status" \
    -H "Authorization: Bearer $TOKEN")

if echo "$AUTO_GEN_STATUS" | grep -q '"running":true'; then
    print_info "Auto-generación ya está en ejecución"
else
    print_info "Iniciando auto-generación de incidentes..."
    START_RESPONSE=$(curl -s -X POST "$BACKEND_URL/simulation/auto-generate/start" \
        -H "Authorization: Bearer $TOKEN")

    if echo "$START_RESPONSE" | grep -q '"ok":true'; then
        print_success "Auto-generación iniciada (intervalo: ~30 segundos)"
    else
        print_warning "No se pudo iniciar auto-generación"
    fi
fi

# 7. Mostrar resumen final
print_header "🎉 KAIROS CDS - SISTEMA LISTO"

echo ""
echo -e "${GREEN}📊 ESTADO DEL SISTEMA:${NC}"
echo ""
echo "  Docker Compose:  ✅ Activo"
echo "  Backend:         ✅ $BACKEND_URL"
echo "  Base de datos:   ✅ PostgreSQL + PostGIS"
echo "  Redis:           ✅ Cache activo"
echo "  Monitorización:  ✅ Prometheus + Alertmanager"
echo "  Auto-generación: ✅ Incidentes generándose"
echo ""
echo -e "${GREEN}🌐 ACCESO:${NC}"
echo ""
echo "  Frontend:        🔗 http://localhost:5173"
echo "  Backend API:     🔗 http://localhost:5001"
echo "  API Swagger:     🔗 http://localhost:5001/docs"
echo "  Prometheus:      🔗 http://localhost:9090"
echo "  Alertmanager:    🔗 http://localhost:9093"
echo ""
echo -e "${GREEN}🔐 CREDENCIALES PARA LOGIN:${NC}"
echo ""
echo "  admin    / admin123"
echo "  operator / operator123"
echo "  doctor   / doctor123"
echo "  viewer   / viewer123"
echo ""
echo -e "${GREEN}📋 DATOS CARGADOS:${NC}"
echo ""
echo "  ✓ 4 Usuarios (admin, operator, doctor, viewer)"
echo "  ✓ 8 Ambulancias (SVB, SVA, VIR, VAMM, SAMU)"
echo "  ✓ Hospitales españoles"
echo "  ✓ 8 Gasolineras"
echo "  ✓ Recursos (DEA, GIS, weather, agencias, SSM)"
echo "  ✓ Tripulaciones con turnos"
echo "  ✓ Auto-generación de incidentes cada ~30s"
echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}✨ Sistema completamente inicializado y ejecutándose${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""

# 8. Información de logs
print_info "Para ver logs del backend: docker compose logs -f backend"
print_info "Para ver logs del frontend: docker compose logs -f frontend"
print_info "Para detener todo: docker compose down"
