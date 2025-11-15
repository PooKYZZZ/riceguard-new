#!/usr/bin/env python3
"""
RiceGuard Setup Verification Script
Comprehensive verification of all system components
"""

import os
import sys
import requests
import subprocess
import json
import time
from pathlib import Path
import importlib.util

# Project paths
REPO_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = REPO_ROOT / "backend"
FRONTEND_DIR = REPO_ROOT / "frontend"
MOBILE_DIR = REPO_ROOT / "mobileapp" / "riceguard"
ML_DIR = REPO_ROOT / "ml"
SCRIPTS_DIR = REPO_ROOT / "scripts"

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(message):
    """Print styled header"""
    print(f"{Colors.HEADER}{Colors.BOLD}{message}{Colors.ENDC}")

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

def print_info(message):
    """Print info message"""
    print(f"{Colors.OKBLUE}ℹ️{Colors.ENDC} {message}")

class VerificationResult:
    """Stores verification results"""
    def __init__(self):
        self.results = {}
        self.overall_status = True

    def add_result(self, test_name, passed, message="", details=None):
        """Add a verification result"""
        self.results[test_name] = {
            "passed": passed,
            "message": message,
            "details": details or {}
        }
        if not passed:
            self.overall_status = False

    def print_summary(self):
        """Print verification summary"""
        passed_count = sum(1 for r in self.results.values() if r["passed"])
        total_count = len(self.results)

        print(f"\n{'='*50}")
        print(f"📊 Verification Summary: {passed_count}/{total_count} tests passed")
        print(f"{'='*50}")

        for test_name, result in self.results.items():
            status = "✅" if result["passed"] else "❌"
            print(f"{status} {test_name}")
            if result["message"]:
                print(f"   {result['message']}")

        print(f"\nOverall Status: {'🎉 PASSED' if self.overall_status else '⚠️ FAILED'}")

