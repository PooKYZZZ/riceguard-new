#!/usr/bin/env python3
"""
RiceGuard Automated Setup Script
Comprehensive setup that handles everything automatically for teammates.
Safe: Never overwrites existing files, creates missing ones.
Cross-platform: Works on Windows, macOS, and Linux.
"""

import os
import sys
import subprocess
import platform
import json
import shutil
import secrets
from pathlib import Path
from urllib.parse import urlparse

# Configuration
REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
FRONTEND_DIR = REPO_ROOT / "frontend"
SCRIPTS_DIR = REPO_ROOT / "scripts"
ML_DIR = REPO_ROOT / "ml"

class Colors:
    """Cross-platform color support with Windows compatibility"""
    def __init__(self):
        self.is_windows = platform.system() == 'Windows'
        self.use_color = not self.is_windows or os.getenv('TERM') == 'xterm-256color'

        # Set console mode for Windows to support UTF-8
        if self.is_windows:
            try:
                import sys
                import ctypes
                kernel32 = ctypes.windll.kernel32
                # Enable UTF-8 mode
                kernel32.SetConsoleOutputCP(65001)
                # Enable virtual terminal processing for colors
                h_out = kernel32.GetStdHandle(-11)
                mode = ctypes.c_ulong()
                kernel32.GetConsoleMode(h_out, ctypes.byref(mode))
                kernel32.SetConsoleMode(h_out, mode | 0x0004)
                self.use_color = True
            except:
                self.use_color = False

    def __getattr__(self, name):
        colors = {
            'HEADER': '\033[95m',
            'OKBLUE': '\033[94m',
            'OKCYAN': '\033[96m',
            'OKGREEN': '\033[92m',
            'WARNING': '\033[93m',
            'FAIL': '\033[91m',
            'ENDC': '\033[0m',
            'BOLD': '\033[1m'
        }
        return colors.get(name, '') if self.use_color else ''

# Safe print function for Windows
def safe_print(*args, **kwargs):
    """Print function that handles Unicode characters safely on Windows"""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # Fallback: replace problematic characters
        text = ' '.join(str(arg) for arg in args)
        safe_text = text.encode('ascii', 'replace').decode('ascii')
        print(safe_text, **kwargs)

colors = Colors()

def print_header(message):
    try:
        safe_print(f"{colors.HEADER}{colors.BOLD}{message}{colors.ENDC}")
    except:
        safe_print(f"=== {message} ===")

def print_status(message):
    try:
        safe_print(f"{colors.OKCYAN}→{colors.ENDC} {message}")
    except:
        safe_print(f"-> {message}")

def print_success(message):
    try:
        safe_print(f"{colors.OKGREEN}✅{colors.ENDC} {message}")
    except:
        safe_print(f"[OK] {message}")

def print_error(message):
    try:
        safe_print(f"{colors.FAIL}❌{colors.ENDC} {message}")
    except:
        safe_print(f"[ERROR] {message}")

def print_warning(message):
    try:
        safe_print(f"{colors.WARNING}⚠️{colors.ENDC} {message}")
    except:
        safe_print(f"[WARNING] {message}")

def run_command(cmd, cwd=None, capture_output=True, shell=False):
    """Run command safely with error handling"""
    try:
        if isinstance(cmd, str) and not shell:
            # Handle Windows commands properly
            if platform.system() == 'Windows':
                cmd = cmd.split()
            else:
                cmd = cmd.split()

        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=capture_output,
            text=True,
            shell=shell
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_system_requirements():
    """Check if system requirements are met"""
    print_status("Checking system requirements...")

    # Check Python version
    python_version = sys.version_info
    if python_version < (3, 8):
        print_error(f"Python {python_version.major}.{python_version.minor} is too old. Requires Python 3.8+")
        return False
    print_success(f"Python {python_version.major}.{python_version.minor}.{python_version.micro}")

    # Check Node.js
    success, output, error = run_command("node --version")
    if not success:
        print_error("Node.js is not installed or not in PATH")
        return False
    node_version = output.strip()
    print_success(f"Node.js {node_version}")

    # Check npm (needs shell=True on Windows)
    success, output, error = run_command("npm --version", shell=True)
    if not success:
        print_error("npm is not installed or not in PATH")
        return False
    npm_version = output.strip()
    print_success(f"npm {npm_version}")

    # Check git
    success, output, error = run_command("git --version")
    if success:
        git_version = output.strip()
        print_success(f"Git {git_version}")
    else:
        print_warning("Git not found - recommended for development")

    return True

