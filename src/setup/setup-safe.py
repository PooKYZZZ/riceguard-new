#!/usr/bin/env python3
"""
RiceGuard Safe Setup Script - VERSION FOR TESTING
This version ONLY checks dependencies and creates missing files - never overwrites existing ones
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

# Configuration
REPO_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = REPO_ROOT / "backend"
FRONTEND_DIR = REPO_ROOT / "frontend"
SCRIPTS_DIR = REPO_ROOT / "scripts"

# Colors (safe for Windows console)
class Colors:
    HEADER = '\033[95m' if platform.system() != 'Windows' else ''
    OKBLUE = '\033[94m' if platform.system() != 'Windows' else ''
    OKCYAN = '\033[96m' if platform.system() != 'Windows' else ''
    OKGREEN = '\033[92m' if platform.system() != 'Windows' else ''
    WARNING = '\033[93m' if platform.system() != 'Windows' else ''
    FAIL = '\033[91m' if platform.system() != 'Windows' else ''
    ENDC = '\033[0m' if platform.system() != 'Windows' else ''
    BOLD = '\033[1m' if platform.system() != 'Windows' else ''

def print_status(message):
    print(f"{Colors.OKCYAN}[INFO]{Colors.ENDC} {message}")

def print_success(message):
    print(f"{Colors.OKGREEN}[SUCCESS]{Colors.ENDC} {message}")

def print_warning(message):
    print(f"{Colors.WARNING}[WARNING]{Colors.ENDC} {message}")

def print_error(message):
    print(f"{Colors.FAIL}[ERROR]{Colors.ENDC} {message}")

def check_system_requirements():
    """Check system requirements"""
    print_status("Checking system requirements...")

    # Check Python
    try:
        python_version = sys.version_info
        if python_version >= (3, 8):
            print_success(f"Python {python_version.major}.{python_version.minor}.{python_version.micro} found")
        else:
            print_error(f"Python {python_version.major}.{python_version.minor} is too old. Please upgrade to 3.8+")
            return False
    except Exception as e:
        print_error(f"Python check failed: {e}")
        return False

    # Check Node.js
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            node_version = result.stdout.strip()
            print_success(f"Node.js {node_version} found")
        else:
            print_error("Node.js not found")
            return False
    except FileNotFoundError:
        print_error("Node.js is not installed or not in PATH")
        return False
    except Exception as e:
        print_error(f"Node.js check failed: {e}")
        return False

    return True

def check_project_structure():
    """Check if essential project files exist"""
    print_status("Checking project structure...")

    required_files = [
        "backend/main.py",
        "backend/requirements.txt",
        "frontend/package.json"
    ]

    missing_files = []
    for file_path in required_files:
        if not (REPO_ROOT / file_path).exists():
            missing_files.append(file_path)

    if missing_files:
        print_error("Missing required files:")
        for file_path in missing_files:
            print(f"  - {file_path}")
        return False

    print_success("All required project files found")
    return True

def check_backend_dependencies():
    """Check backend requirements"""
    print_status("Checking backend dependencies...")

    req_file = BACKEND_DIR / "requirements.txt"
    if not req_file.exists():
        print_error("backend/requirements.txt not found")
        return False

    try:
        with open(req_file, 'r') as f:
            requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        print_success(f"Found {len(requirements)} backend dependencies")
        return True
    except Exception as e:
        print_error(f"Error reading requirements.txt: {e}")
        return False

def check_frontend_dependencies():
    """Check frontend package.json"""
    print_status("Checking frontend dependencies...")

    package_json = FRONTEND_DIR / "package.json"
    if not package_json.exists():
        print_error("frontend/package.json not found")
        return False

    try:
        import json
        with open(package_json, 'r') as f:
            package_data = json.load(f)
        dependencies = package_data.get('dependencies', {})
        print_success(f"Found {len(dependencies)} frontend dependencies")
        return True
    except Exception as e:
        print_error(f"Error reading package.json: {e}")
        return False

def check_virtual_environment():
    """Check if virtual environment exists"""
    print_status("Checking Python virtual environment...")

    venv_dir = BACKEND_DIR / ".venv"
    if venv_dir.exists():
        print_success("Virtual environment found")
        return True
    else:
        print_warning("Virtual environment not found - you may need to create it")
        return False

def check_node_modules():
    """Check if node_modules exists"""
    print_status("Checking Node.js modules...")

    node_modules_dir = FRONTEND_DIR / "node_modules"
    if node_modules_dir.exists():
        print_success("Node.js modules found")
        return True
    else:
        print_warning("node_modules not found - you may need to run 'npm install'")
        return False

def create_missing_directories():
    """Create missing directories (safe operation)"""
    print_status("Creating missing directories...")

    directories_to_create = [
        BACKEND_DIR / "uploads",
        REPO_ROOT / "ml",
        SCRIPTS_DIR
    ]

    created_count = 0
    for directory in directories_to_create:
        if not directory.exists():
            try:
                directory.mkdir(exist_ok=True)
                print_success(f"Created directory: {directory}")
                created_count += 1
            except Exception as e:
                print_error(f"Failed to create directory {directory}: {e}")
                return False

    if created_count == 0:
        print_success("All directories already exist")

    return True

def check_environment_files():
    """Check if environment files exist"""
    print_status("Checking environment configuration...")

    backend_env_example = BACKEND_DIR / ".env.example"
    frontend_env_example = FRONTEND_DIR / ".env.example"

    if not backend_env_example.exists():
        print_warning("backend/.env.example not found")
    else:
        print_success("backend/.env.example found")

    if not frontend_env_example.exists():
        print_warning("frontend/.env.example not found")
    else:
        print_success("frontend/.env.example found")

    return True

def run_safety_checks():
    """Run comprehensive safety checks"""
    print_status("Running safety checks...")

    # Check for dangerous file patterns
    dangerous_patterns = [
        "*.exe", "*.bat", "*.cmd", "*.scr", "*.vbs", "*.js", "*.jar"
    ]

    suspicious_files = []
    for pattern in dangerous_patterns:
        for file_path in REPO_ROOT.rglob(pattern):
            if file_path.is_file() and file_path.name not in ['setup.bat', 'setup.sh', 'start-dev.py']:
                suspicious_files.append(file_path)

    if suspicious_files:
        print_warning(f"Found {len(suspicious_files)} suspicious files - please review manually")
        for file_path in suspicious_files[:5]:  # Show first 5
            print(f"  - {file_path}")
    else:
        print_success("No suspicious files found")

    return True

def main():
    """Main setup function"""
    print(f"{Colors.HEADER}{Colors.BOLD}RiceGuard Safe Setup{Colors.ENDC}")
    print("=" * 50)

    checks = [
        ("System Requirements", check_system_requirements),
        ("Project Structure", check_project_structure),
        ("Backend Dependencies", check_backend_dependencies),
        ("Frontend Dependencies", check_frontend_dependencies),
        ("Virtual Environment", check_virtual_environment),
        ("Node.js Modules", check_node_modules),
        ("Environment Files", check_environment_files),
        ("Safety Checks", run_safety_checks),
        ("Create Missing Directories", create_missing_directories)
    ]

    passed = 0
    total = len(checks)

    for check_name, check_func in checks:
        print(f"\n[{passed+1}/{total}] {check_name}")
        try:
            if check_func():
                passed += 1
            else:
                print_error(f"Check failed: {check_name}")
        except Exception as e:
            print_error(f"Error in {check_name}: {e}")

    print("\n" + "=" * 50)
    print(f"Setup Complete: {passed}/{total} checks passed")

    if passed == total:
        print_success("All checks passed! Your project is ready for development.")
        print("\nNext steps:")
        print("1. Copy environment templates:")
        print("   cp backend/.env.example backend/.env")
        print("   cp frontend/.env.example frontend/.env")
        print("2. Edit backend/.env with your MongoDB Atlas credentials")
        print("3. Install dependencies if needed:")
        print("   cd backend && python -m venv .venv && .venv\\Scripts\\Activate")
        print("   pip install -r requirements.txt")
        print("   cd ../frontend && npm install")
        print("4. Start development:")
        print("   python start-dev.py")
        return True
    else:
        print_warning("Some checks failed. Please review the output above.")
        print("\nFor help, see:")
        print("- TROUBLESHOOTING.md for common issues")
        print("- CLAUDE.md for project documentation")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nSetup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)