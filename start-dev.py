#!/usr/bin/env python3
"""
RiceGuard Development Server Starter
Starts all development services with one command
Cross-platform support for Windows, macOS, and Linux
"""

import os
import sys
import time
import signal
import subprocess
import threading
import platform
from pathlib import Path

# Configuration
REPO_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = REPO_ROOT / "backend"
FRONTEND_DIR = REPO_ROOT / "frontend"
MOBILE_DIR = REPO_ROOT / "mobileapp" / "riceguard"

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

class ServiceManager:
    """Manages multiple development services"""

    def __init__(self):
        self.processes = []
        self.running = True

    def find_python_executable(self):
        """Find the best Python executable (prefer virtual environment)"""
        # Check for virtual environment first
        venv_python = BACKEND_DIR / ".venv" / ("Scripts" if os.name == "nt" else "bin") / ("python.exe" if os.name == "nt" else "python")
        if venv_python.exists():
            return str(venv_python)

        # Fallback to system Python
        return sys.executable

    def stream_output(self, process, service_name):
        """Stream process output with service prefix"""
        try:
            while self.running and process.poll() is None:
                line = process.stdout.readline()
                if line:
                    # Remove trailing newline and add service prefix
                    clean_line = line.rstrip().decode('utf-8', errors='ignore')
                    if service_name == "backend":
                        # Color backend output blue
                        print(f"{Colors.OKBLUE}[backend]{Colors.ENDC} {clean_line}")
                    elif service_name == "frontend":
                        # Color frontend output green
                        print(f"{Colors.OKGREEN}[frontend]{Colors.ENDC} {clean_line}")
                    elif service_name == "mobile":
                        # Color mobile output purple
                        print(f"{Colors.HEADER}[mobile]{Colors.ENDC} {clean_line}")
        except Exception as e:
            if self.running:
                print_error(f"Error streaming {service_name} output: {e}")

    def start_backend(self):
        """Start the FastAPI backend server"""
        print_status("Starting FastAPI backend server...")

        python_exe = self.find_python_executable()
        cmd = [
            python_exe, "-m", "uvicorn",
            "main:app",
            "--reload",
            "--host", "0.0.0.0",
            "--port", "8000"
        ]

        try:
            process = subprocess.Popen(
                cmd,
                cwd=BACKEND_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=False,
                bufsize=1
            )

            self.processes.append(("backend", process))

            # Start output streaming in separate thread
            threading.Thread(
                target=self.stream_output,
                args=(process, "backend"),
                daemon=True
            ).start()

            print_success(f"Backend started: http://127.0.0.1:8000")
            return True

        except Exception as e:
            print_error(f"Failed to start backend: {e}")
            return False

    def start_frontend(self):
        """Start the React frontend development server"""
        print_status("Starting React frontend server...")

        cmd = ["npm", "start"]

        # Set environment variables
        env = os.environ.copy()
        env["BROWSER"] = "none"  # Prevent auto-opening browser
        env["PORT"] = "3000"

        try:
            process = subprocess.Popen(
                cmd,
                cwd=FRONTEND_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=False,
                bufsize=1,
                env=env
            )

            self.processes.append(("frontend", process))

            # Start output streaming in separate thread
            threading.Thread(
                target=self.stream_output,
                args=(process, "frontend"),
                daemon=True
            ).start()

            print_success(f"Frontend started: http://localhost:3000")
            return True

        except Exception as e:
            print_error(f"Failed to start frontend: {e}")
            return False

    def start_mobile(self):
        """Start the Expo mobile development server (optional)"""
        if not MOBILE_DIR.exists():
            print_warning("Mobile app directory not found, skipping mobile server")
            return False

        print_status("Starting Expo mobile development server...")

        cmd = ["npx", "expo", "start", "--lan", "--clear"]

        # Set environment variables for mobile
        env = os.environ.copy()
        # Update these with your actual PC IP for mobile development
        env["EXPO_PUBLIC_API_BASE_URL"] = "http://127.0.0.1:8000/api/v1"
        env["REACT_NATIVE_PACKAGER_HOSTNAME"] = "127.0.0.1"

        try:
            process = subprocess.Popen(
                cmd,
                cwd=MOBILE_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=False,
                bufsize=1,
                env=env
            )

            self.processes.append(("mobile", process))

            # Start output streaming in separate thread
            threading.Thread(
                target=self.stream_output,
                args=(process, "mobile"),
                daemon=True
            ).start()

            print_success("Mobile server started (scan QR code with Expo Go)")
            return True

        except Exception as e:
            print_error(f"Failed to start mobile server: {e}")
            return False

    def stop_all(self):
        """Stop all running processes"""
        print_status("Stopping all services...")
        self.running = False

        for service_name, process in self.processes:
            try:
                if process.poll() is None:
                    print_status(f"Stopping {service_name}...")

                    # Try graceful shutdown first
                    if os.name == "nt":
                        process.send_signal(signal.CTRL_BREAK_EVENT)
                    else:
                        process.terminate()

                    # Wait a bit for graceful shutdown
                    time.sleep(2)

                    # Force kill if still running
                    if process.poll() is None:
                        process.kill()

                    print_success(f"{service_name.capitalize()} stopped")

            except Exception as e:
                print_error(f"Error stopping {service_name}: {e}")

        self.processes.clear()

    def wait_for_startup(self, timeout=30):
        """Wait for services to start up"""
        print_status("Waiting for services to start...")

        start_time = time.time()
        while time.time() - start_time < timeout:
            # Check if any process has exited with an error
            for service_name, process in self.processes:
                if process.poll() is not None and process.returncode != 0:
                    print_error(f"{service_name.capitalize()} failed to start (exit code: {process.returncode})")
                    return False

            # Simple heuristic: if processes are still running after a few seconds, assume they started
            if time.time() - start_time > 5:
                all_running = all(process.poll() is None for _, process in self.processes)
                if all_running:
                    return True

            time.sleep(0.5)

        return True

    def monitor_services(self):
        """Monitor running services and handle shutdown"""
        try:
            while self.running:
                time.sleep(1)

                # Check if any process has died
                for service_name, process in self.processes:
                    if process.poll() is not None:
                        if process.returncode != 0:
                            print_error(f"{service_name.capitalize()} process died unexpectedly")
                            return False
                        else:
                            print_warning(f"{service_name.capitalize()} process ended normally")

        except KeyboardInterrupt:
            pass
        finally:
            self.stop_all()

