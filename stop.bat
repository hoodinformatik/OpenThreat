@echo off
echo ========================================
echo   OpenThreat - Stopping Application
echo ========================================
echo.

echo Stopping Docker containers...
docker-compose down
echo ✓ Docker containers stopped
echo.

echo Killing Python processes (Backend + Celery)...
taskkill /F /IM python.exe /T >nul 2>&1
echo ✓ Backend and Celery stopped
echo.

echo Killing Node processes (Frontend)...
taskkill /F /IM node.exe /T >nul 2>&1
echo ✓ Frontend stopped
echo.

echo ========================================
echo   All services stopped!
echo ========================================
pause
