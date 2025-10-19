@echo off
echo ========================================
echo   OpenThreat - Starting Application
echo ========================================
echo.

REM Check if Docker is running
echo [1/4] Checking Docker...
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
echo [2/4] Starting Docker containers...
docker-compose up -d postgres redis
if %errorlevel% neq 0 (
    echo ERROR: Failed to start Docker containers
    pause
    exit /b 1
)
echo ✓ Docker containers started
echo.

REM Wait for database
echo [3/5] Waiting for database to be ready...
timeout /t 5 /nobreak >nul
echo ✓ Database ready
echo.

REM Run database migrations
echo [4/5] Running database migrations...
alembic upgrade head >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Database migrations may have failed
    echo Run '.\setup_database.bat' manually if needed
) else (
    echo ✓ Database tables created
)
echo.

REM Start backend and frontend
echo [5/5] Starting Backend and Frontend...
echo.
echo Starting Backend API on http://localhost:8001
echo Starting Frontend on http://localhost:3000
echo.
echo Press Ctrl+C to stop all services
echo ========================================
echo.

REM Start both in new windows
start "OpenThreat Backend" cmd /k "python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8001"
timeout /t 2 /nobreak >nul
start "OpenThreat Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ✓ Application started!
echo.
echo Backend:  http://localhost:8001/docs
echo Frontend: http://localhost:3000
echo.
echo Close this window when you're done.
pause
