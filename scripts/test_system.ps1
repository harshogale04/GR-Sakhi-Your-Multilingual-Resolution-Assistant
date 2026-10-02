# ==============================================================================
# MAHA-GR Full System Verification Script
# Verifies Frontend TypeScript build and Backend Pytest suite
# ==============================================================================

Write-Host ">>> [1/2] Verifying Backend Tests via Pytest..." -ForegroundColor Cyan
$env:PYTHONPATH = "."
& ".\backend\venv\Scripts\python.exe" -m pytest backend/tests -v
if ($LASTEXITCODE -ne 0) {
    Write-Host "Backend tests failed!" -ForegroundColor Red
    exit 1
}

Write-Host "`n>>> [2/2] Verifying Frontend Build via Vite & TypeScript..." -ForegroundColor Cyan
Set-Location -Path "frontend"
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Host "Frontend build failed!" -ForegroundColor Red
    Set-Location -Path ".."
    exit 1
}
Set-Location -Path ".."

Write-Host "`n>>> All MAHA-GR Verification Checks Passed Successfully! <<<" -ForegroundColor Green
