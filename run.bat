@echo off
title CampusPredict Launcher
echo ===================================================
echo   Starting CampusPredict (Backend + Frontend)
echo ===================================================
echo.

echo [1/2] Starting Flask Backend on http://localhost:5000 ...
start "CampusPredict Backend (Port 5000)" cmd /k "cd /d %~dp0backend && python app.py"

echo Waiting 3 seconds for backend to initialize...
timeout /t 3 /nobreak >nul

echo [2/2] Starting Streamlit Frontend on http://localhost:8501 ...
start "CampusPredict Frontend (Port 8501)" cmd /k "cd /d %~dp0 && streamlit run streamlit_app.py"

echo.
echo ===================================================
echo   Both services are now running!
echo   Frontend: http://localhost:8501
echo   Backend:  http://localhost:5000
echo   Admin login: admin / admin123
echo ===================================================
pause

