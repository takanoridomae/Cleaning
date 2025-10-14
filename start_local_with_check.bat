@echo off
chcp 65001 >nul
cls

echo.
echo ========================================================================
echo Aircon Report System - Local Startup (Detailed Check)
echo ========================================================================
echo.

cd /d "%~dp0"

REM ========================================================================
REM 1. Check and activate virtual environment
REM ========================================================================
echo [1/6] Checking virtual environment...
echo.

if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found.
    echo.
    echo Do you want to create virtual environment? (Y/N)
    set /p CREATE_VENV=
    if /i "%CREATE_VENV%"=="Y" (
        echo.
        echo Creating virtual environment...
        python -m venv venv
        if %errorlevel% neq 0 (
            echo ERROR: Failed to create virtual environment.
            pause
            exit /b 1
        )
        echo OK: Virtual environment created
        echo.
        echo Installing required packages...
        call venv\Scripts\activate.bat
        pip install -r requirements.txt
        if %errorlevel% neq 0 (
            echo ERROR: Failed to install packages.
            pause
            exit /b 1
        )
        echo OK: Packages installed
    ) else (
        echo Exiting without creating virtual environment.
        pause
        exit /b 1
    )
) else (
    echo OK: Virtual environment found
    call venv\Scripts\activate.bat
    echo OK: Virtual environment activated
)
echo.

REM ========================================================================
REM 2. Check database and create backup
REM ========================================================================
echo [2/6] Checking database and creating backup...
echo.

if not exist "instance" (
    mkdir instance
    echo OK: Created instance directory
)

if not exist "instance\aircon_report.db" (
    echo WARNING: Database file not found.
    echo Database will be created on first startup.
    echo.
) else (
    echo OK: Database file found (instance\aircon_report.db)
    
    if not exist "db_backups\startup" (
        mkdir db_backups\startup
    )
    
    for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c%%a%%b)
    for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a%%b)
    set timestamp=%mydate%_%mytime%
    
    echo Creating database backup...
    copy "instance\aircon_report.db" "db_backups\startup\aircon_report_%timestamp%.db" >nul
    echo OK: Backup created: db_backups\startup\aircon_report_%timestamp%.db
    echo.
)

REM ========================================================================
REM 3. Check environment variables
REM ========================================================================
echo [3/6] Checking environment variables...
echo.

if not exist ".env" (
    echo WARNING: .env file not found.
    echo.
    echo Do you want to see .env file sample? (Y/N)
    set /p SHOW_SAMPLE=
    if /i "%SHOW_SAMPLE%"=="Y" (
        echo.
        echo ========================================================================
        echo .env file sample
        echo ========================================================================
        echo.
        echo # Enable NAS feature
        echo NAS_ENABLED=True
        echo.
        echo # NAS WebDAV URL
        echo NAS_WEBDAV_URL=http://100.69.218.15:5005
        echo.
        echo # NAS login credentials
        echo NAS_USERNAME=Takanori
        echo NAS_PASSWORD=your-password-here
        echo.
        echo # NAS base path
        echo NAS_BASE_PATH=/home/eacon_keep_pict
        echo.
        echo ========================================================================
        echo.
        echo See ENV_SETUP_INSTRUCTIONS.md for details.
        echo.
    )
    echo Continuing with local storage only...
    echo.
) else (
    echo OK: .env file found
    echo.
    
    findstr /i "NAS_ENABLED" .env >nul 2>&1
    if %errorlevel% equ 0 (
        echo Detected settings:
        findstr /i /c:"NAS_ENABLED" .env
        findstr /i /c:"NAS_WEBDAV_URL" .env 2>nul
        echo.
    )
)

REM ========================================================================
REM 4. Check Tailscale VPN connection
REM ========================================================================
echo [4/6] Checking Tailscale VPN connection...
echo.

where tailscale >nul 2>&1
if %errorlevel% equ 0 (
    echo Checking Tailscale connection status...
    echo.
    tailscale status
    echo.
    
    tailscale status | findstr "100.69.218.15" >nul 2>&1
    if %errorlevel% equ 0 (
        echo OK: Tailscale VPN is connected
        echo OK: NAS is accessible (100.69.218.15)
    ) else (
        echo WARNING: NAS not found (100.69.218.15)
        echo          Tailscale VPN may not be fully connected
    )
) else (
    echo INFO: Tailscale is not installed or not in PATH
    echo       If you want to use NAS, please start Tailscale
)
echo.

REM ========================================================================
REM 5. NAS connection test (optional)
REM ========================================================================
echo [5/6] NAS connection test...
echo.

if exist ".env" (
    findstr /i "NAS_ENABLED=True" .env >nul 2>&1
    if %errorlevel% equ 0 (
        echo NAS is enabled. Do you want to run connection test? (Y/N)
        set /p RUN_TEST=
        if /i "%RUN_TEST%"=="Y" (
            echo.
            echo Running NAS connection test...
            echo.
            python scripts\utilities\test_nas_connection.py
            echo.
            if %errorlevel% neq 0 (
                echo WARNING: NAS connection test failed
                echo          Will fallback to local storage
                echo.
                echo Do you want to continue startup? (Y/N)
                set /p CONTINUE=
                if /i not "%CONTINUE%"=="Y" (
                    echo Startup cancelled.
                    pause
                    exit /b 1
                )
            )
        ) else (
            echo NAS connection test skipped
        )
    ) else (
        echo NAS is disabled (using local storage only)
    )
) else (
    echo .env file not found, skipping NAS connection test
)
echo.

REM ========================================================================
REM 6. Start Flask application
REM ========================================================================
echo [6/6] Starting Flask application...
echo.
echo ========================================================================
echo Application starting...
echo ========================================================================
echo.
echo Access URL: http://localhost:5000
echo         or: http://127.0.0.1:5000
echo.
echo For network access from other devices:
echo   http://[this-PC-IP-address]:5000
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
    echo   1. Virtual environment is activated correctly
    echo   2. Required packages are installed
    echo   3. Port 5000 is not in use by another application
    echo   4. Database file is not corrupted
    echo.
    pause
    exit /b 1
)

pause
