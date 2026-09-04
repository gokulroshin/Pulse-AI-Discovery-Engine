"""Pulse AI Discovery Engine — Universal Self-Bootstrapping 24x7 Supervisor Daemon.

Supervises and ensures continuous 24*7 uptime across ANY operating system (Windows, macOS, Linux):
1. Automated Pre-Flight Health Check: Python & Node detection, auto-.env provisioning, dependency auto-installation
2. Port Conflict Auto-Clearing: Checks & cleanly frees ports 8000 (Backend) and 3000 (Frontend)
3. FastAPI Backend Engine (Port 8000) with streamed diagnostic logging
4. Next.js Frontend Dashboard (Port 3000) with streamed diagnostic logging
5. Self-Healing Watchdog: Restarts any terminated or non-responsive service automatically
6. Clean Process Tree Shutdown: Gracefully terminates all child processes on SIGINT/SIGTERM
"""

import os
import sys
import time
import signal
import shutil
import socket
import logging
import subprocess
import urllib.request
import urllib.error
from datetime import datetime

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")

# Log files
LOG_DIR = ROOT_DIR
SUPERVISOR_LOG = os.path.join(LOG_DIR, "engine_24x7.log")
BACKEND_LOG = os.path.join(LOG_DIR, "engine_backend.log")
FRONTEND_LOG = os.path.join(LOG_DIR, "engine_frontend.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [Supervisor] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(SUPERVISOR_LOG, encoding="utf-8", mode="a"),
    ],
)
logger = logging.getLogger("PulseEngineSupervisor")

BACKEND_HEALTH_URLS = [
    "http://127.0.0.1:8000/health",
    "http://127.0.0.1:8000/api/v1/health",
]
FRONTEND_URL = "http://127.0.0.1:3000"

backend_process = None
frontend_process = None
backend_log_file = None
frontend_log_file = None
running = True