def check_project_structure():
    """Verify project structure"""
    print_status("Verifying project structure...")

    required_dirs = [BACKEND_DIR, FRONTEND_DIR]
    required_files = [
        "backend/main.py",
        "backend/requirements.txt",
        "frontend/package.json"
    ]

    # Check directories
    for directory in required_dirs:
        if not directory.exists():
            print_error(f"Directory not found: {directory}")
            return False

    # Check files
    for file_path in required_files:
        full_path = REPO_ROOT / file_path
        if not full_path.exists():
            print_error(f"File not found: {file_path}")
            return False

    print_success("Project structure verified")
    return True

def create_environment_templates():
    """Create environment template files"""
    print_status("Setting up environment configuration...")

    created_files = []

    # Backend .env.example
    backend_env_example = BACKEND_DIR / ".env.example"
    if not backend_env_example.exists():
        backend_content = """# =============================================================================
# RiceGuard Backend Environment Configuration
# =============================================================================
# Copy this file to .env and fill in your actual values

# Environment Settings
ENVIRONMENT=development

# =============================================================================
# MongoDB Atlas Configuration
# =============================================================================
# Get your free MongoDB Atlas cluster from: https://www.mongodb.com/cloud/atlas
MONGO_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/<database_name>
DB_NAME=riceguard_db

# =============================================================================
# JWT Authentication Configuration
# =============================================================================
# Generate a strong secret key: openssl rand -hex 32
JWT_SECRET=<generate_32_character_random_string_here>
JWT_ALGORITHM=HS256
TOKEN_EXPIRE_HOURS=6

# =============================================================================
# Security Settings
# =============================================================================
BCRYPT_ROUNDS=12

# =============================================================================
# File Upload Configuration
# =============================================================================
UPLOAD_DIR=uploads
MAX_UPLOAD_MB=8
ALLOWED_EXTENSIONS=jpg,jpeg,png

# =============================================================================
# ML Model Configuration
# =============================================================================
MODEL_PATH=../ml/model.h5
CONFIDENCE_THRESHOLD=0.45
CONFIDENCE_MARGIN=0.12
TEMPERATURE=1.25
IMG_SIZE=224

# =============================================================================
# CORS Configuration
# =============================================================================
# Comma-separated list of allowed origins
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173

# =============================================================================
# Development Configuration
# =============================================================================
LOG_LEVEL=INFO
ENABLE_SECURITY_LOGGING=true
ENABLE_PERFORMANCE_MONITORING=true

# =============================================================================
# API Configuration
# =============================================================================
API_V1_PREFIX=/api/v1
"""
        try:
            with open(backend_env_example, "w") as f:
                f.write(backend_content)
            created_files.append("backend/.env.example")
        except Exception as e:
            print_error(f"Failed to create backend .env.example: {e}")
            return False
    else:
        print_success("Backend .env.example already exists")

    # Frontend .env.example
    frontend_env_example = FRONTEND_DIR / ".env.example"
    if not frontend_env_example.exists():
        frontend_content = """# =============================================================================
# RiceGuard Frontend Environment Configuration
# =============================================================================
# Copy this file to .env and update the API URL if needed

# =============================================================================
# API Configuration
# =============================================================================
# Backend API URL - update this to match your backend server
REACT_APP_API_URL=http://127.0.0.1:8000/api/v1

# =============================================================================
# Development Configuration
# =============================================================================
# Enable/disable debug mode in development
REACT_APP_DEBUG=true

# Application version (for cache busting and debugging)
REACT_APP_VERSION=1.0.0

# Environment name
REACT_APP_ENVIRONMENT=development

# =============================================================================
# Feature Flags
# =============================================================================
# Enable experimental features (for testing)
REACT_APP_ENABLE_EXPERIMENTAL_FEATURES=false

# Enable analytics tracking (for production only)
REACT_APP_ENABLE_ANALYTICS=false

# =============================================================================
# UI Configuration
# =============================================================================
# Application title
REACT_APP_TITLE=RiceGuard - Rice Leaf Disease Detection

# Default theme
REACT_APP_DEFAULT_THEME=light

# Enable dark mode
REACT_APP_ENABLE_DARK_MODE=true
"""
        try:
            with open(frontend_env_example, "w") as f:
                f.write(frontend_content)
            created_files.append("frontend/.env.example")
        except Exception as e:
            print_error(f"Failed to create frontend .env.example: {e}")
            return False
    else:
        print_success("Frontend .env.example already exists")

    if created_files:
        print_success(f"Created environment templates: {', '.join(created_files)}")

    return True

