@echo off
echo Starting Bayora Isolation Lab Services...

start "Bayora Backend (FastAPI)" cmd /k "cd backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"
timeout /t 3 /nobreak >nul

start "Bayora Frontend (Vite)" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================================
echo Bayora Isolation Lab is launching!
echo Backend:  http://127.0.0.1:8000  (API Docs: /docs)
echo Frontend: http://127.0.0.1:5173
echo ========================================================
echo.
pause
