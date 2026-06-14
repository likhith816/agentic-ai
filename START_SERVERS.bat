@echo off
title agentic-ai Dev Servers
color 0A

echo ==========================================
echo    agentic-ai - Starting Dev Servers
echo ==========================================

:: Kill any existing instances on these ports
echo [*] Clearing ports 8000 and 5173...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000" 2^>nul') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5173" 2^>nul') do taskkill /f /pid %%a >nul 2>&1
timeout /t 2 /nobreak >nul

:: Start FastAPI backend in a new window
echo [*] Starting FastAPI backend on port 8000...
start "agentic-ai Backend" cmd /k "cd /d "d:\chrome downloads\final steelmind\steelmind-ai-wizard-main" && python main.py"

:: Wait for backend to initialize
timeout /t 5 /nobreak >nul

:: Start React frontend in a new window
echo [*] Starting React frontend on port 5173...
start "agentic-ai Frontend" cmd /k "cd /d "d:\chrome downloads\final steelmind\steelmind-ai-wizard-main\frontend" && npm run dev"

echo.
echo ==========================================
echo  Backend:  http://localhost:8000
echo  Frontend: http://localhost:5173
echo  API Docs: http://localhost:8000/docs
echo ==========================================
echo.
echo Both servers started in separate windows.
echo Close those windows to stop the servers.
pause
