@echo off
title FinWise AI - Web Application Server
cd /d "%~dp0"

echo ==========================================================
echo    FinWise AI - Personal Finance Advisor Bot
echo    Starting Local Development Server...
echo ==========================================================
echo.

:: Detect Python executable
set "PYTHON_CMD="
if exist "%~dp0venv\Scripts\python.exe" (
    set "PYTHON_CMD=%~dp0venv\Scripts\python.exe"
) else if exist "%USERPROFILE%\Anaconda3\python.exe" (
    set "PYTHON_CMD=%USERPROFILE%\Anaconda3\python.exe"
) else if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    set "PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
) else if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set "PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
) else if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" (
    set "PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
) else if exist "C:\ProgramData\Anaconda3\python.exe" (
    set "PYTHON_CMD=C:\ProgramData\Anaconda3\python.exe"
) else if exist "C:\Python312\python.exe" (
    set "PYTHON_CMD=C:\Python312\python.exe"
) else if exist "C:\Python311\python.exe" (
    set "PYTHON_CMD=C:\Python311\python.exe"
) else (
    where python >nul 2>nul
    if %errorlevel% equ 0 (
        set "PYTHON_CMD=python"
    ) else (
        where py >nul 2>nul
        if %errorlevel% equ 0 (
            set "PYTHON_CMD=py"
        )
    )
)

if "%PYTHON_CMD%"=="" (
    echo [ERROR] Python was not found!
    echo Please make sure Python or Anaconda is installed on your machine.
    pause
    exit /b 1
)

echo [1/3] Using Python: %PYTHON_CMD%

:: Seed database if it doesn't exist
if not exist "instance\finwise.db" (
    echo [2/3] Initializing database and seeding demo data...
    "%PYTHON_CMD%" seed_demo.py
) else (
    echo [2/3] Database ready.
)

:: Set Port (use 5000 or 5050 if 5000 is occupied)
set PORT=5000
set HOST=127.0.0.1

echo [3/3] Opening your browser at http://localhost:%PORT% ...
start "" "http://localhost:%PORT%"

echo.
echo ==========================================================
echo  Server is now RUNNING!
echo  URL: http://localhost:%PORT%
echo  Demo Account: demo@finwise.ai  /  Password: Demo@12345
echo  (Keep this window open while using the application)
echo ==========================================================
echo.

"%PYTHON_CMD%" run.py

pause
