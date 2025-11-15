@echo off
REM RiceGuard Safe Setup for Windows - READ-ONLY VERSION
REM This script only checks and reports - never modifies existing files

echo.
echo ========================================
echo   RiceGuard Safe Setup Check (Windows)
echo ========================================
echo.
echo This script will ONLY check your setup - it will NOT modify any files
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

echo Found Python and Node.js
echo.

REM Run the safe setup check script
echo Running setup check...
echo.

python setup-safe.py

if errorlevel 1 (
    echo.
    echo Setup check found issues. Please follow the recommendations above.
    echo.
) else (
    echo.
    echo Setup check passed! Your project is ready.
    echo.
)

pause