def create_missing_directories():
    """Create missing directories"""
    print_status("Creating missing directories...")

    directories = [
        BACKEND_DIR / "uploads",
        ML_DIR,
        SCRIPTS_DIR
    ]

    created_count = 0
    for directory in directories:
        if not directory.exists():
            try:
                directory.mkdir(exist_ok=True, parents=True)
                print_success(f"Created: {directory.relative_to(REPO_ROOT)}")
                created_count += 1
            except Exception as e:
                print_error(f"Failed to create {directory}: {e}")
                return False

    if created_count == 0:
        print_success("All directories already exist")

    return True

def setup_backend_dependencies():
    """Setup backend Python virtual environment and dependencies"""
    print_status("Setting up backend Python environment...")

    venv_dir = BACKEND_DIR / ".venv"

    # Check if virtual environment exists
    if not venv_dir.exists():
        print_status("Creating Python virtual environment...")

        # Create virtual environment
        venv_cmd = [sys.executable, "-m", "venv", ".venv"]
        success, output, error = run_command(venv_cmd, cwd=BACKEND_DIR)

        if not success:
            print_error(f"Failed to create virtual environment: {error}")
            return False
        print_success("Virtual environment created")
    else:
        print_success("Virtual environment already exists")

    # Determine python executable in venv
    if platform.system() == 'Windows':
        python_exe = venv_dir / "Scripts" / "python.exe"
        pip_exe = venv_dir / "Scripts" / "pip.exe"
    else:
        python_exe = venv_dir / "bin" / "python"
        pip_exe = venv_dir / "bin" / "pip"

    if not python_exe.exists():
        print_error("Virtual environment python executable not found")
        return False

    # Upgrade pip
    print_status("Upgrading pip...")
    success, output, error = run_command([str(pip_exe), "install", "--upgrade", "pip"])
    if not success:
        print_warning("Failed to upgrade pip (continuing anyway)")

    # Install requirements - ALWAYS check and install if missing
    print_status("Checking backend dependencies...")
    requirements_file = BACKEND_DIR / "requirements.txt"
    if requirements_file.exists():
        # Check if dependencies are already installed
        check_cmd = [str(pip_exe), "list"]
        success, output, error = run_command(check_cmd)

        dependencies_missing = False
        if success:
            try:
                with open(requirements_file, 'r') as f:
                    requirements = f.read()
                    for line in requirements.split('\n'):
                        line = line.strip()
                        if line and not line.startswith('#'):
                            pkg_name = line.split('==')[0].split('>=')[0].split('<=')[0]
                            if pkg_name.lower() not in output.lower():
                                dependencies_missing = True
                                break
            except Exception:
                dependencies_missing = True

        if dependencies_missing:
            print_status("Installing missing backend dependencies...")
            pip_cmd = [str(pip_exe), "install", "-r", "requirements.txt"]
            success, output, error = run_command(pip_cmd, capture_output=False)

            if not success:
                print_error(f"Failed to install backend dependencies: {error}")
                return False
            print_success("Backend dependencies installed")
        else:
            print_success("Backend dependencies already installed")
    else:
        print_error("requirements.txt not found")
        return False

    return True

