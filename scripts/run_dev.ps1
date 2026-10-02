# ==============================================================================
# MAHA-GR Development Runner
# Starts both Backend (FastAPI on :8000) and Frontend (Vite on :5173)
# ==============================================================================

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "   Starting MAHA-GR Development Servers   " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 1. Start Backend in separate window
Write-Host "[1/2] Launching FastAPI Backend on http://localhost:8000..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; .\venv\Scripts\Activate.ps1; $env:PYTHONPATH='..'; uvicorn app.main:app --reload --port 8000"

# 2. Start Frontend
Write-Host "[2/2] Launching React Vite Frontend on http://localhost:5173..." -ForegroundColor Green
cd frontend
npm run dev
