@echo off
echo ========================================
echo   OpenThreat - Starting Celery Beat
echo ========================================
echo.

echo Starting Celery Beat (Scheduler)...
echo.
echo Beat will schedule automatic updates:
echo - Vulnerability updates every 2 hours
echo - Cache cleanup daily at 3 AM
echo - Stats update every 15 minutes
echo.
echo Press Ctrl+C to stop
echo ========================================
echo.

celery -A backend.celery_app beat --loglevel=info
