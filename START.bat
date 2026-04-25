@echo off
title AI Interview System
echo.
echo ========================================
echo    STARTING FASTAPI INTERVIEW SYSTEM
echo ========================================
echo.

echo [1/1] Starting FastAPI Backend...
cd /d "%~dp0"
start "FastAPI" cmd /k "uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"

echo.
echo ========================================
echo SYSTEM READY
echo ========================================
echo.
echo Interview System: http://localhost:8000
echo    - Audio recording and transcription
echo    - Real-time analytics
echo    - Topic-based interview flow
echo    - PDF generation
echo.
echo Using the single built-in frontend from static/ + templates/
echo.
echo Press any key to open the application...
pause >nul
start http://localhost:8000
echo.
echo To stop: Close the terminal window
icorn backend.main:app --reload