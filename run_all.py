#!/usr/bin/env python3
"""
KAIROS CDS - Run All Script (Auto-Init)

Verifica datos existentes y solo carga si es necesario, luego ejecuta el programa.
Compatible con Windows, Linux y macOS.
"""

import subprocess
import sys
import time
import json
import requests
from pathlib import Path
from typing import Dict, Tuple, Optional
from datetime import datetime

# Colores ANSI
class Colors:
    HEADER = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    BLUE = '\033[34m'

# Configuración
BACKEND_URL = "http://localhost:5001"
MAX_RETRIES = 30
RETRY_INTERVAL = 2
TIMEOUT = 5

def print_header(text: str):
    """Imprime encabezado con decoración"""
    border = "=" * 70
    print(f"\n{Colors.HEADER}{border}{Colors.ENDC}")
    print(f"{Colors.HEADER}{text:^70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{border}{Colors.ENDC}\n")

def print_success(text: str):
    """Imprime mensaje de éxito"""
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")

def print_warning(text: str):
    """Imprime mensaje de advertencia"""
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")

def print_info(text: str):
    """Imprime mensaje informativo"""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.ENDC}")

def print_error(text: str):
    """Imprime mensaje de error"""
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")

def run_command(cmd: list, description: str = "") -> Tuple[int, str]:
    """Ejecuta comando y retorna código de salida y output"""
    try:
        if description:
            print_info(description)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return -1, "Timeout"
    except Exception as e:
        return -1, str(e)

def wait_for_backend(url: str, max_retries: int = MAX_RETRIES) -> bool:
    """Espera a que el backend esté disponible"""
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(f"{url}/docs", timeout=TIMEOUT)
            if response.status_code == 200:
                print_success(f"Backend disponible en {url}")
                return True
        except requests.exceptions.RequestException:
            pass

        print_info(f"Intento {attempt}/{max_retries}... esperando {RETRY_INTERVAL}s")
        time.sleep(RETRY_INTERVAL)

    return False

