@echo off
REM Setup OpenThreat Database
REM This script creates all database tables using Alembic migrations

echo ========================================
echo OpenThreat Database Setup
echo ========================================
echo.

REM Check if we're in the correct directory
if not exist "alembic.ini" (
    echo ERROR: alembic.ini not found!
    echo Please run this script from the OpenThreat root directory.
    pause
    exit /b 1
)

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
    echo.
)

REM Check if PostgreSQL is running
echo Checking PostgreSQL connection...
docker ps | findstr openthreat-db >nul
if errorlevel 1 (
    echo WARNING: PostgreSQL container not running!
    echo Starting PostgreSQL...
    docker-compose up -d postgres
    echo Waiting 10 seconds for PostgreSQL to start...
    timeout /t 10 /nobreak >nul
    echo.
)

REM Run Alembic migrations
echo Running database migrations...
echo.
alembic upgrade head

if errorlevel 1 (
    echo.
    echo ERROR: Migration failed!
    echo.
    echo Troubleshooting:
    echo 1. Check if PostgreSQL is running: docker ps
    echo 2. Check database connection in .env file
    echo 3. Check logs: docker logs openthreat-db
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo SUCCESS! Database tables created.
echo ========================================
echo.
echo You can now:
echo 1. Start the backend: .\start_backend.bat
echo 2. Start the frontend: .\start_frontend.bat
echo 3. Populate data: python scripts/fetch_cisa_kev.py
echo.

pause
