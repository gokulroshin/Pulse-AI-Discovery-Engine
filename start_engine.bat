@echo off
title Pulse AI Discovery Engine (Universal 24*7 Launcher)
echo ================================================================
echo    Starting Pulse AI Discovery Engine 24*7 Supervisor Daemon
echo ================================================================
echo.
cd /d "%~dp0"

REM Detect Python in backend\.venv, root .venv, or PATH
if exist "backend\.venv\Scripts\python.exe" (
    set "PY_CMD=backend\.venv\Scripts\python.exe"
) else if exist ".venv\Scripts\python.exe" (
    set "PY_CMD=.venv\Scripts\python.exe"
) else (
    set "PY_CMD=python"
)

%PY_CMD% run_engine_24x7.py
pause
