@echo off
REM Start OpenThreat Frontend
REM This script must be run from the project root directory

echo Starting OpenThreat Frontend...
echo.

REM Check if we're in the correct directory
if not exist "frontend\package.json" (
    echo ERROR: frontend\package.json not found!
    echo Please run this script from the OpenThreat root directory.
    pause
    exit /b 1
)

REM Navigate to frontend directory
cd frontend

REM Check if node_modules exists
if not exist "node_modules" (
    echo Installing dependencies...
    call npm install
    echo.
)

REM Start Next.js dev server
echo Starting Next.js dev server on http://localhost:3000
echo Press Ctrl+C to stop
echo.

call npm run dev

pause
