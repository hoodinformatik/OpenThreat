@echo off
echo ========================================
echo   OpenThreat - Full Stack with Celery
echo ========================================
echo.

REM Check if Docker is running
echo [1/5] Checking Docker...
docker ps >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not running!
    echo Please start Docker Desktop first.
    pause
    exit /b 1
)
echo ✓ Docker is running
echo.

REM Start Docker containers
echo [2/5] Starting Docker containers...
docker-compose up -d postgres redis
if %errorlevel% neq 0 (
    echo ERROR: Failed to start Docker containers
    pause
    exit /b 1
)
echo ✓ Docker containers started
echo.

REM Wait for services
echo [3/5] Waiting for services to be ready...
timeout /t 3 /nobreak >nul
echo ✓ Services ready
echo.

REM Start all services
echo [4/5] Starting Backend, Frontend, and Celery...
echo.
echo Starting Backend API on http://localhost:8001
echo Starting Frontend on http://localhost:3000
echo Starting Celery Worker for background tasks
echo Starting Celery Beat for scheduled tasks
echo.
echo Press Ctrl+C in any window to stop that service
echo ========================================
echo.

REM Start all services in separate windows
start "OpenThreat Backend" cmd /k "python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8001"
timeout /t 2 /nobreak >nul

start "OpenThreat Frontend" cmd /k "cd frontend && npm run dev"
timeout /t 2 /nobreak >nul

start "OpenThreat Celery Worker" cmd /k "celery -A backend.celery_app worker --loglevel=info --pool=solo"
timeout /t 2 /nobreak >nul

start "OpenThreat Celery Beat" cmd /k "celery -A backend.celery_app beat --loglevel=info"

echo.
echo ✓ All services started!
echo.
echo Backend:  http://localhost:8001/docs
echo Frontend: http://localhost:3000
echo.
echo [5/5] Monitoring services...
echo Close this window when you're done.
echo To stop all services, run: stop.bat
pause
