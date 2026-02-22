@echo off
REM ============================================================================
REM KAIROS CDS - Unified Setup & Run Script (Windows)
REM ============================================================================

setlocal enabledelayedexpansion

cls
echo.
echo  ╔════════════════════════════════════════════════════════════════╗
echo  ║                   KAIROS CDS v1.0.0                            ║
echo  ║            Emergency Fleet Management Digital Twin            ║
echo  ╚════════════════════════════════════════════════════════════════╝
echo.

REM Check Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker not found. Please install Docker Desktop.
    pause
    exit /b 1
)
echo ✅ Docker is ready

REM 1. Start Docker Compose
echo.
echo Starting services (PostgreSQL, Redis, Backend, Frontend)...
docker compose up -d --build
if errorlevel 1 (
    echo ❌ Failed to start Docker Compose
    pause
    exit /b 1
)
echo ✅ Services started

REM 2. Wait for Backend (max 60 seconds)
echo.
echo Waiting for API to be ready...
set ATTEMPTS=0
:wait_loop
set /a ATTEMPTS=!ATTEMPTS!+1
curl -s http://localhost:5001/docs >nul 2>&1
if errorlevel 1 (
    if !ATTEMPTS! lss 30 (
        echo  Attempt !ATTEMPTS!/30...
        timeout /t 2 /nobreak >nul
        goto wait_loop
    ) else (
        echo ❌ Backend timeout. Check logs: docker compose logs backend
        pause
        exit /b 1
    )
)
echo ✅ API is ready

REM 3. Initialize data
echo.
echo Initializing data...
curl -s -X POST http://localhost:5001/api/auth/init-admin -d "username=admin&password=admin123" >nul 2>&1
echo ✅ Data initialized

REM 4. Start auto-generation
echo.
echo Starting incident auto-generation...
curl -s -X POST "http://localhost:5001/simulation/auto-generate/start?interval=15" >nul 2>&1
curl -s -X POST "http://localhost:5001/simulation/lifecycle/start" >nul 2>&1
echo ✅ Auto-generation active

REM 5. Summary
echo.
echo  ╔════════════════════════════════════════════════════════════════╗
echo  ║                    SETUP COMPLETE! ✅                          ║
echo  ╠════════════════════════════════════════════════════════════════╣
echo  ║  Frontend ................. http://localhost:5173             ║
echo  ║  API ....................... http://localhost:5001             ║
echo  ║  API Docs .................. http://localhost:5001/docs       ║
echo  ║                                                                ║
echo  ║  Credentials:                                                  ║
echo  ║    admin    / admin123                                         ║
echo  ║    operator / operator123                                      ║
echo  ║    doctor  / doctor123                                         ║
echo  ║    viewer  / viewer123                                         ║
echo  ╚════════════════════════════════════════════════════════════════╝
echo.
echo  📌 To restart services: docker compose restart
echo  📌 To view logs:        docker compose logs -f
echo  📌 To stop:             docker compose down
echo.

pause
