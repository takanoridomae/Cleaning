@echo off
chcp 65001 >nul
cls

echo.
echo ========================================================================
echo Aircon Report System - Local Startup
echo ========================================================================
echo.

cd /d "%~dp0"

REM ========================================================================
REM 1. Check and activate virtual environment
REM ========================================================================
echo [1/5] Checking virtual environment...
echo.

if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found.
    echo.
    echo Please create virtual environment:
    echo   python -m venv venv
    echo   venv\Scripts\activate
    echo   pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo OK: Virtual environment found
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo OK: Virtual environment activated
echo.

REM ========================================================================
REM 2. Check database
REM ========================================================================
echo [2/5] Checking database...
echo.

if not exist "instance\aircon_report.db" (
    echo WARNING: Database file not found.
    echo Database will be created on first startup.
    echo.
) else (
    echo OK: Database file found (instance\aircon_report.db)
    echo.
)

REM ========================================================================
REM 3. Check environment variables
REM ========================================================================
echo [3/5] Checking environment variables...
echo.

if not exist ".env" (
    echo WARNING: .env file not found.
    echo.
    echo If you want to use NAS storage, please create .env file.
    echo See ENV_SETUP_INSTRUCTIONS.md for details.
    echo.
    echo Continuing with local storage only...
    echo.
) else (
    echo OK: .env file found
    echo.
)

REM ========================================================================
REM 4. Check Tailscale VPN (for NAS)
REM ========================================================================
echo [4/5] Checking Tailscale VPN connection (for NAS)...
echo.

where tailscale >nul 2>&1
if %errorlevel% equ 0 (
    echo Tailscale connection status:
    tailscale status | findstr "100.69.218.15" >nul 2>&1
    if %errorlevel% equ 0 (
        echo OK: Tailscale VPN is connected
        echo OK: NAS is accessible (100.69.218.15)
    ) else (
        echo WARNING: NAS not found (100.69.218.15)
        echo          You can continue with local storage
    )
    echo.
) else (
    echo INFO: Tailscale is not installed or not in PATH
    echo       If you want to use NAS, please start Tailscale
    echo       Continuing with local storage only...
    echo.
)

REM ========================================================================
REM 5. Start Flask application
REM ========================================================================
echo [5/5] Starting Flask application...
echo.
echo ========================================================================
echo Application starting...
echo ========================================================================
echo.
echo Access URL: http://localhost:5000
echo         or: http://127.0.0.1:5000
echo.
echo To stop: Press Ctrl + C
echo.
echo ========================================================================
echo.

python run.py

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to start application.
    echo.
    echo Please check:
    echo   1. Virtual environment is activated
    echo   2. Required packages are installed (pip install -r requirements.txt)
    echo   3. Port 5000 is not in use by another application
    echo.
    pause
    exit /b 1
)

pause
