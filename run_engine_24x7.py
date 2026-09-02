"""Pulse AI Discovery Engine — 24x7 Self-Healing Supervisor Daemon.

Supervises and ensures continuous 24*7 uptime for:
1. FastAPI Backend Engine (Port 8000)
2. Next.js Frontend Intelligence Dashboard (Port 3000)

Monitors HTTP health and automatically restarts any terminated or non-responsive process.
"""

import os
import sys
import time
import signal
import logging
import subprocess
import urllib.request
import urllib.error
from datetime import datetime

# Setup logging
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "engine_24x7.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [Supervisor] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding="utf-8", mode="a"),
    ],
)
logger = logging.getLogger("PulseEngineSupervisor")

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")

BACKEND_URL = "http://127.0.0.1:8000/api/v1/health"
FRONTEND_URL = "http://127.0.0.1:3000"

backend_process = None
frontend_process = None
running = True


def signal_handler(sig, frame):
    global running
    logger.info("Termination signal received. Shutting down 24x7 Engine Supervisor...")
    running = False
    stop_services()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def start_backend():
    global backend_process
    logger.info("Starting FastAPI Backend Engine on port 8000...")
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--app-dir",
        "backend",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
    ]
    try:
        backend_process = subprocess.Popen(
            cmd,
            cwd=ROOT_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        logger.info(f"FastAPI Backend process spawned (PID: {backend_process.pid})")
    except Exception as e:
        logger.error(f"Failed to spawn backend process: {e}")


def start_frontend():
    global frontend_process
    logger.info("Starting Next.js Frontend Dashboard on port 3000...")
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    cmd = [npm_cmd, "--prefix", "frontend", "run", "dev"]
    try:
        frontend_process = subprocess.Popen(
            cmd,
            cwd=ROOT_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        logger.info(f"Next.js Frontend process spawned (PID: {frontend_process.pid})")
    except Exception as e:
        logger.error(f"Failed to spawn frontend process: {e}")


def check_http_health(url: str, timeout: int = 5) -> bool:
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "PulseSupervisor/1.0"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.status in (200, 304)
    except Exception:
        return False


def stop_services():
    global backend_process, frontend_process
    if backend_process:
        try:
            logger.info(f"Terminating Backend (PID: {backend_process.pid})...")
            backend_process.terminate()
            backend_process.wait(timeout=5)
        except Exception:
            backend_process.kill()
        backend_process = None

    if frontend_process:
        try:
            logger.info(f"Terminating Frontend (PID: {frontend_process.pid})...")
            frontend_process.terminate()
            frontend_process.wait(timeout=5)
        except Exception:
            frontend_process.kill()
        frontend_process = None


def main():
    logger.info("================================================================")
    logger.info("   PULSE AI DISCOVERY ENGINE — 24*7 SUPERVISOR WATCHDOG")
    logger.info("================================================================")
    logger.info(f"Root Directory: {ROOT_DIR}")
    logger.info("Initializing services...")

    start_backend()
    start_frontend()

    # Initial grace period for servers to boot
    logger.info("Warming up services (10 seconds)...")
    time.sleep(10)

    backend_fails = 0
    frontend_fails = 0

    while running:
        # Check backend process & HTTP
        backend_alive = backend_process is not None and backend_process.poll() is None
        backend_healthy = check_http_health(BACKEND_URL)

        if not backend_alive or not backend_healthy:
            backend_fails += 1
            logger.warning(
                f"Backend check failed ({backend_fails}/3) - Alive: {backend_alive}, HTTP Healthy: {backend_healthy}"
            )
            if backend_fails >= 3 or not backend_alive:
                logger.error("Restarting FastAPI Backend Engine...")
                if backend_process:
                    try:
                        backend_process.kill()
                    except Exception:
                        pass
                start_backend()
                backend_fails = 0
                time.sleep(5)
        else:
            backend_fails = 0

        # Check frontend process & HTTP
        frontend_alive = frontend_process is not None and frontend_process.poll() is None
        frontend_healthy = check_http_health(FRONTEND_URL)

        if not frontend_alive or not frontend_healthy:
            frontend_fails += 1
            logger.warning(
                f"Frontend check failed ({frontend_fails}/3) - Alive: {frontend_alive}, HTTP Healthy: {frontend_healthy}"
            )
            if frontend_fails >= 3 or not frontend_alive:
                logger.error("Restarting Next.js Frontend...")
                if frontend_process:
                    try:
                        frontend_process.kill()
                    except Exception:
                        pass
                start_frontend()
                frontend_fails = 0
                time.sleep(5)
        else:
            frontend_fails = 0

        # Heartbeat log every 60 seconds
        now = datetime.now().strftime("%H:%M:%S")
        logger.info(
            f"[{now}] 24x7 Heartbeat: Backend (8000): OK | Frontend (3000): OK"
        )
        time.sleep(15)


if __name__ == "__main__":
    main()
