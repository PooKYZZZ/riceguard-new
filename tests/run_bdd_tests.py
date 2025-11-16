#!/usr/bin/env python3
"""
RiceGuard BDD Test Runner
Comprehensive BDD testing framework for RiceGuard application
"""

import os
import sys
import subprocess
import argparse
import time
from pathlib import Path
from datetime import datetime

class Colors:
    """Cross-platform color support"""
    def __init__(self):
        import platform
        self.is_windows = platform.system() == 'Windows'
        self.use_color = not self.is_windows

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

colors = Colors()

def print_status(message, color=None):
    """Print colored status message"""
    if color is None:
        color = colors.OKCYAN
    print(f"{color}→{colors.ENDC} {message}")

def print_success(message):
    print(f"{colors.OKGREEN}✅{colors.ENDC} {message}")

def print_error(message):
    print(f"{colors.FAIL}❌{colors.ENDC} {message}")

def print_warning(message):
    print(f"{colors.WARNING}⚠️{colors.ENDC} {message}")

def check_environment():
    """Check if the testing environment is properly configured"""
    print_status("Checking test environment...")

    # Check if we're in the right directory
    if not Path("tests").exists():
        print_error("tests/ directory not found. Run from project root.")
        return False

    # Check required files
    required_files = [
        "tests/behave.ini",
        "tests/features/user_authentication.feature",
        "tests/features/disease_detection.feature",
        "tests/features/scan_history.feature",
        "tests/features/security_and_privacy.feature",
        "tests/features/performance_and_scalability.feature"
    ]

    for file_path in required_files:
        if not Path(file_path).exists():
            print_error(f"Required file missing: {file_path}")
            return False

    # Check if behave is installed
    try:
        result = subprocess.run([sys.executable, "-m", "behave", "--version"],
                              capture_output=True, text=True)
        if result.returncode != 0:
            print_error("behave is not installed. Run: pip install -r tests/requirements.txt")
            return False
    except Exception:
        print_error("Failed to check behave installation")
        return False

    print_success("Environment check passed")
    return True

def install_dependencies():
    """Install BDD testing dependencies"""
    print_status("Installing BDD dependencies...")

    try:
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "tests/requirements.txt"
        ], capture_output=True, text=True)

        if result.returncode != 0:
            print_error(f"Failed to install dependencies: {result.stderr}")
            return False

        print_success("Dependencies installed successfully")
        return True
    except Exception as e:
        print_error(f"Failed to install dependencies: {e}")
        return False

def setup_test_environment():
    """Setup test environment and services"""
    print_status("Setting up test environment...")

    # Create reports directory
    reports_dir = Path("tests/reports")
    reports_dir.mkdir(exist_ok=True)

    # Create allure results directory
    allure_dir = reports_dir / "allure"
    allure_dir.mkdir(exist_ok=True)

    # Set environment variables for testing
    os.environ["TESTING"] = "true"
    os.environ["LOG_LEVEL"] = "DEBUG"

    print_success("Test environment setup complete")
    return True

def run_specific_feature(feature_name, tags=None):
    """Run a specific feature file"""
    print_status(f"Running feature: {feature_name}")

    cmd = [sys.executable, "-m", "behave"]

    # Add feature file
    feature_path = f"tests/features/{feature_name}.feature"
    if Path(feature_path).exists():
        cmd.append(feature_path)
    else:
        print_error(f"Feature file not found: {feature_path}")
        return False

    # Add tags if specified
    if tags:
        cmd.extend(["--tags", tags])

    # Add output formatting
    cmd.extend([
        "--format", "pretty",
        "--format", "json.pretty:reports/behave_report.json",
        "--format", "allure:reports/allure"
    ])

    # Add JUnit output for CI
    cmd.extend(["--junit", "--junit-directory", "reports"])

    try:
        start_time = time.time()
        result = subprocess.run(cmd, cwd=Path.cwd())
        duration = time.time() - start_time

        if result.returncode == 0:
            print_success(f"Feature '{feature_name}' completed successfully in {duration:.2f}s")
            return True
        else:
            print_error(f"Feature '{feature_name}' failed with exit code {result.returncode}")
            return False
    except Exception as e:
        print_error(f"Failed to run feature '{feature_name}': {e}")
        return False

