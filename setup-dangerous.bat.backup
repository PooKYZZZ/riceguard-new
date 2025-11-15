@echo off
REM RiceGuard One-Click Setup for Windows
REM Cross-platform setup for all team members

echo.
echo =====================================
echo   RiceGuard Automated Setup (Windows)
echo =====================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js 18+ from https://nodejs.org
    pause
    exit /b 1
)

echo ✓ Python and Node.js found
echo.

REM Run the main setup script
echo Starting RiceGuard setup...
echo.

python setup.py

if errorlevel 1 (
    echo.
    echo Setup completed with errors. Please check the output above.
    echo.
    echo Common fixes:
    echo 1. Run as Administrator
    echo 2. Check internet connection
    echo 3. Temporarily disable antivirus
    echo 4. Read TROUBLESHOOTING.md for help
) else (
    echo.
    echo ✓ Setup completed successfully!
    echo.
    echo Next steps:
    echo 1. Configure backend\.env (copy from .env.example)
    echo 2. Download ML model to ml\model.h5
    echo 3. Run: python start-dev.py
    echo 4. Verify with: python verify-setup.py
)

echo.
pause