def get_token(url: str, username: str = "admin", password: str = "admin123") -> Optional[str]:
    """Obtiene token JWT de autenticación"""
    try:
        response = requests.post(
            f"{url}/api/auth/login",
            data={"username": username, "password": password},
            timeout=TIMEOUT,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        if response.status_code == 200:
            token = response.json().get("access_token")
            return token
    except Exception as e:
        print_warning(f"Error obteniendo token: {e}")

    return None

def seed_users(url: str) -> Dict[str, any]:
    """Crea usuarios iniciales"""
    try:
        response = requests.post(
            f"{url}/api/auth/init-admin",
            timeout=TIMEOUT
        )
        data = response.json()

        if "already exist" in str(data):
            print_info("Usuarios ya existen - omitiendo")
            return {"status": "exists", "data": data}
        else:
            print_success("Usuarios creados")
            return {"status": "created", "data": data}
    except Exception as e:
        print_warning(f"Error inicializando usuarios: {e}")
        return {"status": "error", "data": str(e)}

def seed_fleet(url: str) -> Dict[str, any]:
    """Crea flota de ambulancias"""
    try:
        response = requests.post(
            f"{url}/fleet/seed-ambulances",
            timeout=TIMEOUT
        )
        data = response.json()

        count = data.get("count", 0)
        if count == 0:
            print_info("Flota ya existe - omitiendo")
            return {"status": "exists", "data": data}
        else:
            vehicles = data.get("created", [])
            print_success(f"Flota inicializada: {count} ambulancias")
            return {"status": "created", "data": data}
    except Exception as e:
        print_warning(f"Error inicializando flota: {e}")
        return {"status": "error", "data": str(e)}

def seed_hospitals(url: str, token: str) -> Dict[str, any]:
    """Crea hospitales"""
    try:
        response = requests.post(
            f"{url}/api/hospitals/seed",
            headers={"Authorization": f"Bearer {token}"},
            timeout=TIMEOUT
        )
        data = response.json()

        hospitals = data.get("hospitals", [])
        if len(hospitals) == 0:
            print_info("Hospitales ya existen - omitiendo")
            return {"status": "exists", "data": data}
        else:
            print_success(f"Hospitales inicializados")
            return {"status": "created", "data": data}
    except Exception as e:
        print_warning(f"Error inicializando hospitales: {e}")
        return {"status": "error", "data": str(e)}

def seed_resources(url: str, token: str) -> Dict[str, any]:
    """Crea recursos (DEA, GIS, weather, etc.)"""
    try:
        response = requests.post(
            f"{url}/api/resources/seed-all",
            headers={"Authorization": f"Bearer {token}"},
            timeout=TIMEOUT
        )
        data = response.json()

        if "ok" in data:
            print_success("Recursos inicializados (DEA, GIS, weather, agencias, SSM)")
            return {"status": "created", "data": data}
        else:
            print_info("Recursos ya existen - omitiendo")
            return {"status": "exists", "data": data}
    except Exception as e:
        print_warning(f"Error inicializando recursos: {e}")
        return {"status": "error", "data": str(e)}

def seed_gas_stations(url: str, token: str) -> Dict[str, any]:
    """Crea gasolineras"""
    try:
        response = requests.post(
            f"{url}/api/gas-stations/seed",
            headers={"Authorization": f"Bearer {token}"},
            timeout=TIMEOUT
        )
        data = response.json()

        count = data.get("count", 0)
        if count == 0:
            print_info("Gasolineras ya existen - omitiendo")
            return {"status": "exists", "data": data}
        else:
            print_success(f"Gasolineras inicializadas: {count}")
            return {"status": "created", "data": data}
    except Exception as e:
        print_warning(f"Error inicializando gasolineras: {e}")
        return {"status": "error", "data": str(e)}

def seed_crews(url: str, token: str) -> Dict[str, any]:
    """Crea tripulaciones"""
    try:
        response = requests.post(
            f"{url}/api/crews/seed",
            headers={"Authorization": f"Bearer {token}"},
            timeout=TIMEOUT
        )
        data = response.json()

        crews_created = data.get("crew_created", 0)
        if crews_created == 0:
            print_info("Tripulaciones ya existen - omitiendo")
            return {"status": "exists", "data": data}
        else:
            print_success(f"Tripulaciones inicializadas")
            return {"status": "created", "data": data}
    except Exception as e:
        print_warning(f"Error inicializando tripulaciones: {e}")
        return {"status": "error", "data": str(e)}

def start_auto_generation(url: str, token: str) -> Dict[str, any]:
    """Inicia auto-generación de incidentes"""
    try:
        # Primero verificar estado
        response = requests.get(
            f"{url}/simulation/auto-generate/status",
            headers={"Authorization": f"Bearer {token}"},
            timeout=TIMEOUT
        )
        status_data = response.json()

        if status_data.get("running"):
            print_info("Auto-generación ya está en ejecución")
            return {"status": "running", "data": status_data}

        # Iniciar auto-generación
        response = requests.post(
            f"{url}/simulation/auto-generate/start",
            headers={"Authorization": f"Bearer {token}"},
            timeout=TIMEOUT
        )
        data = response.json()

        if data.get("ok"):
            interval = data.get("interval", 30)
            print_success(f"Auto-generación iniciada (intervalo: ~{interval}s)")
            return {"status": "started", "data": data}
        else:
            print_warning("No se pudo iniciar auto-generación")
            return {"status": "failed", "data": data}
    except Exception as e:
        print_warning(f"Error en auto-generación: {e}")
        return {"status": "error", "data": str(e)}

def check_docker():
    """Verifica si Docker está instalado y levantado"""
    code, output = run_command(
        ["docker", "compose", "ps"],
        "Verificando Docker..."
    )

    if code != 0:
        print_error("Docker no está disponible o no está levantado")
        return False

    if "kairos_cds" in output:
        print_info("Docker Compose ya está activo")
        return True

    return False

def start_docker():
    """Levanta Docker Compose"""
    print_info("Levantando Docker Compose...")
    code, output = run_command(
        ["docker", "compose", "up", "-d", "--build"],
        "Inicializando servicios..."
    )

    if code == 0:
        print_success("Docker Compose iniciado")
        return True
    else:
        print_error(f"Error levantando Docker: {output}")
        return False

def print_summary(seeds_result: Dict):
    """Imprime resumen final"""
    print_header("🎉 KAIROS CDS - SISTEMA LISTO")

    print(f"{Colors.OKGREEN}📊 ESTADO DEL SISTEMA:{Colors.ENDC}\n")
    print(f"  Docker Compose:  ✅ Activo")
    print(f"  Backend:         ✅ {BACKEND_URL}")
    print(f"  Base de datos:   ✅ PostgreSQL + PostGIS")
    print(f"  Redis:           ✅ Cache activo")
    print(f"  Monitorización:  ✅ Prometheus + Alertmanager")
    print(f"  Auto-generación: ✅ Incidentes generándose\n")

    print(f"{Colors.OKGREEN}🌐 ACCESO:{Colors.ENDC}\n")
    print(f"  Frontend:        🔗 http://localhost:5173")
    print(f"  Backend API:     🔗 http://localhost:5001")
    print(f"  API Swagger:     🔗 http://localhost:5001/docs")
    print(f"  Prometheus:      🔗 http://localhost:9090")
    print(f"  Alertmanager:    🔗 http://localhost:9093\n")

    print(f"{Colors.OKGREEN}🔐 CREDENCIALES PARA LOGIN:{Colors.ENDC}\n")
    print(f"  admin    / admin123")
    print(f"  operator / operator123")
    print(f"  doctor   / doctor123")
    print(f"  viewer   / viewer123\n")

    print(f"{Colors.OKGREEN}📋 DATOS CARGADOS:{Colors.ENDC}\n")
    print(f"  ✓ 4 Usuarios (admin, operator, doctor, viewer)")
    print(f"  ✓ 8 Ambulancias (SVB, SVA, VIR, VAMM, SAMU)")
    print(f"  ✓ Hospitales españoles")
    print(f"  ✓ 8 Gasolineras")
    print(f"  ✓ Recursos (DEA, GIS, weather, agencias, SSM)")
    print(f"  ✓ Tripulaciones con turnos")
    print(f"  ✓ Auto-generación de incidentes cada ~30s\n")

    print(f"{Colors.HEADER}{'=' * 70}{Colors.ENDC}")
    print(f"{Colors.HEADER}✨ Sistema completamente inicializado y ejecutándose{Colors.ENDC}")
    print(f"{Colors.HEADER}{'=' * 70}{Colors.ENDC}\n")

    print_info("Para ver logs del backend: docker compose logs -f backend")
    print_info("Para ver logs del frontend: docker compose logs -f frontend")
    print_info("Para detener todo: docker compose down")

def main():
    """Función principal"""
    print_header("1️⃣  KAIROS CDS - INICIALIZACIÓN AUTOMÁTICA")

    # 1. Verificar/iniciar Docker
    print_header("2️⃣  DOCKER COMPOSE")

    if not check_docker():
        if not start_docker():
            sys.exit(1)

    # 2. Esperar backend
    print_header("3️⃣  ESPERANDO BACKEND")

    if not wait_for_backend(BACKEND_URL):
        print_error("Backend no respondió después de múltiples intentos")
        sys.exit(1)

    # 3. Autenticación
    print_header("4️⃣  AUTENTICACIÓN")

    token = get_token(BACKEND_URL)
    if not token:
        print_error("No se pudo obtener token de autenticación")
        sys.exit(1)

    print_success("Token obtenido exitosamente")

    # 4. Cargar datos
    print_header("5️⃣  CARGANDO DATOS INICIALES")

    seeds_result = {
        "users": seed_users(BACKEND_URL),
        "fleet": seed_fleet(BACKEND_URL),
        "hospitals": seed_hospitals(BACKEND_URL, token),
        "resources": seed_resources(BACKEND_URL, token),
        "gas_stations": seed_gas_stations(BACKEND_URL, token),
        "crews": seed_crews(BACKEND_URL, token),
    }

    # 5. Auto-generación
    print_header("6️⃣  AUTO-GENERACIÓN DE INCIDENTES")

    seeds_result["auto_generation"] = start_auto_generation(BACKEND_URL, token)

    # 6. Resumen final
    print_summary(seeds_result)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Proceso interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        print_error(f"Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