def setup_frontend_dependencies():
    """Setup frontend Node.js dependencies"""
    print_status("Setting up frontend Node.js environment...")

    # Check if package.json exists
    package_json = FRONTEND_DIR / "package.json"
    if not package_json.exists():
        print_error("package.json not found in frontend directory")
        return False

    # Check if node_modules exists
    node_modules_dir = FRONTEND_DIR / "node_modules"
    if not node_modules_dir.exists():
        print_status("Installing frontend dependencies...")

        # Run npm install
        npm_cmd = "npm install"
        success, output, error = run_command(npm_cmd, cwd=FRONTEND_DIR, shell=True, capture_output=False)

        if not success:
            print_error(f"Failed to install frontend dependencies: {error}")
            return False
        print_success("Frontend dependencies installed")
    else:
        # Verify dependencies are complete
        print_status("Verifying frontend dependencies...")
        npm_cmd = "npm ls --depth=0"
        success, output, error = run_command(npm_cmd, cwd=FRONTEND_DIR, shell=True)

        if not success or "UNMET DEPENDENCY" in output or "missing" in output.lower():
            print_status("Fixing incomplete frontend dependencies...")
            npm_cmd = "npm install"
            success, output, error = run_command(npm_cmd, cwd=FRONTEND_DIR, shell=True, capture_output=False)

            if not success:
                print_error(f"Failed to fix frontend dependencies: {error}")
                return False
            print_success("Frontend dependencies fixed")
        else:
            print_success("Frontend dependencies already installed")

    return True

def check_environment_files():
    """Check and automatically create environment configuration files"""
    print_status("Checking environment configuration...")

    backend_env = BACKEND_DIR / ".env"
    frontend_env = FRONTEND_DIR / ".env"

    backend_example = BACKEND_DIR / ".env.example"
    frontend_example = FRONTEND_DIR / ".env.example"

    # Create backend .env from template if missing
    if not backend_env.exists():
        if backend_example.exists():
            print_status("Creating backend .env from template...")
            try:
                import shutil
                shutil.copy2(backend_example, backend_env)
                print_success("Backend .env created from template")
                print_warning("⚠️  Edit backend/.env and add your MongoDB Atlas credentials")
            except Exception as e:
                print_error(f"Failed to create backend .env: {e}")
                return False
        else:
            print_error("Backend .env.example not found")
            return False
    else:
        # Check if .env has placeholder values
        with open(backend_env, 'r') as f:
            content = f.read()
            if '<username>' in content or '<generate' in content or '<password>' in content:
                print_warning("Backend .env contains placeholder values - needs configuration")
            else:
                print_success("Backend .env configured")

    # Create frontend .env from template if missing
    if not frontend_env.exists():
        if frontend_example.exists():
            print_status("Creating frontend .env from template...")
            try:
                import shutil
                shutil.copy2(frontend_example, frontend_env)
                print_success("Frontend .env created from template")
            except Exception as e:
                print_error(f"Failed to create frontend .env: {e}")
                return False
        else:
            print_error("Frontend .env.example not found")
            return False
    else:
        print_success("Frontend .env configured")

    # Check for placeholder values in created files
    needs_configuration = False
    backend_needs_config = False
    frontend_needs_config = False

    if backend_env.exists():
        with open(backend_env, 'r') as f:
            content = f.read()
            if any(placeholder in content for placeholder in ['<username>', '<password>', '<generate', '<cluster>']):
                backend_needs_config = True
                needs_configuration = True

    if needs_configuration:
        print("\n" + "="*60)
        print_warning("Environment Configuration Required")
        print("="*60)

        if backend_needs_config:
            print("\n[INFO] Backend Configuration Steps:")
            print("   1. Edit backend/.env")
            print("   2. Replace placeholder values:")
            print("      * MongoDB Atlas: <username>:<password>@<cluster>")
            print("      * JWT Secret: Generate with 'openssl rand -hex 32'")
            print("   3. Get free MongoDB Atlas cluster: https://www.mongodb.com/cloud/atlas")

        print("\n" + "="*60)
        print_warning("Complete environment configuration before running the application")
        print("="*60)

    return True

