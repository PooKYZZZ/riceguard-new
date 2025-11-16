#!/usr/bin/env python3
"""
Comprehensive test runner for RiceGuard backend TDD suite.
Provides different test modes and generates detailed reports.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def get_project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent

def get_backend_root():
    """Get the backend root directory."""
    return Path(__file__).parent.parent

def run_command(cmd, cwd=None, capture_output=False):
    """Run a command and return the result."""
    try:
        if capture_output:
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            return result.returncode, result.stdout, result.stderr
        else:
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=cwd,
                timeout=300  # 5 minute timeout
            )
            return result.returncode, None, None
    except subprocess.TimeoutExpired:
        return -1, None, "Command timed out"
    except Exception as e:
        return -1, None, str(e)

def run_fast_tests():
    """Run fast unit tests only."""
    print("🚀 Running fast unit tests...")
    backend_root = get_backend_root()

    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-m", "not slow and not integration",
        "-v",
        "--tb=short",
        "--cov=../",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov/fast",
        "--cov-fail-under=80"
    ]

    returncode, stdout, stderr = run_command(" ".join(cmd), cwd=backend_root, capture_output=True)

    if stdout:
        print(stdout)
    if stderr:
        print(stderr)

    return returncode == 0

def run_all_tests():
    """Run all tests including integration and slow tests."""
    print("🔬 Running all tests (unit + integration + slow)...")
    backend_root = get_backend_root()

    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "--tb=short",
        "--cov=../",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov/all",
        "--cov-report=xml:coverage.xml",
        "--cov-fail-under=90"
    ]

    returncode, stdout, stderr = run_command(" ".join(cmd), cwd=backend_root, capture_output=True)

    if stdout:
        print(stdout)
    if stderr:
        print(stderr)

    return returncode == 0

def run_security_tests():
    """Run security-focused tests."""
    print("🔒 Running security tests...")
    backend_root = get_backend_root()

    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_security_comprehensive.py",
        "-v",
        "--tb=short",
        "-m", "security"
    ]

    returncode, stdout, stderr = run_command(" ".join(cmd), cwd=backend_root, capture_output=True)

    if stdout:
        print(stdout)
    if stderr:
        print(stderr)

    return returncode == 0

def run_performance_tests():
    """Run performance tests."""
    print("⚡ Running performance tests...")
    backend_root = get_backend_root()

    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "--tb=short",
        "-m", "performance"
    ]

    returncode, stdout, stderr = run_command(" ".join(cmd), cwd=backend_root, capture_output=True)

    if stdout:
        print(stdout)
    if stderr:
        print(stderr)

    return returncode == 0

def run_ml_tests():
    """Run ML service tests."""
    print("🤖 Running ML service tests...")
    backend_root = get_backend_root()

    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_ml_service_comprehensive.py",
        "-v",
        "--tb=short",
        "-m", "ml"
    ]

    returncode, stdout, stderr = run_command(" ".join(cmd), cwd=backend_root, capture_output=True)

    if stdout:
        print(stdout)
    if stderr:
        print(stderr)

    return returncode == 0

def run_api_tests():
    """Run API endpoint tests."""
    print("🌐 Running API endpoint tests...")
    backend_root = get_backend_root()

    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_api_endpoints_comprehensive.py",
        "-v",
        "--tb=short",
        "-m", "api"
    ]

    returncode, stdout, stderr = run_command(" ".join(cmd), cwd=backend_root, capture_output=True)

    if stdout:
        print(stdout)
    if stderr:
        print(stderr)

    return returncode == 0

def generate_coverage_report():
    """Generate detailed coverage report."""
    print("📊 Generating coverage report...")
    backend_root = get_backend_root()

    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "--cov=../",
        "--cov-report=html:htmlcov/detailed",
        "--cov-report=xml:coverage-detailed.xml",
        "--cov-report=annotate:htmlcov/annotate"
    ]

    returncode, stdout, stderr = run_command(" ".join(cmd), cwd=backend_root, capture_output=True)

    if returncode == 0:
        print(f"✅ Coverage report generated: {backend_root}/htmlcov/detailed/index.html")
    else:
        print("❌ Failed to generate coverage report")
        if stderr:
            print(stderr)

def check_test_dependencies():
    """Check if all test dependencies are installed."""
    print("🔍 Checking test dependencies...")

    required_packages = [
        "pytest",
        "pytest-asyncio",
        "pytest-cov",
        "pytest-mock",
        "mongomock",
        "factory-boy",
        "faker",
        "freezegun",
        "httpx"
    ]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print(f"❌ Missing test dependencies: {', '.join(missing_packages)}")
        print("Install with: pip install -r requirements.txt")
        return False
    else:
        print("✅ All test dependencies are installed")
        return True

def setup_test_environment():
    """Set up test environment variables."""
    print("⚙️ Setting up test environment...")

    # Set test-specific environment variables
    os.environ["TESTING"] = "true"
    os.environ["MONGO_URI"] = "mongodb://localhost:27017/test_riceguard"
    os.environ["DB_NAME"] = "test_riceguard"
    os.environ["JWT_SECRET"] = "test_jwt_secret_key_for_testing_only"
    os.environ["UPLOAD_DIR"] = "/tmp/test_uploads"
    os.environ["MAX_UPLOAD_MB"] = "2"
    os.environ["MODEL_PATH"] = "/tmp/test_model.h5"
    os.environ["MODEL_TEMPERATURE"] = "1.0"

    # Create test directories
    os.makedirs("/tmp/test_uploads", exist_ok=True)

    print("✅ Test environment configured")

def cleanup_test_environment():
    """Clean up test environment."""
    print("🧹 Cleaning up test environment...")

    # Remove test directories
    import shutil
    test_dirs = ["/tmp/test_uploads"]

    for test_dir in test_dirs:
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir, ignore_errors=True)

    print("✅ Test environment cleaned up")

def main():
    parser = argparse.ArgumentParser(description="RiceGuard Backend Test Runner")
    parser.add_argument(
        "mode",
        choices=["fast", "all", "security", "performance", "ml", "api", "coverage"],
        help="Test mode to run"
    )
    parser.add_argument(
        "--no-setup",
        action="store_true",
        help="Skip environment setup"
    )
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Skip environment cleanup"
    )

    args = parser.parse_args()

    print("🧪 RiceGuard Backend Test Suite")
    print("=" * 40)

    # Check dependencies
    if not check_test_dependencies():
        sys.exit(1)

    # Setup environment
    if not args.no_setup:
        setup_test_environment()

    try:
        # Run tests based on mode
        success = True

        if args.mode == "fast":
            success = run_fast_tests()
        elif args.mode == "all":
            success = run_all_tests()
        elif args.mode == "security":
            success = run_security_tests()
        elif args.mode == "performance":
            success = run_performance_tests()
        elif args.mode == "ml":
            success = run_ml_tests()
        elif args.mode == "api":
            success = run_api_tests()
        elif args.mode == "coverage":
            generate_coverage_report()

        if success:
            print("\n✅ Tests completed successfully!")

            if args.mode != "coverage":
                print("\n📋 Test Summary:")
                print("- All tests passed")
                print("- Coverage report available in htmlcov/")
                print("- Detailed XML report: coverage.xml")
        else:
            print("\n❌ Some tests failed!")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)
    finally:
        # Cleanup environment
        if not args.no_cleanup:
            cleanup_test_environment()

if __name__ == "__main__":
    main()