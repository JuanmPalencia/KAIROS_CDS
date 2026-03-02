#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os

# Force UTF-8 on Windows
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

"""
KAIROS CDS - Unified Setup & Run Script
======================================

Usage:
  python3 run_all.py              # Start/restart services (keep data)
  python3 run_all.py --reset      # Full reset (delete all data & restart)
  python3 run_all.py --logs       # View live logs
  python3 run_all.py --stop       # Stop all services
  python3 run_all.py --security   # Run cyber-claude security scan
"""

import subprocess
import sys
import time
import os
import shutil
from pathlib import Path

try:
    import requests
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "requests"], check=True)
    import requests

class KAIROS:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.docker_cmd = self._detect_docker()
        self.backend_url = "http://localhost:5001"
        self.max_retries = 30
        self.retry_delay = 2

    def _detect_docker(self):
        if shutil.which("docker"):
            return "docker"
        raise RuntimeError("Docker not found")

    def _run_cmd(self, cmd, shell=False):
        try:
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            env["NODE_ENV"] = "production"
            result = subprocess.run(cmd, shell=shell, capture_output=True, text=True,
                                   encoding="utf-8", errors="replace", timeout=120, env=env)
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 1, "", "Timeout"
        except Exception as e:
            return 1, "", str(e)

    def _print_banner(self, text):
        width = 80
        print("\n" + "=" * width)
        print(f"  {text.center(width - 4)}")
        print("=" * width + "\n")

    def _print_success(self, text):
        print(f"✅ {text}")

    def _print_error(self, text):
        print(f"❌ {text}")
        sys.exit(1)

    def _print_info(self, text):
        print(f"ℹ️  {text}")

    def check_docker(self):
        self._print_info("Checking Docker...")
        code, _, _ = self._run_cmd(f"{self.docker_cmd} ps")
        if code != 0:
            self._print_error("Docker is not running")
        self._print_success("Docker is ready")

    def start_services(self):
        self._print_info("Starting services...")
        code, _, stderr = self._run_cmd(f"{self.docker_cmd} compose up -d --build", shell=True)
        if code != 0:
            self._print_error(f"Failed: {stderr}")
        self._print_success("Services started")

    def wait_for_backend(self):
        self._print_info(f"Waiting for API...")
        for attempt in range(self.max_retries):
            try:
                response = requests.get(f"{self.backend_url}/docs", timeout=2)
                if response.status_code == 200:
                    self._print_success("API is ready")
                    return
            except:
                pass
            print(f"  Attempt {attempt + 1}/{self.max_retries}...", end="\r")
            time.sleep(self.retry_delay)
        self._print_error(f"Backend timeout")

    def initialize_data(self):
        self._print_info("Initializing database...")
        try:
            # Initialize auth users
            requests.post(f"{self.backend_url}/api/auth/init-admin",
                data={"username": "admin", "password": "admin123"}, timeout=10)

            # Seed ambulances/fleet
            try:
                requests.post(f"{self.backend_url}/fleet/seed-ambulances", timeout=10)
            except:
                pass

            # Seed hospitals
            try:
                requests.post(f"{self.backend_url}/hospitals/seed", timeout=10)
            except:
                pass

            # Seed gas stations
            try:
                requests.post(f"{self.backend_url}/gas-stations/seed", timeout=10)
            except:
                pass

            # Seed crews
            try:
                requests.post(f"{self.backend_url}/crews/seed", timeout=10)
            except:
                pass

            # Seed DEA locations
            try:
                requests.post(f"{self.backend_url}/dea/seed", timeout=10)
            except:
                pass

            # Seed GIS layers
            try:
                requests.post(f"{self.backend_url}/gis/seed", timeout=10)
            except:
                pass

            # Seed agency resources
            try:
                requests.post(f"{self.backend_url}/agencies/seed", timeout=10)
            except:
                pass

            self._print_success("Database initialized with fleet, hospitals, and stations")
        except:
            self._print_info("Database already initialized")

    def start_autogen(self):
        self._print_info("Starting incident auto-generation...")
        try:
            requests.post(f"{self.backend_url}/simulation/auto-generate/start?interval=15", timeout=5)
            requests.post(f"{self.backend_url}/simulation/lifecycle/start", timeout=5)
            self._print_success("Auto-generation started")
        except:
            self._print_info("Auto-generation already running")

    def run_security_scan(self):
        self._print_banner("CYBERSECURITY SCAN")
        cyber_path = self.project_root / "cyber-claude"
        if not cyber_path.exists():
            self._print_error("cyber-claude folder not found")
        os.chdir(cyber_path)
        if not (cyber_path / "dist").exists():
            self._print_info("Building cyber-claude...")
            code, _, _ = self._run_cmd("npm install && npm run build", shell=True)
            if code != 0:
                self._print_error("Build failed")
        self._print_info("Running security scan...")
        code, stdout, stderr = self._run_cmd("node dist/cli/index.js scan", shell=True)
        if code == 0:
            print(stdout)
            self._print_success("Scan completed")
        else:
            print(stderr)
            self._print_error("Scan failed")

    def reset_database(self):
        self._print_banner("RESET DATABASE")
        confirm = input("Delete all data? (yes/no): ")
        if confirm.lower() != "yes":
            self._print_info("Cancelled")
            return
        self._print_info("Stopping containers...")
        self._run_cmd(f"{self.docker_cmd} compose down -v", shell=True)
        self._print_success("Volumes deleted")
        self.start_services()
        self.wait_for_backend()
        self.initialize_data()
        self.start_autogen()

    def view_logs(self):
        self._print_banner("LIVE LOGS")
        self._print_info("Press Ctrl+C to stop")
        time.sleep(1)
        self._run_cmd(f"{self.docker_cmd} compose logs -f backend", shell=True)

    def stop_services(self):
        self._print_info("Stopping services...")
        self._run_cmd(f"{self.docker_cmd} compose down", shell=True)
        self._print_success("Stopped (data preserved)")

    def show_access_info(self):
        print("\n" + "=" * 80)
        print("  ✅ KAIROS CDS - READY".center(80))
        print("=" * 80 + """

  🌐 URLS:
     • Frontend ........ http://localhost:5173
     • API ............ http://localhost:5001
     • API Docs ....... http://localhost:5001/docs
     • Prometheus ..... http://localhost:9090

  🔐 Credentials:
     • admin / admin123 (full access)
     • operator / operator123 (dispatch)
     • doctor / doctor123 (clinical)
     • viewer / viewer123 (read-only)

  📊 Security:
     • Run: python3 run_all.py --security
     • Cyber-claude scans included

""" + "=" * 80 + "\n")

    def run(self, args):
        if not args:
            self._print_banner("KAIROS CDS - STARTUP")
            self.check_docker()
            self.start_services()
            self.wait_for_backend()
            self.initialize_data()
            self.start_autogen()
            self.show_access_info()
        elif "--reset" in args:
            self.check_docker()
            self.reset_database()
            self.show_access_info()
        elif "--logs" in args:
            self.view_logs()
        elif "--stop" in args:
            self.stop_services()
        elif "--security" in args:
            self.run_security_scan()
        elif "--help" in args or "-h" in args:
            print(__doc__)
        else:
            self._print_error(f"Unknown: {args[0]}")

if __name__ == "__main__":
    try:
        kairos = KAIROS()
        kairos.run(sys.argv[1:])
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ {e}")
        sys.exit(1)
