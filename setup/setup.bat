@echo off
REM =============================================================================
REM RiceGuard Automated Setup Script for Windows
REM =============================================================================
REM This script sets up the entire RiceGuard development environment
REM It safely handles dependencies, environment files, and configuration
REM =============================================================================

title RiceGuard Setup

echo.
echo =============================================================================
echo                           🌾 RiceGuard Setup
echo =============================================================================
echo.
echo This script will automatically set up your RiceGuard development environment.
echo It will install dependencies and create necessary configuration files.
echo Existing files will NEVER be overwritten - your data is safe.
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ❌ ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python 3.8+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ❌ ERROR: Node.js is not installed or not in PATH
    echo.
    echo Please install Node.js 18+ from https://nodejs.org
    echo Make sure to check "Add Node.js to PATH" during installation
    echo.
    pause
    exit /b 1
)

echo ✅ System requirements verified
echo.

REM Run the main setup script
echo 🚀 Starting RiceGuard automated setup...
echo This may take a few minutes...
echo.

python setup.py

REM Check the result
if errorlevel 1 (
    echo.
    echo =============================================================================
    echo                      ⚠️ Setup Completed with Issues
    echo =============================================================================
    echo.
    echo Some setup steps encountered problems. Please review the output above.
    echo.
    echo Common solutions:
    echo   1. If dependencies failed to install, try running the setup again
    echo   2. If permissions are required, run as administrator
    echo   3. If network issues occurred, check your internet connection
    echo.
    echo Manual setup steps:
    echo   1. Copy environment files:
    echo      copy backend\.env.example backend\.env
    echo      copy frontend\.env.example frontend\.env
    echo.
    echo   2. Edit backend\.env with your MongoDB Atlas credentials
    echo      - Get free cluster from: https://www.mongodb.com/cloud/atlas
    echo      - Generate JWT secret: openssl rand -hex 32
    echo.
    echo   3. Start development:
    echo      python start-dev.py
    echo.
) else (
    echo.
    echo =============================================================================
    echo                       🎉 Setup Completed Successfully!
    echo =============================================================================
    echo.
    echo Your RiceGuard development environment is ready!
    echo.
    echo Next steps:
    echo   1. Configure environment files (if not done):
    echo      - Edit backend\.env with your MongoDB Atlas credentials
    echo      - Get free cluster from: https://www.mongodb.com/cloud/atlas
    echo.
    echo   2. Start development servers:
    echo      python start-dev.py
    echo.
    echo   3. Open your browser:
    echo      - Frontend: http://localhost:3000
    echo      - API Docs: http://127.0.0.1:8000/docs
    echo.
    echo   4. Verify setup (optional):
    echo      python verify-setup.py
    echo.
    echo Need help? Check CLAUDE.md for documentation
    echo.
)

echo =============================================================================
echo Press any key to exit...
echo =============================================================================
pause >nul