def check_system_requirements():
    """Check system requirements"""
    print_status("Checking system requirements...")
    result = VerificationResult()

    # Check Python version
    python_version = sys.version_info
    if python_version >= (3, 8):
        result.add_result(
            "Python Version",
            True,
            f"Python {python_version.major}.{python_version.minor}.{python_version.micro}"
        )
    else:
        result.add_result(
            "Python Version",
            False,
            f"Python {python_version.major}.{python_version.minor} found, need 3.8+"
        )

    # Check Node.js
    try:
        node_result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if node_result.returncode == 0:
            result.add_result(
                "Node.js",
                True,
                f"Node.js {node_result.stdout.strip()}"
            )
        else:
            result.add_result("Node.js", False, "Node.js not found")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        result.add_result("Node.js", False, "Node.js not installed")

    # Check npm
    try:
        npm_result = subprocess.run(
            ["npm", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if npm_result.returncode == 0:
            result.add_result(
                "npm",
                True,
                f"npm {npm_result.stdout.strip()}"
            )
        else:
            result.add_result("npm", False, "npm not found")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        result.add_result("npm", False, "npm not installed")

    return result

def check_project_structure():
    """Check project directory structure"""
    print_status("Checking project structure...")
    result = VerificationResult()

    required_dirs = [
        (BACKEND_DIR, "Backend Directory"),
        (FRONTEND_DIR, "Frontend Directory"),
        (ML_DIR, "ML Directory"),
        (SCRIPTS_DIR, "Scripts Directory"),
    ]

    optional_dirs = [
        (MOBILE_DIR, "Mobile App Directory"),
    ]

    for dir_path, name in required_dirs:
        if dir_path.exists():
            result.add_result(name, True, f"Found at {dir_path}")
        else:
            result.add_result(name, False, f"Missing at {dir_path}")

    for dir_path, name in optional_dirs:
        if dir_path.exists():
            result.add_result(name, True, f"Found at {dir_path}")
        else:
            result.add_result(name, False, f"Optional: Missing at {dir_path}")

    return result

def check_backend_setup():
    """Check backend setup and dependencies"""
    print_status("Checking backend setup...")
    result = VerificationResult()

    # Check virtual environment
    venv_dir = BACKEND_DIR / ".venv"
    if venv_dir.exists():
        result.add_result("Backend Virtual Environment", True, "Found .venv directory")
    else:
        result.add_result("Backend Virtual Environment", False, "Virtual environment not created")

    # Check requirements.txt
    requirements_file = BACKEND_DIR / "requirements.txt"
    if requirements_file.exists():
        result.add_result("Backend Requirements", True, "requirements.txt found")
    else:
        result.add_result("Backend Requirements", False, "requirements.txt missing")

    # Check .env file
    env_file = BACKEND_DIR / ".env"
    env_example_file = BACKEND_DIR / ".env.example"

    if env_file.exists():
        result.add_result("Backend Environment File", True, ".env file exists")
    elif env_example_file.exists():
        result.add_result(
            "Backend Environment File",
            False,
            ".env file missing (copy from .env.example)"
        )
    else:
        result.add_result(
            "Backend Environment File",
            False,
            "Both .env and .env.example missing"
        )

    # Check backend files
    backend_files = [
        ("main.py", "Main Application"),
        ("routers.py", "API Routers"),
        ("models.py", "Data Models"),
        ("db.py", "Database Connection"),
        ("ml_service.py", "ML Service"),
    ]

    for filename, name in backend_files:
        file_path = BACKEND_DIR / filename
        if file_path.exists():
            result.add_result(f"Backend File: {name}", True, f"{filename} found")
        else:
            result.add_result(f"Backend File: {name}", False, f"{filename} missing")

    return result

def check_frontend_setup():
    """Check frontend setup and dependencies"""
    print_status("Checking frontend setup...")
    result = VerificationResult()

    # Check package.json
    package_json = FRONTEND_DIR / "package.json"
    if package_json.exists():
        result.add_result("Frontend Package File", True, "package.json found")
    else:
        result.add_result("Frontend Package File", False, "package.json missing")

    # Check node_modules
    node_modules = FRONTEND_DIR / "node_modules"
    if node_modules.exists():
        result.add_result("Frontend Dependencies", True, "node_modules directory exists")
    else:
        result.add_result("Frontend Dependencies", False, "Dependencies not installed")

    # Check .env file
    env_file = FRONTEND_DIR / ".env"
    env_example_file = FRONTEND_DIR / ".env.example"

    if env_file.exists():
        result.add_result("Frontend Environment File", True, ".env file exists")
    elif env_example_file.exists():
        result.add_result(
            "Frontend Environment File",
            False,
            ".env file missing (copy from .env.example)"
        )
    else:
        result.add_result(
            "Frontend Environment File",
            False,
            "Both .env and .env.example missing"
        )

    # Check key frontend files
    frontend_files = [
        ("src/App.js", "Main App Component"),
        ("src/index.js", "Entry Point"),
        ("public/index.html", "HTML Template"),
    ]

    for filename, name in frontend_files:
        file_path = FRONTEND_DIR / filename
        if file_path.exists():
            result.add_result(f"Frontend File: {name}", True, f"{filename} found")
        else:
            result.add_result(f"Frontend File: {name}", False, f"{filename} missing")

    return result

def check_ml_model():
    """Check ML model setup"""
    print_status("Checking ML model setup...")
    result = VerificationResult()

    model_file = ML_DIR / "model.h5"
    model_info_file = ML_DIR / "model_info.json"

    # Check model file
    if model_file.exists():
        file_size = model_file.stat().st_size / (1024 * 1024)  # MB
        result.add_result(
            "ML Model File",
            True,
            f"model.h5 found ({file_size:.1f}MB)"
        )
    else:
        result.add_result(
            "ML Model File",
            False,
            "model.h5 not found (run download-model.py)"
        )

    # Check model info
    if model_info_file.exists():
        result.add_result("ML Model Info", True, "model_info.json found")
    else:
        result.add_result(
            "ML Model Info",
            False,
            "model_info.json missing (run setup-ml-model.py)"
        )

    return result

def check_environment_files():
    """Check environment configuration"""
    print_status("Checking environment configuration...")
    result = VerificationResult()

    # Backend environment
    backend_env = BACKEND_DIR / ".env"
    if backend_env.exists():
        try:
            with open(backend_env) as f:
                env_content = f.read()

            required_vars = [
                "MONGO_URI",
                "DB_NAME",
                "JWT_SECRET",
                "MODEL_PATH"
            ]

            missing_vars = []
            for var in required_vars:
                if f"{var}=" not in env_content or f"{var}=<" in env_content:
                    missing_vars.append(var)

            if not missing_vars:
                result.add_result("Backend Environment Config", True, "All required variables set")
            else:
                result.add_result(
                    "Backend Environment Config",
                    False,
                    f"Missing variables: {', '.join(missing_vars)}"
                )
        except Exception as e:
            result.add_result("Backend Environment Config", False, f"Error reading .env: {e}")
    else:
        result.add_result("Backend Environment Config", False, ".env file not found")

    # Frontend environment
    frontend_env = FRONTEND_DIR / ".env"
    if frontend_env.exists():
        try:
            with open(frontend_env) as f:
                env_content = f.read()

            if "REACT_APP_API_URL=" in env_content:
                result.add_result("Frontend Environment Config", True, "API URL configured")
            else:
                result.add_result("Frontend Environment Config", False, "REACT_APP_API_URL not set")
        except Exception as e:
            result.add_result("Frontend Environment Config", False, f"Error reading .env: {e}")
    else:
        result.add_result("Frontend Environment Config", False, ".env file not found")

    return result

def test_services():
    """Test running services"""
    print_status("Testing running services...")
    result = VerificationResult()

    # Test backend health endpoint
    try:
        response = requests.get(
            "http://127.0.0.1:8000/health",
            timeout=5
        )
        if response.status_code == 200:
            result.add_result("Backend Health Check", True, "Backend responding at port 8000")
        else:
            result.add_result(
                "Backend Health Check",
                False,
                f"Backend returned status {response.status_code}"
            )
    except requests.exceptions.RequestException:
        result.add_result("Backend Health Check", False, "Backend not reachable at http://127.0.0.1:8000")

    # Test frontend accessibility
    try:
        response = requests.get(
            "http://localhost:3000",
            timeout=5
        )
        if response.status_code == 200:
            result.add_result("Frontend Accessibility", True, "Frontend responding at port 3000")
        else:
            result.add_result(
                "Frontend Accessibility",
                False,
                f"Frontend returned status {response.status_code}"
            )
    except requests.exceptions.RequestException:
        result.add_result("Frontend Accessibility", False, "Frontend not reachable at http://localhost:3000")

    # Test API documentation
    try:
        response = requests.get(
            "http://127.0.0.1:8000/docs",
            timeout=5
        )
        if response.status_code == 200:
            result.add_result("API Documentation", True, "Swagger UI accessible")
        else:
            result.add_result(
                "API Documentation",
                False,
                f"API docs returned status {response.status_code}"
            )
    except requests.exceptions.RequestException:
        result.add_result("API Documentation", False, "API documentation not accessible")

    return result

def main():
    """Main verification function"""
    print_header("🔍 RiceGuard Setup Verification")
    print("Comprehensive system verification and diagnostics")
    print("=" * 60)

    all_results = []

    # Run all verification checks
    verification_checks = [
        ("System Requirements", check_system_requirements),
        ("Project Structure", check_project_structure),
        ("Backend Setup", check_backend_setup),
        ("Frontend Setup", check_frontend_setup),
        ("ML Model Setup", check_ml_model),
        ("Environment Configuration", check_environment_files),
        ("Running Services", test_services),
    ]

    for check_name, check_func in verification_checks:
        print(f"\n{Colors.HEADER}{Colors.BOLD}{check_name}{Colors.ENDC}")
        print("-" * 40)

        try:
            result = check_func()
            result.print_summary()
            all_results.append(result)
        except Exception as e:
            print_error(f"Verification failed: {e}")
            all_results.append(VerificationResult())

    # Overall summary
    print(f"\n{Colors.HEADER}{Colors.BOLD}Overall Verification Summary{Colors.ENDC}")
    print("=" * 60)

    total_passed = 0
    total_tests = 0

    for result in all_results:
        for test_name, test_result in result.results.items():
            total_tests += 1
            if test_result["passed"]:
                total_passed += 1

    success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0

    print(f"📊 Total Tests: {total_tests}")
    print(f"✅ Passed: {total_passed}")
    print(f"❌ Failed: {total_tests - total_passed}")
    print(f"📈 Success Rate: {success_rate:.1f}%")

    if success_rate >= 90:
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}🎉 Excellent! Your setup is ready to use!{Colors.ENDC}")
    elif success_rate >= 70:
        print(f"\n{Colors.WARNING}⚠️ Good progress! Some items need attention.{Colors.ENDC}")
    else:
        print(f"\n{Colors.FAIL}❌ Setup needs significant work. See details above.{Colors.ENDC}")

    print(f"\n{Colors.BOLD}Next Steps:{Colors.ENDC}")
    print(f"1. Fix any failed tests shown above")
    print(f"2. Run 'python setup.py' if setup is incomplete")
    print(f"3. Start development servers with 'python start-dev.py'")
    print(f"4. Read TROUBLESHOOTING.md for common issues")

    return 0 if success_rate >= 70 else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Verification cancelled by user{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.FAIL}Unexpected error: {e}{Colors.ENDC}")
        sys.exit(1)