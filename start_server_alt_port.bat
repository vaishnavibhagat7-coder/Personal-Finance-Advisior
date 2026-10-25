@echo off
title FinWise AI - Web Application Server (Port 5050)
cd /d "%~dp0"

echo ==========================================================
echo    FinWise AI - Starting on Alternate Port 5050
echo ==========================================================
echo.

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

if not exist "instance\finwise.db" (
    echo Initializing database...
    "%PYTHON_CMD%" seed_demo.py
)

set PORT=5050
set HOST=127.0.0.1

echo Opening browser at http://localhost:5050 ...
start "" "http://localhost:5050"

"%PYTHON_CMD%" run.py

pause
