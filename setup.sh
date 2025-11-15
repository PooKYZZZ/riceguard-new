#!/bin/bash
# =============================================================================
# RiceGuard Automated Setup Script for Linux and macOS
# =============================================================================
# This script sets up the entire RiceGuard development environment
# It safely handles dependencies, environment files, and configuration
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Print functions
print_header() {
    echo -e "${WHITE}${PURPLE}=============================================================================${NC}"
    echo -e "${WHITE}${PURPLE}                           🌾 RiceGuard Setup${NC}"
    echo -e "${WHITE}${PURPLE}=============================================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_status() {
    echo -e "${CYAN}→ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if running on a supported system
check_system() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        print_success "Linux system detected"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        print_success "macOS system detected"
    else
        print_warning "Unsupported system: $OSTYPE"
        print_info "This script is designed for Linux and macOS"
    fi
}

# Check system requirements
check_requirements() {
    print_status "Checking system requirements..."

    # Check Python
    if command -v python3 &> /dev/null; then
        python_version=$(python3 --version | cut -d' ' -f2)
        print_success "Python $python_version found"
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        python_version=$(python --version | cut -d' ' -f2)
        print_success "Python $python_version found"
        PYTHON_CMD="python"
    else
        print_error "Python is not installed or not in PATH"
        print_info "Please install Python 3.8+ from https://python.org"
        exit 1
    fi

    # Check Python version
    python_major=$($PYTHON_CMD -c "import sys; print(sys.version_info.major)")
    python_minor=$($PYTHON_CMD -c "import sys; print(sys.version_info.minor)")

    if [[ $python_major -lt 3 ]] || [[ $python_major -eq 3 && $python_minor -lt 8 ]]; then
        print_error "Python $python_major.$python_minor is too old. Requires Python 3.8+"
        exit 1
    fi

    # Check Node.js
    if command -v node &> /dev/null; then
        node_version=$(node --version)
        print_success "Node.js $node_version found"
    else
        print_error "Node.js is not installed or not in PATH"
        print_info "Please install Node.js 18+ from https://nodejs.org"
        exit 1
    fi

    # Check npm
    if command -v npm &> /dev/null; then
        npm_version=$(npm --version)
        print_success "npm $npm_version found"
    else
        print_error "npm is not installed or not in PATH"
        print_info "npm should be installed with Node.js"
        exit 1
    fi

    # Check git (optional but recommended)
    if command -v git &> /dev/null; then
        git_version=$(git --version | cut -d' ' -f3)
        print_success "Git $git_version found"
    else
        print_warning "Git not found - recommended for development"
    fi
}

# Show setup information
show_info() {
    echo
    print_header
    echo
    echo "This script will automatically set up your RiceGuard development environment."
    echo "It will install dependencies and create necessary configuration files."
    print_success "Existing files will NEVER be overwritten - your data is safe."
    echo
}

# Check if we're in the right directory
check_directory() {
    if [ ! -f "setup.py" ]; then
        print_error "setup.py not found. Please run this script from the RiceGuard root directory."
        exit 1
    fi

    # Make scripts executable
    chmod +x setup.py 2>/dev/null || true
    chmod +x start-dev.py 2>/dev/null || true
    chmod +x verify-setup.py 2>/dev/null || true
    if [ -d "scripts" ]; then
        chmod +x scripts/*.py 2>/dev/null || true
    fi
}

# Run the main setup script
run_setup() {
    echo
    print_status "Starting RiceGuard automated setup..."
    print_info "This may take a few minutes..."
    echo

    # Run the Python setup script
    if $PYTHON_CMD setup.py; then
        echo
        print_success "Setup completed successfully!"
        show_success_info
    else
        echo
        print_warning "Setup completed with some issues"
        show_troubleshooting_info
        exit 1
    fi
}

# Show success information
show_success_info() {
    echo
    print_header
    print_success "🎉 Setup Completed Successfully!"
    echo
    echo "Your RiceGuard development environment is ready!"
    echo
    echo "Next steps:"
    echo "  1. Configure environment files (if not done):"
    echo "     - Edit backend/.env with your MongoDB Atlas credentials"
    echo "     - Get free cluster from: https://www.mongodb.com/cloud/atlas"
    echo
    echo "  2. Start development servers:"
    echo "     python start-dev.py"
    echo
    echo "  3. Open your browser:"
    echo "     - Frontend: http://localhost:3000"
    echo "     - API Docs: http://127.0.0.1:8000/docs"
    echo
    echo "  4. Verify setup (optional):"
    echo "     python verify-setup.py"
    echo
    echo "Need help? Check CLAUDE.md for documentation"
    echo
}

# Show troubleshooting information
show_troubleshooting_info() {
    echo
    print_header
    print_warning "⚠️  Setup Completed with Issues"
    echo
    echo "Some setup steps encountered problems. Please review the output above."
    echo
    echo "Common solutions:"
    echo "  1. If dependencies failed to install, try running the setup again"
    echo "  2. If permissions are required, try with sudo:"
    echo "     sudo $0"
    echo "  3. If network issues occurred, check your internet connection"
    echo "  4. Install build tools (Ubuntu/Debian): sudo apt install build-essential"
    echo
    echo "Manual setup steps:"
    echo "  1. Copy environment files:"
    echo "     cp backend/.env.example backend/.env"
    echo "     cp frontend/.env.example frontend/.env"
    echo
    echo "  2. Edit backend/.env with your MongoDB Atlas credentials"
    echo "     - Get free cluster from: https://www.mongodb.com/cloud/atlas"
    echo "     - Generate JWT secret: openssl rand -hex 32"
    echo
    echo "  3. Start development:"
    echo "     python start-dev.py"
    echo
}

# Main execution
main() {
    # Trap Ctrl+C and exit gracefully
    trap 'echo -e "\n${YELLOW}Setup interrupted by user${NC}"; exit 1' INT

    show_info
    check_system
    check_requirements
    check_directory
    run_setup
}

# Run main function
main "$@"