def check_prerequisites():
    """Check if all prerequisites are met"""
    print_status("Checking prerequisites...")

    # Check backend directory
    if not BACKEND_DIR.exists():
        print_error("Backend directory not found!")
        return False

    # Check frontend directory
    if not FRONTEND_DIR.exists():
        print_error("Frontend directory not found!")
        return False

    # Check backend virtual environment
    venv_dir = BACKEND_DIR / ".venv"
    if not venv_dir.exists():
        print_warning("Backend virtual environment not found. Run 'python setup.py' first.")
        return False

    # Check backend requirements
    requirements_file = BACKEND_DIR / "requirements.txt"
    if not requirements_file.exists():
        print_error("Backend requirements.txt not found!")
        return False

    # Check frontend node_modules
    node_modules = FRONTEND_DIR / "node_modules"
    if not node_modules.exists():
        print_warning("Frontend dependencies not installed. Run 'npm install' in frontend directory.")
        return False

    print_success("Prerequisites check passed")
    return True

def show_usage():
    """Show usage instructions"""
    print_header("🌾 RiceGuard Development Server")
    print("=" * 50)
    print()
    print("Usage:")
    print("  python start-dev.py [options]")
    print()
    print("Options:")
    print("  --no-mobile    Skip mobile app server")
    print("  --backend-only Start only backend server")
    print("  --frontend-only Start only frontend server")
    print("  --mobile-only  Start only mobile server")
    print("  --help         Show this help message")
    print()
    print("Services:")
    print("  🖥️  Backend API:   http://127.0.0.1:8000")
    print("  🌐 Frontend Web:  http://localhost:3000")
    print("  📱 Mobile App:    Expo Go QR code")
    print()
    print("Press Ctrl+C to stop all services")
    print("=" * 50)

def main():
    """Main function"""
    # Parse command line arguments
    args = sys.argv[1:]

    if "--help" in args or "-h" in args:
        show_usage()
        return 0

    backend_only = "--backend-only" in args
    frontend_only = "--frontend-only" in args
    mobile_only = "--mobile-only" in args
    no_mobile = "--no-mobile" in args

    # Show header
    print_header("🚀 RiceGuard Development Server")
    print("=" * 50)

    # Check prerequisites
    if not check_prerequisites():
        print_error("Prerequisites check failed. Run 'python setup.py' first.")
        return 1

    # Create service manager
    manager = ServiceManager()

    try:
        # Start services based on arguments
        if backend_only:
            if not manager.start_backend():
                return 1
        elif frontend_only:
            if not manager.start_frontend():
                return 1
        elif mobile_only:
            if not manager.start_mobile():
                return 1
        else:
            # Start all services
            if not manager.start_backend():
                return 1

            time.sleep(2)  # Give backend time to start

            if not manager.start_frontend():
                return 1

            if not no_mobile:
                time.sleep(1)  # Give frontend time to start
                manager.start_mobile()  # Mobile is optional

        # Wait for startup
        if manager.wait_for_startup():
            print("\n" + "=" * 50)
            print(f"{Colors.BOLD}🎉 Development servers started successfully!{Colors.ENDC}")
            print()
            print("🔗 Available Services:")
            if backend_only or not frontend_only:
                print(f"  🖥️  Backend API:    http://127.0.0.1:8000")
                print(f"  📚 API Docs:      http://127.0.0.1:8000/docs")
            if frontend_only or not backend_only:
                print(f"  🌐 Frontend Web:   http://localhost:3000")
            if not no_mobile and not backend_only and not frontend_only and not mobile_only:
                print(f"  📱 Mobile App:     Scan QR code in Expo Go")

            print()
            print("🛠️ Development Tools:")
            print(f"  🔍 Verify Setup:   python verify-setup.py")
            print(f"  🗄️ Database:       python scripts/setup-database.py")
            print(f"  🧠 ML Model:       python scripts/setup-ml-model.py")

            print()
            print("⚠️ Press Ctrl+C to stop all servers")
            print("=" * 50)

            # Monitor services
            manager.monitor_services()
        else:
            print_error("Service startup failed")
            return 1

    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Shutdown requested by user{Colors.ENDC}")
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return 1
    finally:
        manager.stop_all()

    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print_error(f"Fatal error: {e}")
        sys.exit(1)