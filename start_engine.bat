@echo off
title Pulse AI Discovery Engine (24*7 Supervisor)
echo ================================================================
echo    Starting Pulse AI Discovery Engine 24*7 Supervisor Daemon
echo ================================================================
echo.
cd /d "%~dp0"
python run_engine_24x7.py
pause
