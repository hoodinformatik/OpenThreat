@echo off
echo ========================================
echo   OpenThreat - Starting Backend Only
echo ========================================
echo.

REM Check if Docker is running
echo Checking Docker...
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
echo Starting Docker containers...
docker-compose up -d postgres redis
echo ✓ Docker containers started
echo.

REM Wait for database
echo Waiting for database...
timeout /t 3 /nobreak >nul
echo ✓ Database ready
echo.

REM Start backend
echo Starting Backend API...
echo.
echo Backend running on: http://localhost:8001
echo API Docs: http://localhost:8001/docs
echo.
echo Press Ctrl+C to stop
echo ========================================
echo.

python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8001
