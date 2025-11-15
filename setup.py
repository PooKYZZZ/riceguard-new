#!/usr/bin/env python3
"""
RiceGuard Automated Setup Script
Cross-platform setup for all team members
Usage: python setup.py
"""

import os
import sys
import platform
import subprocess
import json
import shutil
from pathlib import Path
from urllib.request import urlopen
import urllib.error

# Setup configuration
REPO_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = REPO_ROOT / "backend"
FRONTEND_DIR = REPO_ROOT / "frontend"
MOBILE_DIR = REPO_ROOT / "mobileapp" / "riceguard"

class Colors:
    """Terminal colors for better UX"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_status(message, color=Colors.OKCYAN):
    """Print colored status message"""
    print(f"{color}→{Colors.ENDC} {message}")

def print_success(message):
    """Print success message"""
    print(f"{Colors.OKGREEN}✅{Colors.ENDC} {message}")

def print_error(message):
    """Print error message"""
    print(f"{Colors.FAIL}❌{Colors.ENDC} {message}")

def print_warning(message):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠️{Colors.ENDC} {message}")

def run_command(cmd, cwd=None, check=True, capture_output=False):
    """Run command with proper error handling"""
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=cwd, check=check,
            capture_output=capture_output, text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        if capture_output:
            print_error(f"Command failed: {cmd}")
            print_error(f"Error: {e.stderr}")
        else:
            print_error(f"Command failed: {cmd}")
        raise

def check_system_requirements():
    """Check system requirements and provide guidance"""
    print_status("Checking system requirements...")

    # Check Python version
    python_version = sys.version_info
    if python_version < (3, 8):
        print_error(f"Python 3.8+ required, found {python_version.major}.{python_version.minor}")
        return False
    else:
        print_success(f"Python {python_version.major}.{python_version.minor}.{python_version.micro} found")

    # Check Node.js
    try:
        node_result = run_command("node --version", capture_output=True)
        print_success(f"Node.js {node_result.stdout.strip()} found")
    except FileNotFoundError:
        print_error("Node.js not found. Please install Node.js 18+ from https://nodejs.org/")
        return False

    # Check npm
    try:
        npm_result = run_command("npm --version", capture_output=True)
        print_success(f"npm {npm_result.stdout.strip()} found")
    except FileNotFoundError:
        print_error("npm not found. Please install Node.js with npm included.")
        return False

    # Check Git
    try:
        git_result = run_command("git --version", capture_output=True)
        print_success(f"Git {git_result.stdout.strip()} found")
    except FileNotFoundError:
        print_warning("Git not found. Git is recommended for version control.")

    return True

def setup_backend():
    """Setup backend with virtual environment and dependencies"""
    print_status("Setting up backend environment...")

    # Create backend directory if it doesn't exist
    if not BACKEND_DIR.exists():
        print_error("Backend directory not found!")
        return False

    # Create virtual environment
    venv_dir = BACKEND_DIR / ".venv"
    if not venv_dir.exists():
        print_status("Creating Python virtual environment...")
        run_command(f"python -m venv {venv_dir}")
        print_success("Virtual environment created")
    else:
        print_success("Virtual environment already exists")

    # Determine activation script path
    if platform.system() == "Windows":
        activate_script = venv_dir / "Scripts" / "Activate.ps1"
        pip_exe = venv_dir / "Scripts" / "pip.exe"
    else:
        activate_script = venv_dir / "bin" / "activate"
        pip_exe = venv_dir / "bin" / "pip"

    # Upgrade pip
    print_status("Upgrading pip...")
    run_command(f"{pip_exe} install --upgrade pip")

    # Install requirements
    print_status("Installing Python dependencies...")
    requirements_file = BACKEND_DIR / "requirements.txt"
    if requirements_file.exists():
        run_command(f"{pip_exe} install -r {requirements_file}")
        print_success("Python dependencies installed")
    else:
        print_warning("requirements.txt not found")

    return True

def setup_frontend():
    """Setup frontend with npm dependencies"""
    print_status("Setting up frontend environment...")

    if not FRONTEND_DIR.exists():
        print_error("Frontend directory not found!")
        return False

    # Check if node_modules exists
    node_modules = FRONTEND_DIR / "node_modules"
    if not node_modules.exists():
        print_status("Installing npm dependencies...")
        run_command("npm install", cwd=FRONTEND_DIR)
        print_success("Frontend dependencies installed")
    else:
        print_success("Frontend dependencies already installed")

    return True

def setup_environment_files():
    """Create .env.example files and guide user to create .env files"""
    print_status("Setting up environment configuration...")

    # Backend .env.example
    backend_env_example = BACKEND_DIR / ".env.example"
    backend_env_content = """# RiceGuard Backend Environment Configuration