def run_all_tests(tags=None):
    """Run all BDD tests"""
    print_status("Running all BDD tests...")

    cmd = [sys.executable, "-m", "behave", "tests/features"]

    # Add tags if specified
    if tags:
        cmd.extend(["--tags", tags])

    # Add output formatting
    cmd.extend([
        "--format", "pretty",
        "--format", "json.pretty:reports/behave_report.json",
        "--format", "allure:reports/allure"
    ])

    # Add JUnit output for CI
    cmd.extend(["--junit", "--junit-directory", "reports"])

    # Add verbose output
    cmd.append("--verbose")

    try:
        start_time = time.time()
        print(f"\n{colors.OKBLUE}Starting BDD test run at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{colors.ENDC}")
        print("=" * 60)

        result = subprocess.run(cmd, cwd=Path.cwd())
        duration = time.time() - start_time

        print("=" * 60)
        if result.returncode == 0:
            print_success(f"All tests passed successfully in {duration:.2f}s")
            return True
        else:
            print_error(f"Tests failed with exit code {result.returncode}")
            return False
    except Exception as e:
        print_error(f"Failed to run tests: {e}")
        return False

def generate_reports():
    """Generate test reports"""
    print_status("Generating test reports...")

    # Generate Allure report if available
    try:
        result = subprocess.run([
            "allure", "generate", "tests/reports/allure",
            "--clean", "-o", "tests/reports/allure-report"
        ], capture_output=True, text=True)

        if result.returncode == 0:
            print_success("Allure report generated: tests/reports/allure-report/index.html")
        else:
            print_warning("Allure report generation failed (allure command not found)")
    except Exception:
        print_warning("Allure not available - skipping report generation")

def cleanup():
    """Clean up test artifacts"""
    print_status("Cleaning up test artifacts...")

    # Remove temporary files
    temp_patterns = [
        "tests/reports/*.tmp",
        "tests/reports/*.log"
    ]

    for pattern in temp_patterns:
        try:
            import glob
            for file_path in glob.glob(pattern):
                Path(file_path).unlink(missing_ok=True)
        except Exception:
            pass

    print_success("Cleanup completed")

def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description="RiceGuard BDD Test Runner")
    parser.add_argument("--install", action="store_true", help="Install test dependencies")
    parser.add_argument("--setup", action="store_true", help="Setup test environment")
    parser.add_argument("--feature", type=str, help="Run specific feature file (without .feature extension)")
    parser.add_argument("--tags", type=str, help="Run scenarios with specific tags")
    parser.add_argument("--skip-env-check", action="store_true", help="Skip environment check")
    parser.add_argument("--generate-reports", action="store_true", help="Generate test reports")
    parser.add_argument("--cleanup", action="store_true", help="Clean up test artifacts")

    args = parser.parse_args()

    print(f"{colors.HEADER}{colors.BOLD}RiceGuard BDD Test Runner{colors.ENDC}")
    print("=" * 50)

    try:
        # Install dependencies if requested
        if args.install:
            if not install_dependencies():
                sys.exit(1)
            print_success("Dependencies installed. Run again without --install to run tests.")
            return

        # Setup environment if requested
        if args.setup:
            if not setup_test_environment():
                sys.exit(1)
            print_success("Environment setup complete.")
            return

        # Check environment
        if not args.skip_env_check:
            if not check_environment():
                print_error("Environment check failed. Use --install to install dependencies.")
                sys.exit(1)

        # Run specific feature or all tests
        success = False
        if args.feature:
            success = run_specific_feature(args.feature, args.tags)
        else:
            success = run_all_tests(args.tags)

        # Generate reports if requested
        if args.generate_reports:
            generate_reports()

        # Cleanup if requested
        if args.cleanup:
            cleanup()

        # Print summary
        print("\n" + "=" * 50)
        if success:
            print_success("Test run completed successfully")

            # Show report locations
            print(f"\n{colors.OKCYAN}Available Reports:{colors.ENDC}")
            print(f"  - JSON Report: tests/reports/behave_report.json")
            if Path("tests/reports/allure-report/index.html").exists():
                print(f"  - Allure Report: tests/reports/allure-report/index.html")
            print(f"  - JUnit XML: tests/reports/")

            sys.exit(0)
        else:
            print_error("Test run failed")
            print(f"\n{colors.WARNING}Check logs in tests/reports/ for details{colors.ENDC}")
            sys.exit(1)

    except KeyboardInterrupt:
        print_warning("\nTest run interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()