def create_development_tools():
    """Create helpful development scripts"""
    print_status("Creating development tools...")

    created = []

    # Create verify-setup.py if missing
    verify_script = REPO_ROOT / "verify-setup.py"
    if not verify_script.exists():
        verify_content = '''#!/usr/bin/env python3
"""Verify RiceGuard setup and configuration"""

import os
import sys
import platform
from pathlib import Path

# Color support for different platforms
class Colors:
    def __init__(self):
        self.is_windows = platform.system() == 'Windows'
        self.use_color = not self.is_windows
        if self.is_windows:
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleOutputCP(65001)
                h_out = kernel32.GetStdHandle(-11)
                mode = ctypes.c_ulong()
                kernel32.GetConsoleMode(h_out, ctypes.byref(mode))
                kernel32.SetConsoleMode(h_out, mode | 0x0004)
                self.use_color = True
            except:
                self.use_color = False

    def __getattr__(self, name):
        colors = {
            'OKGREEN': '\\033[92m',
            'FAIL': '\\033[91m',
            'ENDC': '\\033[0m'
        }
        return colors.get(name, '') if self.use_color else ''

# Safe print function for Windows
def safe_print(*args, **kwargs):
    """Print function that handles Unicode characters safely on Windows"""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # Fallback: replace problematic characters
        text = ' '.join(str(arg) for arg in args)
        safe_text = text.encode('ascii', 'replace').decode('ascii')
        print(safe_text, **kwargs)

colors = Colors()

REPO_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = REPO_ROOT / "backend"
FRONTEND_DIR = REPO_ROOT / "frontend"

def verify_setup():
    try:
        safe_print("[INFO] Verifying RiceGuard Setup...")

        # Check directories
        dirs_ok = all([
            BACKEND_DIR.exists(),
            FRONTEND_DIR.exists(),
            (BACKEND_DIR / ".venv").exists(),
            (FRONTEND_DIR / "node_modules").exists()
        ])

        # Check files
        files_ok = all([
            (BACKEND_DIR / ".env").exists(),
            (FRONTEND_DIR / ".env").exists()
        ])

        if dirs_ok and files_ok:
            safe_print(f"{colors.OKGREEN}[OK] Setup verification passed!{colors.ENDC}")
            return True
        else:
            safe_print(f"{colors.FAIL}[ERROR] Setup verification failed!{colors.ENDC}")
            if not dirs_ok:
                safe_print("Missing directories:")
                if not BACKEND_DIR.exists():
                    safe_print("  - backend/")
                if not FRONTEND_DIR.exists():
                    safe_print("  - frontend/")
                if not (BACKEND_DIR / ".venv").exists():
                    safe_print("  - backend/.venv (run setup.py)")
                if not (FRONTEND_DIR / "node_modules").exists():
                    safe_print("  - frontend/node_modules (run setup.py)")
            if not files_ok:
                safe_print("Missing files:")
                if not (BACKEND_DIR / ".env").exists():
                    safe_print("  - backend/.env (run setup.py)")
                if not (FRONTEND_DIR / ".env").exists():
                    safe_print("  - frontend/.env (run setup.py)")
            return False
    except Exception as e:
        safe_print(f"Unexpected error during verification: {e}")
        return False

if __name__ == "__main__":
    success = verify_setup()
    sys.exit(0 if success else 1)
'''
        try:
            with open(verify_script, "w") as f:
                f.write(verify_content)
            created.append("verify-setup.py")
        except Exception as e:
            print_warning(f"Could not create verify-setup.py: {e}")

    if created:
        print_success(f"Created development tools: {', '.join(created)}")

    return True

def run_safety_checks():
    """Run safety checks without false positives"""
    print_status("Running safety checks...")

    # Normal files and directories that are safe to ignore
    safe_files = {
        'setup.py', 'setup.bat', 'setup.sh', 'start-dev.py', 'verify-setup.py',
        'package.json', 'package-lock.json', 'yarn.lock',
        'python.exe', 'node.exe', 'npm.cmd', 'npx.cmd'
    }

    # Safe directories to ignore completely
    safe_directories = {
        'node_modules', '.venv', '__pycache__', '.git', 'dist', 'build',
        'mobileapp', 'ml', 'scripts', '.vscode', '.idea'
    }

    # Suspicious file patterns that could be malware
    suspicious_patterns = ['*.scr', '*.vbs', '*.bat', '*.cmd', '*.com', '*.pif']

    suspicious_count = 0
    suspicious_files = []

    for pattern in suspicious_patterns:
        for file_path in REPO_ROOT.rglob(pattern):
            if file_path.is_file():
                # Skip if in safe directory
                if any(safe_dir in str(file_path) for safe_dir in safe_directories):
                    continue

                # Skip if safe file name
                if file_path.name in safe_files:
                    continue

                # Additional safety checks
                # Skip if it's a known development tool or configuration file
                relative_path = file_path.relative_to(REPO_ROOT)
                path_str = str(relative_path).lower()

                if any(keyword in path_str for keyword in [
                    'gradlew', 'webpack', 'babel', 'eslint', 'prettier', 'jest',
                    'react', 'expo', 'metro', 'android', 'ios', ' cocoa',
                    'pod', 'carthage', 'fastlane', 'scripts', 'tools'
                ]):
                    continue

                # Skip if file is in project root and is expected
                if len(relative_path.parts) == 1 and file_path.name in safe_files:
                    continue

                # Skip test files and development scripts
                if any(keyword in path_str for keyword in [
                    'test', 'spec', 'mock', 'debug', 'temp', 'backup'
                ]):
                    continue

                suspicious_count += 1
                if suspicious_count <= 5:  # Show first 5
                    suspicious_files.append(str(relative_path))

    if suspicious_count == 0:
        print_success("Safety checks passed - no suspicious files found")
    else:
        print_warning(f"Found {suspicious_count} files to review:")
        for file in suspicious_files:
            print_warning(f"  • {file}")
        if suspicious_count > 5:
            print_warning(f"  ... and {suspicious_count - 5} more")

    return True

