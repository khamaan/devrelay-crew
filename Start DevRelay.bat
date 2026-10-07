@echo off
cd /d "%~dp0"
echo Checking project dependencies...
uv sync --quiet
if errorlevel 1 (pause & exit /b 1)
".venv\Scripts\python.exe" -m devrelay.web
if errorlevel 1 pause
