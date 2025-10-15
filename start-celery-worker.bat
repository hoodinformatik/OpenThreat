@echo off
echo ========================================
echo   OpenThreat - Starting Celery Worker
echo ========================================
echo.

echo Starting Celery Worker...
echo.
echo Worker will process background tasks
echo Press Ctrl+C to stop
echo ========================================
echo.

celery -A backend.celery_app worker --loglevel=info --pool=solo
