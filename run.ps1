Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  Starting CampusPredict (Backend + Frontend)" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host ""

$root = $PSScriptRoot

Write-Host "[1/2] Starting Flask Backend on http://localhost:5000..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\backend'; python app.py"

Start-Sleep -Seconds 3

Write-Host "[2/2] Starting Streamlit Frontend on http://localhost:8501..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root'; streamlit run streamlit_app.py"

Write-Host ""
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  Both services launched in separate windows!" -ForegroundColor Green
Write-Host "  Frontend: http://localhost:8501" -ForegroundColor Yellow
Write-Host "  Backend:  http://localhost:5000" -ForegroundColor Yellow
Write-Host "  Admin login: admin / admin123" -ForegroundColor Yellow
Write-Host "===================================================" -ForegroundColor Cyan

