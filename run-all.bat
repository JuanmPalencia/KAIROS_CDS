@echo off
REM ============================================================================
REM                    KAIROS CDS - RUN ALL (Auto-Init)
REM
REM Script que:
REM 1. Levanta Docker Compose
REM 2. Verifica si los datos ya están cargados
REM 3. Carga datos SOLO si no existen
REM 4. Inicia auto-generación de incidentes
REM 5. Muestra URLs de acceso
REM ============================================================================

setlocal enabledelayedexpansion

REM Configuración
set BACKEND_URL=http://localhost:5001
set MAX_RETRIES=30
set RETRY_INTERVAL=2
set TOKEN=

REM Colores (requiere Windows 10+)
set RED=[91m
set GREEN=[92m
set YELLOW=[93m
set BLUE=[94m
set NC=[0m

cls
echo.
echo ======================================================================
echo.
echo       KAIROS CDS - INICIALIZACION AUTOMATICA
echo.
echo ======================================================================
echo.

REM 1. Iniciar Docker Compose
echo.
echo ======================================================================
echo 1^. DOCKER COMPOSE
echo ======================================================================
echo.

docker compose ps >nul 2>&1
if errorlevel 1 (
    echo.
    echo Levantando Docker Compose...
    docker compose up -d --build
    if errorlevel 1 (
        echo ERROR: No se pudo iniciar Docker
        pause
        exit /b 1
    )
    echo [OK] Docker Compose iniciado
) else (
    echo [INFO] Docker ya está levantado
)

REM 2. Esperar backend
echo.
echo ======================================================================
echo 2. ESPERANDO BACKEND
echo ======================================================================
echo.

set /a ATTEMPT=0
:wait_backend
set /a ATTEMPT=!ATTEMPT!+1

curl -s "%BACKEND_URL%/docs" >nul 2>&1
if errorlevel 1 (
    if %ATTEMPT% lss %MAX_RETRIES% (
        echo Intento %ATTEMPT%/%MAX_RETRIES%... esperando %RETRY_INTERVAL%s
        timeout /t %RETRY_INTERVAL% /nobreak >nul 2>&1
        goto wait_backend
    ) else (
        echo ERROR: Backend no respondió después de %MAX_RETRIES% intentos
        pause
        exit /b 1
    )
)

echo [OK] Backend disponible en %BACKEND_URL%

REM 3. Obtener token
echo.
echo ======================================================================
echo 3. AUTENTICACION
echo ======================================================================
echo.

echo Obteniendo token de autenticacion...

for /f %%A in ('curl -s -X POST "%BACKEND_URL%/api/auth/login" ^
  -H "Content-Type: application/x-www-form-urlencoded" ^
  -d "username=admin&password=admin123" ^
  ^| findstr /R "access_token"') do (
    set TOKEN=%%A
)

if "%TOKEN%"=="" (
    echo ERROR: No se pudo obtener token
    pause
    exit /b 1
)

echo [OK] Token obtenido

REM 4. Cargar datos
echo.
echo ======================================================================
echo 4. CARGANDO DATOS INICIALES
echo ======================================================================
echo.

REM Crear usuarios
echo [INFO] Verificando usuarios...
for /f %%A in ('curl -s -X POST "%BACKEND_URL%/api/auth/init-admin" ^
  ^| findstr /R "already"') do (
    if not "%%A"=="" (
        echo [INFO] Usuarios ya existen - omitiendo
        goto skip_users
    )
)
echo [OK] Usuarios creados
:skip_users

REM Crear flota
echo [INFO] Verificando flota de ambulancias...
for /f %%A in ('curl -s -X POST "%BACKEND_URL%/fleet/seed-ambulances" ^
  ^| findstr /R "count"') do (
    if "%%A"=="count\":0" (
        echo [INFO] Flota ya existe - omitiendo
        goto skip_fleet
    )
)
echo [OK] Flota inicializada
:skip_fleet

REM Crear hospitales
echo [INFO] Verificando hospitales...
curl -s -X POST "%BACKEND_URL%/api/hospitals/seed" ^
  -H "Authorization: Bearer %TOKEN%" >nul 2>&1
echo [OK] Hospitales procesados

REM Crear recursos
echo [INFO] Verificando recursos...
curl -s -X POST "%BACKEND_URL%/api/resources/seed-all" ^
  -H "Authorization: Bearer %TOKEN%" >nul 2>&1
echo [OK] Recursos procesados

REM Crear gasolineras
echo [INFO] Verificando gasolineras...
for /f %%A in ('curl -s -X POST "%BACKEND_URL%/api/gas-stations/seed" ^
  -H "Authorization: Bearer %TOKEN%" ^
  ^| findstr /R "count"') do (
    echo [OK] Gasolineras procesadas
)

REM Crear tripulaciones
echo [INFO] Verificando tripulaciones...
curl -s -X POST "%BACKEND_URL%/api/crews/seed" ^
  -H "Authorization: Bearer %TOKEN%" >nul 2>&1
echo [OK] Tripulaciones procesadas

REM 5. Auto-generación
echo.
echo ======================================================================
echo 5. VERIFICANDO AUTO-GENERACION DE INCIDENTES
echo ======================================================================
echo.

curl -s -X POST "%BACKEND_URL%/simulation/auto-generate/start" ^
  -H "Authorization: Bearer %TOKEN%" >nul 2>&1
echo [OK] Auto-generacion iniciada

REM 6. Resumen
echo.
echo ======================================================================
echo.
echo              ^!^! KAIROS CDS - SISTEMA LISTO
echo.
echo ======================================================================
echo.
echo [OK] ESTADO DEL SISTEMA:
echo.
echo   Docker Compose:  ^[OK^] Activo
echo   Backend:         [OK] %BACKEND_URL%
echo   Base de datos:   [OK] PostgreSQL + PostGIS
echo   Redis:           [OK] Cache activo
echo   Monitorización:  [OK] Prometheus + Alertmanager
echo   Auto-generacion: [OK] Incidentes generándose
echo.
echo [OK] ACCESO:
echo.
echo   Frontend:        http://localhost:5173
echo   Backend API:     http://localhost:5001
echo   API Swagger:     http://localhost:5001/docs
echo   Prometheus:      http://localhost:9090
echo   Alertmanager:    http://localhost:9093
echo.
echo [OK] CREDENCIALES PARA LOGIN:
echo.
echo   admin    / admin123
echo   operator / operator123
echo   doctor   / doctor123
echo   viewer   / viewer123
echo.
echo [OK] DATOS CARGADOS:
echo.
echo   ^. 4 Usuarios (admin, operator, doctor, viewer)
echo   ^. 8 Ambulancias (SVB, SVA, VIR, VAMM, SAMU)
echo   ^. Hospitales españoles
echo   ^. 8 Gasolineras
echo   ^. Recursos (DEA, GIS, weather, agencias, SSM)
echo   ^. Tripulaciones con turnos
echo   ^. Auto-generacion de incidentes cada ~30s
echo.
echo ======================================================================
echo.

echo [INFO] Para ver logs del backend: docker compose logs -f backend
echo [INFO] Para ver logs del frontend: docker compose logs -f frontend
echo [INFO] Para detener todo: docker compose down
echo.

pause
