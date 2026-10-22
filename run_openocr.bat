@echo off
cd /d "%~dp0"
setlocal enabledelayedexpansion

echo ==========================================
echo       OpenOCR - One-Click Launcher
echo ==========================================
echo Developed by Dr. Abu Suraih Sakhri
echo.

:: 1. Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.12 and add it to your PATH.
    pause
    exit /b
)

:: 2. Check for virtual environment
if not exist "venv" (
    echo [INFO] Creating virtual environment for first-run setup...
    python -m venv venv
)

:: 3. Activate virtual environment
call venv\Scripts\activate

:: 4. Install/Update dependencies
echo [INFO] Checking dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Dependency installation failed.
    pause
    exit /b 1
)

:: 5. Launch Application
echo [SUCCESS] Everything is ready. Starting OpenOCR...
python src/main.py

:: 6. Keep window open if crash occurs
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Application crashed. Please check the logs above.
    pause
)

deactivate