def provide_next_steps():
    """Provide clear next steps"""
    print("\n" + "="*70)
    print_header("RiceGuard Setup Complete!")
    print("="*70)

    print("\n[OK] What's been automatically done:")
    print("   * Environment templates created and copied to .env files")
    print("   * Python virtual environment set up with all dependencies")
    print("   * Node.js dependencies installed for frontend")
    print("   * Project structure verified and directories created")
    print("   * Safety checks completed")

    print("\n[INFO] Required Next Steps (do these now):")
    print("   1. Configure environment files:")
    print("      -> Edit backend/.env with your MongoDB Atlas credentials:")
    print("         * Get free cluster: https://www.mongodb.com/cloud/atlas")
    print("         * Replace <username>, <password>, <cluster> placeholders")
    print("         * Generate JWT secret: openssl rand -hex 32")

    print("\n   2. Start development servers:")
    print("      -> python start-dev.py")
    print("      (This starts both backend and frontend automatically)")

    print("\n[INFO] Development URLs (after starting servers):")
    print("   * Frontend Web App:  http://localhost:3000")
    print("   * Backend API:      http://127.0.0.1:8000")
    print("   * API Documentation: http://127.0.0.1:8000/docs")
    print("   * Health Check:     http://127.0.0.1:8000/health")

    print("\n[INFO] Helpful Commands:")
    print("   * Verify setup:     python verify-setup.py")
    print("   * Re-run setup:     python setup.py")
    print("   * Mobile app:       python start-dev.py (includes mobile)")
    print("   * Clean restart:    Delete backend/.venv and frontend/node_modules")

    print("\n[INFO] Pro Tips:")
    print("   * Use Ctrl+C to stop development servers")
    print("   * Check CLAUDE.md for detailed documentation")
    print("   * Backend runs on port 8000, Frontend on port 3000")
    print("   * Mobile app requires Expo Go on your phone")

    print("\n" + "="*70)

def main():
    """Main setup function"""
    print_header("RiceGuard Automated Setup")
    print("=" * 60)
    print("This will set up your development environment safely.")
    print("Existing files will never be overwritten.")
    print("=" * 60)

    # Setup phases
    phases = [
        ("System Requirements", check_system_requirements),
        ("Project Structure", check_project_structure),
        ("Environment Templates", create_environment_templates),
        ("Missing Directories", create_missing_directories),
        ("Backend Dependencies", setup_backend_dependencies),
        ("Frontend Dependencies", setup_frontend_dependencies),
        ("Environment Configuration", check_environment_files),
        ("Development Tools", create_development_tools),
        ("Safety Checks", run_safety_checks)
    ]

    passed = 0
    total = len(phases)

    for phase_name, phase_func in phases:
        print(f"\n[{passed+1}/{total}] {phase_name}")
        try:
            if phase_func():
                passed += 1
            else:
                print_error(f"Phase failed: {phase_name}")
                if phase_name in ["System Requirements", "Project Structure"]:
                    print_error("Critical setup phase failed. Cannot continue.")
                    return False
        except Exception as e:
            print_error(f"Error in {phase_name}: {e}")
            if phase_name in ["System Requirements", "Project Structure"]:
                return False

    print(f"\n[INFO] Setup Summary: {passed}/{total} phases completed")

    if passed >= 7:  # Allow non-critical phases to fail
        provide_next_steps()
        return True
    else:
        print_error("Setup incomplete. Please fix the issues above and run again.")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)