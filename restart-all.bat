@echo off
REM ============================================================================
REM restart-all.bat - Reinicia todos los procesos de KAIROS CDS (Windows)
REM ============================================================================
REM Funcionalidad:
REM 1. Mata el proceso Vite dev server (puertos 5173 o 5174)
REM 2. Reinicia servicios Docker (sin borrar datos)
REM 3. Espera a que el backend responda en /health
REM 4. Lanza el frontend dev server en segundo plano
REM 5. Muestra URLs de acceso

setlocal enabledelayedexpansion

echo.
echo ============================================================================
echo  KAIROS CDS - RESTART ALL PROCESSES (Windows)
echo ============================================================================
echo.

REM --- 1. Matar procesos del dev server en puertos 5173 y 5174 ---
echo [1/4] Killing Vite dev server (ports 5173, 5174)...
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":5173"') do (
    taskkill /PID %%a /F >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":5174"') do (
    taskkill /PID %%a /F >nul 2>&1
)
timeout /t 1 /nobreak >nul

REM --- 2. Reiniciar servicios Docker ---
echo [2/4] Restarting Docker services...
docker compose restart
if errorlevel 1 (
    echo ERROR: Docker compose restart failed. Check Docker daemon.
    exit /b 1
)
timeout /t 2 /nobreak >nul

REM --- 3. Esperar a que el backend responda en /health ---
echo [3/4] Waiting for backend health...
setlocal enabledelayedexpansion
set "max_attempts=30"
set "attempt=0"

:health_check_loop
set /a attempt+=1
if !attempt! gtr !max_attempts! (
    echo ERROR: Backend did not respond after %max_attempts% attempts
    exit /b 1
)

for /f "tokens=*" %%i in ('curl -s -o /dev/null -w "%%{http_code}" http://localhost:5001/health 2^>nul') do set "http_code=%%i"

if "!http_code!"=="200" (
    echo Backend is ready!
    timeout /t 1 /nobreak >nul
    goto frontend_launch
)

echo   Attempt !attempt!/%max_attempts% - waiting...
timeout /t 2 /nobreak >nul
goto health_check_loop

REM --- 4. Lanzar frontend dev server ---
:frontend_launch
echo [4/4] Starting frontend dev server...
cd frontend
start /b npm run dev
cd ..
timeout /t 3 /nobreak >nul

REM --- 5. Mostrar resumen ---
echo.
echo ============================================================================
echo  RESTART COMPLETED SUCCESSFULLY
echo ============================================================================
echo.
echo  Frontend Dev Server: http://localhost:5173
echo                       (or http://localhost:5174 if 5173 is busy)
echo.
echo  Backend API:        http://localhost:5001
echo  API Docs:           http://localhost:5001/docs
echo.
echo  Docker Status:      Run 'docker compose ps' to verify all services
echo.
echo  Default Credentials:
echo    admin    / admin123  (Admin)
echo    operator / operator123 (Operator)
echo    doctor   / doctor123 (Doctor)
echo    viewer   / viewer123 (Viewer)
echo.
echo ============================================================================
echo.
pause
