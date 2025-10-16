@echo off
REM Start Celery Worker and Beat for OpenThreat
REM This script starts both the worker (for processing tasks) and beat (for scheduling)

echo ========================================
echo Starting Celery for OpenThreat
echo ========================================
echo.

REM Check if Redis is running
echo [1/3] Checking Redis...
docker ps | findstr openthreat-redis >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Redis is not running!
    echo Please start Redis first: docker-compose up -d redis
    pause
    exit /b 1
)
echo [OK] Redis is running
echo.

REM Check if Ollama is running
echo [2/3] Checking Ollama...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [WARN] Ollama is not running!
    echo LLM processing will be disabled.
    echo To enable: Start Ollama desktop app
    echo.
) else (
    echo [OK] Ollama is running
    echo.
)

echo [3/3] Starting Celery...
echo.
echo Starting in 2 separate windows:
echo   1. Celery Worker  - Processes tasks
echo   2. Celery Beat    - Schedules tasks
echo.

REM Start Celery Worker in new window
start "Celery Worker - OpenThreat" cmd /k "cd /d %~dp0 && echo Starting Celery Worker... && celery -A backend.celery_app worker --loglevel=info --pool=solo"

REM Wait a bit for worker to start
timeout /t 3 /nobreak >nul

REM Start Celery Beat in new window
start "Celery Beat - OpenThreat" cmd /k "cd /d %~dp0 && echo Starting Celery Beat... && celery -A backend.celery_app beat --loglevel=info"

echo.
echo ========================================
echo Celery Started Successfully!
echo ========================================
echo.
echo Two new windows opened:
echo   - Celery Worker: Processes background tasks
echo   - Celery Beat:   Schedules periodic tasks
echo.
echo Scheduled Tasks:
echo   - New CVEs:        Every 5 minutes
echo   - High Priority:   Every 10 minutes
echo   - Medium Priority: Every 30 minutes
echo   - Low Priority:    Every 2 hours
echo.
echo To stop: Close both Celery windows
echo.
echo Press any key to close this window...
pause >nul
