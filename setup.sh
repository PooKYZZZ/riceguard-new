#!/bin/bash
# RiceGuard One-Click Setup for macOS and Linux
# Cross-platform setup for all team members

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${PURPLE}"
echo "====================================="
echo "  RiceGuard Automated Setup (Unix)"
echo "====================================="
echo -e "${NC}"

# Function to print colored messages
print_status() {
    echo -e "${BLUE}→${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅${NC} $1"
}

print_error() {
    echo -e "${RED}❌${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed"
    echo "Please install Python 3.8+:"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
    echo "  macOS: brew install python@3.9"
    echo "  CentOS/RHEL: sudo yum install python3 python3-pip"
    exit 1
fi

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if python3 -c 'import sys; exit(0 if sys.version_info >= (3, 8) else 1)'; then
    print_success "Python $python_version found"
else
    print_error "Python $python_version found, need 3.8+"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed"
    echo "Please install Node.js 18+:"
    echo "  Ubuntu/Debian: curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - && sudo apt install nodejs"
    echo "  macOS: brew install node"
    echo "  CentOS/RHEL: curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash - && sudo yum install nodejs"
    exit 1
fi

node_version=$(node --version)
print_success "Node.js $node_version found"

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    print_error "npm is not installed"
    exit 1
fi

npm_version=$(npm --version)
print_success "npm $npm_version found"

echo ""
print_status "System requirements check passed"
echo ""

# Check if we're in the right directory
if [ ! -f "setup.py" ]; then
    print_error "setup.py not found. Please run this script from the RiceGuard root directory."
    exit 1
fi

# Make the script executable
chmod +x setup.py
chmod +x start-dev.py
chmod +x verify-setup.py
chmod +x scripts/*.py

# Run the main setup script
print_status "Starting RiceGuard setup..."
echo ""

if python3 setup.py; then
    echo ""
    print_success "Setup completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Configure backend/.env (copy from .env.example)"
    echo "2. Download ML model to ml/model.h5"
    echo "3. Run: python3 start-dev.py"
    echo "4. Verify with: python3 verify-setup.py"
    echo ""
    echo "🚀 To start development: python3 start-dev.py"
    echo "🔍 To verify setup: python3 verify-setup.py"
    echo "📚 For troubleshooting: read TROUBLESHOOTING.md"
else
    echo ""
    print_warning "Setup completed with errors. Please check the output above."
    echo ""
    echo "Common fixes:"
    echo "1. Check internet connection"
    echo "2. Try running with sudo: sudo ./setup.sh"
    echo "3. Install build tools: sudo apt install build-essential (Ubuntu)"
    echo "4. Read TROUBLESHOOTING.md for detailed help"
    exit 1
fi

echo ""