@echo off
REM Start OpenThreat Backend
REM This script must be run from the project root directory

echo Starting OpenThreat Backend...
echo.

REM Check if we're in the correct directory
if not exist "backend\main.py" (
    echo ERROR: backend\main.py not found!
    echo Please run this script from the OpenThreat root directory.
    pause
    exit /b 1
)

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Start uvicorn
echo Starting uvicorn server on http://127.0.0.1:8001
echo Press Ctrl+C to stop
echo.

python -m uvicorn backend.main:app --reload --port 8001 --host 127.0.0.1

pause