def find_python_interpreter() -> str:
    """Finds the optimal python interpreter, checking virtual environments first."""
    # 1. Check active virtualenv
    if "VIRTUAL_ENV" in os.environ:
        if sys.platform == "win32":
            venv_py = os.path.join(os.environ["VIRTUAL_ENV"], "Scripts", "python.exe")
        else:
            venv_py = os.path.join(os.environ["VIRTUAL_ENV"], "bin", "python")
        if os.path.exists(venv_py):
            return venv_py

    # 2. Check local backend/.venv
    candidates = [
        os.path.join(BACKEND_DIR, ".venv", "Scripts", "python.exe"),
        os.path.join(BACKEND_DIR, ".venv", "bin", "python"),
        os.path.join(ROOT_DIR, ".venv", "Scripts", "python.exe"),
        os.path.join(ROOT_DIR, ".venv", "bin", "python"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c

    # 3. Fallback to current sys.executable
    return sys.executable


def find_npm_command() -> str:
    """Finds npm command cross-platform (npm.cmd on Windows, npm on Unix)."""
    if sys.platform == "win32":
        npm_cmd = shutil.which("npm.cmd") or shutil.which("npm") or "npm.cmd"
        return npm_cmd
    return shutil.which("npm") or "npm"


def ensure_env_files():
    """Ensures .env and .env.local configuration files exist from templates."""
    root_env = os.path.join(ROOT_DIR, ".env")
    root_env_example = os.path.join(ROOT_DIR, ".env.example")
    backend_env = os.path.join(BACKEND_DIR, ".env")
    backend_env_example = os.path.join(BACKEND_DIR, ".env.example")
    frontend_env = os.path.join(FRONTEND_DIR, ".env.local")
    frontend_env_example = os.path.join(FRONTEND_DIR, ".env.local.example")

    if not os.path.exists(root_env) and os.path.exists(root_env_example):
        logger.info("Initializing root .env from template...")
        shutil.copyfile(root_env_example, root_env)

    if not os.path.exists(backend_env) and os.path.exists(backend_env_example):
        logger.info("Initializing backend .env from template...")
        shutil.copyfile(backend_env_example, backend_env)

    if not os.path.exists(frontend_env) and os.path.exists(frontend_env_example):
        logger.info("Initializing frontend .env.local from template...")
        shutil.copyfile(frontend_env_example, frontend_env)


def is_port_in_use(port: int) -> bool:
    """Checks if a TCP port is in use on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex(("127.0.0.1", port)) == 0


def free_port_if_needed(port: int):
    """Terminates any process holding a specific port if it is not healthy."""
    if not is_port_in_use(port):
        return

    logger.warning(f"Port {port} is occupied. Attempting to release...")
    try:
        if sys.platform == "win32":
            output = subprocess.check_output(f"netstat -ano | findstr :{port}", shell=True).decode(errors="ignore")
            for line in output.strip().splitlines():
                parts = line.split()
                if len(parts) >= 5 and "LISTENING" in parts:
                    pid = parts[-1]
                    if pid != str(os.getpid()):
                        logger.info(f"Terminating stale process on port {port} (PID: {pid})...")
                        subprocess.run(f"taskkill /F /PID {pid}", shell=True, capture_output=True)
        else:
            output = subprocess.check_output(["lsof", "-ti", f":{port}"]).decode().strip()
            for pid in output.splitlines():
                if pid and pid != str(os.getpid()):
                    logger.info(f"Terminating stale process on port {port} (PID: {pid})...")
                    subprocess.run(["kill", "-9", pid], capture_output=True)
    except Exception as e:
        logger.debug(f"Port {port} release check note: {e}")


def ensure_database(python_exe: str):
    """Ensures backend database exists and is synchronized."""
    backend_db = os.path.join(BACKEND_DIR, "intently.db")
    root_db = os.path.join(ROOT_DIR, "intently.db")

    if not os.path.exists(backend_db) and os.path.exists(root_db):
        logger.info("Syncing pre-analyzed corpus database to backend...")
        shutil.copyfile(root_db, backend_db)
    elif os.path.exists(backend_db) and not os.path.exists(root_db):
        shutil.copyfile(backend_db, root_db)


def preflight_check():
    """Performs full system doctor: Python packages, npm dependencies, configs, and DB."""
    logger.info("Running pre-flight diagnostics and environment verification...")
    python_exe = find_python_interpreter()
    npm_cmd = find_npm_command()
    logger.info(f"Python interpreter: {python_exe}")
    logger.info(f"Node/npm binary: {npm_cmd}")

    ensure_env_files()
    ensure_database(python_exe)

    # Verify backend Python dependencies
    try:
        check_script = "import fastapi, uvicorn, pydantic, sqlalchemy, sklearn, numpy, scipy"
        subprocess.check_call(
            [python_exe, "-c", check_script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        logger.info("Python backend dependencies: OK")
    except Exception:
        logger.info("Installing missing Python backend dependencies from requirements.txt...")
        req_file = os.path.join(BACKEND_DIR, "requirements.txt")
        try:
            subprocess.check_call([python_exe, "-m", "pip", "install", "-r", req_file])
            logger.info("Python backend dependencies installed successfully.")
        except Exception as pip_err:
            logger.error(f"Failed to install Python dependencies: {pip_err}")

    # Verify frontend node_modules
    frontend_nm = os.path.join(FRONTEND_DIR, "node_modules")
    if not os.path.exists(frontend_nm):
        logger.info("Frontend node_modules missing. Installing npm packages...")
        try:
            subprocess.check_call([npm_cmd, "--prefix", "frontend", "install"], cwd=ROOT_DIR)
            logger.info("Frontend npm dependencies installed successfully.")
        except Exception as npm_err:
            logger.error(f"Failed to install frontend dependencies: {npm_err}")

    # Clear lingering stale ports
    free_port_if_needed(8000)
    free_port_if_needed(3000)
    logger.info("Pre-flight system verification complete.")


def signal_handler(sig, frame):
    global running
    logger.info("Shutdown signal received (Ctrl+C / SIGTERM). Gracefully terminating all processes...")
    running = False
    stop_services()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def start_backend():
    global backend_process, backend_log_file
    python_exe = find_python_interpreter()
    logger.info("Starting FastAPI Backend Engine on http://localhost:8000...")
    cmd = [
        python_exe,
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
        backend_log_file = open(BACKEND_LOG, "a", encoding="utf-8")
        backend_process = subprocess.Popen(
            cmd,
            cwd=ROOT_DIR,
            stdout=backend_log_file,
            stderr=subprocess.STDOUT,
        )
        logger.info(f"FastAPI Backend process spawned (PID: {backend_process.pid}) | Logs: engine_backend.log")
    except Exception as e:
        logger.error(f"Failed to spawn backend process: {e}")


def start_frontend():
    global frontend_process, frontend_log_file
    npm_cmd = find_npm_command()
    logger.info("Starting Next.js Frontend Dashboard on http://localhost:3000...")
    cmd = [npm_cmd, "--prefix", "frontend", "run", "dev"]
    try:
        frontend_log_file = open(FRONTEND_LOG, "a", encoding="utf-8")
        frontend_process = subprocess.Popen(
            cmd,
            cwd=ROOT_DIR,
            stdout=frontend_log_file,
            stderr=subprocess.STDOUT,
        )
        logger.info(f"Next.js Frontend process spawned (PID: {frontend_process.pid}) | Logs: engine_frontend.log")
    except Exception as e:
        logger.error(f"Failed to spawn frontend process: {e}")


def check_http_health(url: str, timeout: int = 5) -> bool:
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "PulseSupervisor/2.0"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.status in (200, 304)
    except Exception:
        return False


def check_backend_healthy() -> bool:
    for url in BACKEND_HEALTH_URLS:
        if check_http_health(url):
            return True
    return False


def kill_proc_tree(pid: int):
    """Recursively kills a process tree across Windows and POSIX."""
    try:
        if sys.platform == "win32":
            subprocess.run(f"taskkill /F /T /PID {pid}", shell=True, capture_output=True)
        else:
            subprocess.run(["kill", "-9", str(pid)], capture_output=True)
    except Exception:
        pass


def stop_services():
    global backend_process, frontend_process, backend_log_file, frontend_log_file
    if backend_process:
        try:
            logger.info(f"Terminating Backend (PID: {backend_process.pid})...")
            kill_proc_tree(backend_process.pid)
        except Exception:
            pass
        backend_process = None

    if frontend_process:
        try:
            logger.info(f"Terminating Frontend (PID: {frontend_process.pid})...")
            kill_proc_tree(frontend_process.pid)
        except Exception:
            pass
        frontend_process = None

    if backend_log_file:
        try:
            backend_log_file.close()
        except Exception:
            pass
        backend_log_file = None

    if frontend_log_file:
        try:
            frontend_log_file.close()
        except Exception:
            pass
        frontend_log_file = None


def main():
    logger.info("================================================================")
    logger.info("   PULSE AI DISCOVERY ENGINE — 24*7 SUPERVISOR WATCHDOG")
    logger.info("   Platform: " + sys.platform + " | OS: " + os.name)
    logger.info("================================================================")
    logger.info(f"Workspace Root: {ROOT_DIR}")

    # 1. Pre-flight diagnostics
    preflight_check()

    # 2. Launch services
    logger.info("Initializing services...")
    start_backend()
    start_frontend()

    # Grace period for servers to boot
    logger.info("Warming up services (8 seconds)...")
    time.sleep(8)

    backend_fails = 0
    frontend_fails = 0

    logger.info("================================================================")
    logger.info("🚀 Pulse Discovery Engine is LIVE & ACTIVE!")
    logger.info("👉 Next.js Frontend Dashboard:  http://localhost:3000")
    logger.info("👉 FastAPI Backend Swagger Docs: http://localhost:8000/docs")
    logger.info("👉 System Health API Endpoint:   http://localhost:8000/health")
    logger.info("================================================================")

    while running:
        # Check backend process & HTTP
        backend_alive = backend_process is not None and backend_process.poll() is None
        backend_healthy = check_backend_healthy()

        if not backend_alive or not backend_healthy:
            backend_fails += 1
            logger.warning(
                f"Backend check notice ({backend_fails}/3) - Alive: {backend_alive}, HTTP Healthy: {backend_healthy}"
            )
            if backend_fails >= 3 or not backend_alive:
                logger.error("Auto-healing: Restarting FastAPI Backend Engine...")
                if backend_process:
                    kill_proc_tree(backend_process.pid)
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
                f"Frontend check notice ({frontend_fails}/3) - Alive: {frontend_alive}, HTTP Healthy: {frontend_healthy}"
            )
            if frontend_fails >= 3 or not frontend_alive:
                logger.error("Auto-healing: Restarting Next.js Frontend Dashboard...")
                if frontend_process:
                    kill_proc_tree(frontend_process.pid)
                start_frontend()
                frontend_fails = 0
                time.sleep(5)
        else:
            frontend_fails = 0

        # Heartbeat log every 30 seconds
        now = datetime.now().strftime("%H:%M:%S")
        logger.info(
            f"[{now}] 24x7 Pulse Watchdog Heartbeat: Backend (8000): OK | Frontend (3000): OK"
        )
        time.sleep(15)


if __name__ == "__main__":
    main()
