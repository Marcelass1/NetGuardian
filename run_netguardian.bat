@echo off
title NetGuardian Controller
color 0A

echo ===================================================
echo      NetGuardian - Network Supervision PFE
echo ===================================================
echo.

echo [1/2] Installing Dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo    - 'pip' command failed. Trying 'py -m pip'...
    py -m pip install -r requirements.txt
)
echo.

echo [2/2] Starting Web Server...
echo.
echo    - Access the Dashboard at: http://localhost:5000
echo    - Login: admin / admin
echo.

"C:\Users\dell\AppData\Local\Programs\Python\Python312\python.exe" app.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Application crashed.
)

pause