# Copy this file to .env and fill in your values

# MongoDB Atlas Configuration
MONGO_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/riceguard_db
DB_NAME=riceguard_db

# JWT Configuration (Generate a strong secret key)
JWT_SECRET=CHANGE_ME_SUPER_SECRET_KEY_HERE
JWT_ALGORITHM=HS256
TOKEN_EXPIRE_HOURS=6

# File Upload Configuration
UPLOAD_DIR=uploads
MAX_UPLOAD_MB=8

# ML Model Configuration
MODEL_PATH=../ml/model.h5

# ML Model Tuning Parameters
CONFIDENCE_THRESHOLD=0.62
CONFIDENCE_MARGIN=0.08
TEMPERATURE=2.1

# CORS Configuration (Add your frontend origins)
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173
"""

    if not backend_env_example.exists():
        with open(backend_env_example, "w") as f:
            f.write(backend_env_content)
        print_success("Backend .env.example created")
    else:
        print_success("Backend .env.example already exists")

    # Frontend .env.example
    frontend_env_example = FRONTEND_DIR / ".env.example"
    frontend_env_content = """# RiceGuard Frontend Environment Configuration
# Copy this file to .env and update the API URL if needed

REACT_APP_API_URL=http://127.0.0.1:8000/api/v1
"""

    if not frontend_env_example.exists():
        with open(frontend_env_example, "w") as f:
            f.write(frontend_env_content)
        print_success("Frontend .env.example created")
    else:
        print_success("Frontend .env.example already exists")

    return True

def setup_directory_structure():
    """Create necessary directories"""
    print_status("Creating necessary directories...")

    # Create uploads directory
    uploads_dir = BACKEND_DIR / "uploads"
    uploads_dir.mkdir(exist_ok=True)
    print_success(f"Created {uploads_dir}")

    # Create ml directory for model
    ml_dir = REPO_ROOT / "ml"
    ml_dir.mkdir(exist_ok=True)
    print_success(f"Created {ml_dir}")

    return True

def setup_development_tools():
    """Setup development helper scripts"""
    print_status("Creating development helper scripts...")

    # Cross-platform start script
    start_script = REPO_ROOT / "start-dev.py"
    start_content = '''#!/usr/bin/env python3
"""
RiceGuard Development Server Starter
Start both backend and frontend with one command
"""

import os
import sys
import time
import signal
import subprocess
import threading
from pathlib import Path

# Configuration
REPO_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = REPO_ROOT / "backend"
FRONTEND_DIR = REPO_ROOT / "frontend"

# Find Python executable (prefer virtual environment)
def find_python():
    venv_python = BACKEND_DIR / ".venv" / ("Scripts" if os.name == "nt" else "bin") / ("python.exe" if os.name == "nt" else "python")
    if venv_python.exists():
        return str(venv_python)
    return sys.executable

# Start backend
def start_backend():
    python_exe = find_python()
    cmd = [python_exe, "-m", "uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
    print(f"Starting backend: {' '.join(cmd)}")
    return subprocess.Popen(cmd, cwd=BACKEND_DIR)

# Start frontend
def start_frontend():
    cmd = ["npm", "start"]
    print(f"Starting frontend: {' '.join(cmd)}")
    env = os.environ.copy()
    env["BROWSER"] = "none"  # Prevent auto-opening browser
    return subprocess.Popen(cmd, cwd=FRONTEND_DIR, env=env)

def main():
    processes = []

    try:
        print("🚀 Starting RiceGuard development servers...")
        backend = start_backend()
        time.sleep(2)  # Give backend time to start
        frontend = start_frontend()
        processes = [backend, frontend]

        print("\\n" + "="*50)
        print("✅ Backend API: http://127.0.0.1:8000")
        print("✅ API Docs: http://127.0.0.1:8000/docs")
        print("✅ Frontend: http://localhost:3000")
        print("Press Ctrl+C to stop all servers")
        print("="*50)

        # Wait for processes
        while True:
            time.sleep(1)
            for proc in processes:
                if proc.poll() is not None:
                    raise KeyboardInterrupt

    except KeyboardInterrupt:
        print("\\nStopping servers...")
        for proc in processes:
            if proc.poll() is None:
                proc.terminate()
        print("✅ All servers stopped")

if __name__ == "__main__":
    main()
'''

    with open(start_script, "w") as f:
        f.write(start_content)
    print_success("Development starter script created")

    return True

def create_verification_script():
    """Create verification script to test setup"""
    print_status("Creating verification script...")

    verify_script = REPO_ROOT / "verify-setup.py"
    verify_content = '''#!/usr/bin/env python3
"""
RiceGuard Setup Verification Script
Verify that all components are working correctly
"""

import requests
import subprocess
import time
import sys
from pathlib import Path

def test_backend():
    """Test backend health endpoint"""
    print("Testing backend...")
    try:
        response = requests.get("http://127.0.0.1:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is responding")
            return True
        else:
            print(f"❌ Backend returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend connection failed: {e}")
        return False

def test_frontend():
    """Test frontend accessibility"""
    print("Testing frontend...")
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend is responding")
            return True
        else:
            print(f"❌ Frontend returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Frontend connection failed: {e}")
        return False

def check_environment():
    """Check environment files"""
    print("Checking environment files...")

    backend_env = Path("backend/.env")
    frontend_env = Path("frontend/.env")

    if backend_env.exists():
        print("✅ Backend .env exists")
    else:
        print("❌ Backend .env missing (copy from .env.example)")

    if frontend_env.exists():
        print("✅ Frontend .env exists")
    else:
        print("❌ Frontend .env missing (copy from .env.example)")

def main():
    print("🔍 Verifying RiceGuard setup...")
    print("-" * 40)

    # Check environment files
    check_environment()
    print()

    # Test backend
    backend_ok = test_backend()
    print()

    # Test frontend
    frontend_ok = test_frontend()
    print()

    if backend_ok and frontend_ok:
        print("🎉 All systems operational!")
        return 0
    else:
        print("⚠️ Some issues detected. Check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
'''

    with open(verify_script, "w") as f:
        f.write(verify_content)
    print_success("Verification script created")

    return True

def create_troubleshooting_guide():
    """Create comprehensive troubleshooting guide"""
    print_status("Creating troubleshooting guide...")

    guide_file = REPO_ROOT / "TROUBLESHOOTING.md"
    guide_content = '''# RiceGuard Troubleshooting Guide

## Quick Start Checklist

- [ ] System requirements met (Python 3.8+, Node.js 18+)
- [ ] Backend virtual environment created and activated
- [ ] All dependencies installed
- [ ] Environment files configured (.env files created)
- [ ] MongoDB Atlas connection string configured
- [ ] ML model file placed at `ml/model.h5`
- [ ] Development servers started without errors

## Common Issues

### Backend Issues

**Port 8000 already in use**
```bash
# Find process using port 8000
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # macOS/Linux

# Kill the process (replace PID)
taskkill /PID <PID> /F        # Windows
kill -9 <PID>                 # macOS/Linux
```

**MongoDB connection failed**
- Check your internet connection
- Verify MongoDB Atlas credentials in `.env`
- Ensure your IP is whitelisted in MongoDB Atlas
- Check if cluster name and database name are correct

**ModuleNotFoundError: No module named 'tensorflow'**
```bash
# Activate virtual environment first
cd backend
# Windows
.venv\\Scripts\\Activate.ps1
# macOS/Linux
source .venv/bin/activate

# Reinstall requirements
pip install -r requirements.txt
```

**ML model not found**
- Download the model file (128MB) from the team
- Place it at `ml/model.h5` in the project root
- Ensure the file is not corrupted

### Frontend Issues

**Port 3000 already in use**
```bash
# Kill the process or use different port
npm start -- --port=3001
```

**npm install fails**
```bash
# Clear npm cache
npm cache clean --force
# Delete node_modules and package-lock.json
rm -rf node_modules package-lock.json
# Reinstall
npm install
```

**CORS errors in browser**
- Check that backend `.env` includes your frontend origin
- Restart backend after updating ALLOWED_ORIGINS
- Ensure both frontend and backend are running

### Environment Issues

**Virtual environment not activating**
```bash
# Create new virtual environment
cd backend
python -m venv .venv
# Activate it
# Windows
.venv\\Scripts\\Activate.ps1
# macOS/Linux
source .venv/bin/activate
```

**Environment variables not loading**
- Ensure `.env` files exist (copy from `.env.example`)
- Check file permissions
- Restart servers after creating `.env` files

### Mobile App Issues

**Expo Go cannot connect to backend**
- Ensure backend runs with `--host 0.0.0.0`
- Check firewall settings for ports 8000 and 8081
- Verify PC IP address configuration
- Try using `--tunnel` mode if LAN connection fails

**Metro bundler issues**
```bash
# Clear Metro cache
npx expo start --clear
# Reset cache completely
npx expo start -c
```

## Platform-Specific Solutions

### Windows

**PowerShell execution policy**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Windows Firewall**
- Allow ports 8000 (backend), 3000 (frontend), 8081 (Metro)
- Add exceptions for Node.js and Python

**Antivirus software**
- Add exceptions for project directories
- Allow Node.js and Python executables

### macOS

**Homebrew dependencies**
```bash
brew install python@3.9 node
```

**Permission issues**
```bash
# Fix npm permissions
sudo chown -R $(whoami) ~/.npm
sudo chown -R $(whoami) /usr/local/lib/node_modules
```

### Linux

**Package installation**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv nodejs npm

# CentOS/RHEL
sudo yum install python3 python3-pip nodejs npm
```

## Getting Help

1. Check this guide first
2. Search GitHub Issues for similar problems
3. Ask in the team Discord/Slack
4. Check the official documentation for:
   - FastAPI: https://fastapi.tiangolo.com/
   - React: https://reactjs.org/docs/
   - Expo: https://docs.expo.dev/

## Performance Tips

- Keep Node.js and Python versions up to date
- Use SSD storage for better performance
- Close unnecessary applications while developing
- Use `npm start` with `BROWSER=none` to prevent auto-opening browser
- Regularly clean npm cache: `npm cache clean --force`
'''

    with open(guide_file, "w") as f:
        f.write(guide_content)
    print_success("Troubleshooting guide created")

    return True

def main():
    """Main setup function"""
    print(f"{Colors.HEADER}{Colors.BOLD}🌾 RiceGuard Automated Setup{Colors.ENDC}")
    print(f"{Colors.HEADER}Cross-platform setup for all team members{Colors.ENDC}")
    print("=" * 50)

    # Check system requirements
    if not check_system_requirements():
        print_error("System requirements not met. Please install missing components.")
        return False

    # Setup components
    setup_steps = [
        ("Creating directory structure", setup_directory_structure),
        ("Setting up backend environment", setup_backend),
        ("Setting up frontend environment", setup_frontend),
        ("Creating environment templates", setup_environment_files),
        ("Creating development tools", setup_development_tools),
        ("Creating verification script", create_verification_script),
        ("Creating troubleshooting guide", create_troubleshooting_guide),
    ]

    for step_name, step_func in setup_steps:
        try:
            print_status(step_name)
            if not step_func():
                print_error(f"Failed to {step_name.lower()}")
                return False
        except Exception as e:
            print_error(f"Error during {step_name.lower()}: {e}")
            return False

    print("\n" + "=" * 50)
    print(f"{Colors.OKGREEN}{Colors.BOLD}🎉 Setup completed successfully!{Colors.ENDC}")
    print("\n" + "=" * 50)
    print(f"{Colors.BOLD}Next Steps:{Colors.ENDC}")
    print(f"1. {Colors.OKCYAN}Copy environment files:{Colors.ENDC}")
    print(f"   cp backend/.env.example backend/.env")
    print(f"   cp frontend/.env.example frontend/.env")
    print(f"\n2. {Colors.OKCYAN}Configure your MongoDB Atlas connection in backend/.env{Colors.ENDC}")
    print(f"\n3. {Colors.OKCYAN}Download and place the ML model file at ml/model.h5{Colors.ENDC}")
    print(f"\n4. {Colors.OKCYAN}Start development servers:{Colors.ENDC}")
    print(f"   python start-dev.py")
    print(f"   # Or: python dev_runner.py")
    print(f"\n5. {Colors.OKCYAN}Verify setup:{Colors.ENDC}")
    print(f"   python verify-setup.py")
    print(f"\n{Colors.WARNING}⚠️  Important:{Colors.ENDC}")
    print(f"   - Read TROUBLESHOOTING.md for common issues")
    print(f"   - Ensure MongoDB Atlas IP whitelist includes your IP")
    print(f"   - The ML model file (model.h5) must be obtained from the team")
    print("=" * 50)

    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Setup cancelled by user{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"{Colors.ERROR}Unexpected error: {e}{Colors.ENDC}")
        sys.exit(1)