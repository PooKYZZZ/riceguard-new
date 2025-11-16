#!/usr/bin/env python3
"""
RiceGuard Development Startup Script

This script helps start both backend and frontend services for development.
It checks dependencies and provides clear instructions.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def check_node_version():
    """Check if Node.js is installed"""
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✅ Node.js {version}")
            return True
    except FileNotFoundError:
        pass

    print("❌ Node.js is not installed or not in PATH")
    print("   Download from: https://nodejs.org/")
    return False

def check_mongodb():
    """Check if MongoDB is running"""
    try:
        # Try to connect to MongoDB
        import pymongo
        client = pymongo.MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=2000)
        client.admin.command('ping')
        print("✅ MongoDB is running")
        client.close()
        return True
    except Exception:
        print("❌ MongoDB is not running or not accessible")
        print("   Start MongoDB service or install MongoDB Community Server")
        return False

def install_python_dependencies():
    """Install Python dependencies if needed"""
    backend_path = Path(__file__).parent / "src" / "backend"
    requirements_file = backend_path / "requirements.txt"

    if not requirements_file.exists():
        print("❌ requirements.txt not found")
        return False

    print("📦 Installing Python dependencies...")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ], check=True, cwd=backend_path)
        print("✅ Python dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Python dependencies: {e}")
        return False

def install_node_dependencies():
    """Install Node.js dependencies if needed"""
    frontend_path = Path(__file__).parent / "src" / "frontend"
    package_json = frontend_path / "package.json"
    node_modules = frontend_path / "node_modules"

    if not package_json.exists():
        print("❌ package.json not found")
        return False

    if node_modules.exists():
        print("✅ Node dependencies already installed")
        return True

    print("📦 Installing Node.js dependencies...")
    try:
        subprocess.run(['npm', 'install'], check=True, cwd=frontend_path)
        print("✅ Node dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Node dependencies: {e}")
        return False

def start_backend():
    """Start the backend server"""
    backend_path = Path(__file__).parent / "src" / "backend"

    print("🚀 Starting backend server...")
    try:
        # Start backend in background
        process = subprocess.Popen([
            sys.executable, "main.py"
        ], cwd=backend_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Give it time to start
        time.sleep(3)

        if process.poll() is None:
            print("✅ Backend server started successfully")
            print("   URL: http://localhost:8000")
            print("   Health check: http://localhost:8000/health")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Backend failed to start")
            if stderr:
                print(f"   Error: {stderr.decode()}")
            return None
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        return None

def start_frontend():
    """Start the frontend development server"""
    frontend_path = Path(__file__).parent / "src" / "frontend"

    print("🚀 Starting frontend development server...")
    try:
        # Start frontend in background
        process = subprocess.Popen([
            'npm', 'start'
        ], cwd=frontend_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        print("✅ Frontend server starting...")
        print("   URL: http://localhost:3000")
        print("   (May take a few seconds to open in browser)")
        return process
    except Exception as e:
        print(f"❌ Failed to start frontend: {e}")
        return None

def main():
    """Main startup function"""
    print("🌾 RiceGuard Development Environment Setup")
    print("=" * 50)

    # Check prerequisites
    checks = [
        ("Python", check_python_version),
        ("Node.js", check_node_version),
        ("MongoDB", check_mongodb),
    ]

    all_passed = True
    for name, check_func in checks:
        print(f"\n🔍 Checking {name}...")
        if not check_func():
            all_passed = False

    if not all_passed:
        print("\n❌ Some prerequisites are missing. Please install them and try again.")
        return

    # Install dependencies
    print(f"\n📦 Installing dependencies...")
    deps_ok = True

    print("\n🔍 Python dependencies...")
    if not install_python_dependencies():
        deps_ok = False

    print("\n🔍 Node.js dependencies...")
    if not install_node_dependencies():
        deps_ok = False

    if not deps_ok:
        print("\n❌ Failed to install dependencies")
        return

    # Start services
    print(f"\n🚀 Starting services...")

    print("\n🔍 Starting backend...")
    backend_process = start_backend()
    if not backend_process:
        print("❌ Failed to start backend. Exiting.")
        return

    print("\n🔍 Starting frontend...")
    frontend_process = start_frontend()
    if not frontend_process:
        print("❌ Failed to start frontend. Exiting.")
        if backend_process:
            backend_process.terminate()
        return

    # Success message
    print(f"\n🎉 RiceGuard is now running!")
    print("=" * 50)
    print("📱 Frontend: http://localhost:3000")
    print("🔧 Backend:  http://localhost:8000")
    print("🏥 Health:   http://localhost:8000/health")
    print("\n📝 Next steps:")
    print("1. Open http://localhost:3000 in your browser")
    print("2. Register a new account")
    print("3. Upload an image to test disease detection")
    print("\n⏹️  Press Ctrl+C to stop both servers")

    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping servers...")
        if backend_process:
            backend_process.terminate()
        if frontend_process:
            frontend_process.terminate()
        print("✅ Servers stopped")

if __name__ == "__main__":
    main()