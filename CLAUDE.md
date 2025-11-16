# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RiceGuard is a multi-platform rice leaf disease detection system developed by Team 27 for an academic capstone project (CPE025 Software Design, CPE026 Emerging Technologies 3). This is a **school project for educational purposes** with basic security implementation suitable for academic demonstration, not production deployment.

**Project Context:**
- **Academic Project**: Capstone demonstration for university courses
- **Educational Focus**: Learning TDD/BDD practices, full-stack development, ML integration
- **Security Level**: Basic implementation suitable for school environment (NOT production-ready)
- **Scope**: Demonstrate working disease detection system with proper development practices

**Disease Classification Classes:**
- bacterial_leaf_blight
- brown_spot
- healthy
- leaf_blast
- leaf_scald
- narrow_brown_spot

**Core Architecture:**
- Backend: FastAPI with MongoDB Atlas for user management, scan history, and ML predictions
- Frontend: React SPA with JWT authentication and file upload capabilities
- ML Pipeline: TensorFlow model (src/ml/model.h5, 128MB) with temperature scaling calibration
- Mobile: React Native (Expo) with TensorFlow Lite for on-device inference
- Database: MongoDB Atlas with comprehensive indexing and query optimization

## Current Project Status

### ✅ **Working Components**
- **Backend**: Functional FastAPI with ML integration and basic security
- **Frontend**: React application with authentication and file upload
- **Mobile**: React Native app with camera integration
- **ML Pipeline**: TensorFlow model with confidence calibration
- **Setup Scripts**: Automated development environment setup

### ⚠️ **Known Limitations (School Project Context)**
- **Security**: Basic implementation suitable for educational environment only
- **Testing**: TDD/BDD framework implemented for learning purposes
- **Performance**: Optimized for development/demo, not production scale
- **Error Handling**: Basic implementation for academic demonstration
- **Mobile Features**: Core functionality implemented for project requirements

## Architecture & Structure

### Current Directory Layout
The project uses a simplified root structure with `src/` directory for all application code:

```
riceguard/
├── setup.py              # Automated project setup (cross-platform)
├── start.py              # Development server manager
├── README.md             # Quick start guide
├── CLAUDE.md             # This file
├── src/                  # All application code
│   ├── backend/          # FastAPI + MongoDB + TensorFlow
│   ├── frontend/         # React web app with JWT auth
│   ├── mobileapp/        # React Native (Expo) mobile app
│   ├── ml/               # TensorFlow model and labels
│   ├── docs/             # Documentation files
│   ├── scripts/          # Utility scripts
│   ├── tools/            # Development tools
│   └── setup/            # Setup configurations
└── .gitignore
```

### Technology Stack
- **Backend**: FastAPI, MongoDB Atlas, TensorFlow 2.20.0, JWT auth
- **Frontend**: React 19.2.0, React Router, React Testing Library
- **Mobile**: React Native 0.81.4, Expo 54, React Navigation 7
- **ML**: TensorFlow with temperature scaling, confidence calibration
- **Security**: Rate limiting, CORS, bcrypt, httpOnly cookies

## Essential Commands

### Setup (Run once)
```bash
python setup.py                    # Cross-platform automated setup
# OR use platform-specific scripts:
setup/setup.bat                    # Windows
./setup/setup.sh                  # macOS/Linux

# Verify setup completeness
python src/tools/verify-setup.py  # Check configuration
```

### Development
```bash
# Start all services (recommended for daily development)
python start.py                    # Backend + Frontend + Mobile
python start.py --backend-only     # Backend only (port 8000)
python start.py --frontend-only    # Frontend only (port 3000)
python start.py --mobile-only      # Mobile only (Expo)
python start.py --no-mobile        # Skip mobile server

# Individual service management
cd src/backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000
cd src/frontend && npm start
cd src/mobileapp/riceguard && npx expo start --lan

# Development verification
python src/tools/verify-setup.py  # Check complete development environment
```

### Testing Commands

#### **Backend Testing (TDD Framework)**
```bash
cd src/backend

# Comprehensive test runner (recommended)
python tests/run_tests.py fast          # Fast unit tests only
python tests/run_tests.py all           # Full test suite (integration + slow)
python tests/run_tests.py security      # Security-focused validation
python tests/run_tests.py performance   # Performance benchmarks
python tests/run_tests.py ml           # ML service testing
python tests/run_tests.py api          # API endpoint validation
python tests/run_tests.py coverage     # Detailed coverage reports

# Direct pytest commands
python -m pytest tests/                                    # Run all tests
python -m pytest tests/ -m unit                           # Unit tests only
python -m pytest tests/ -m integration                    # Integration tests
python -m pytest tests/ -m security                       # Security tests
python -m pytest tests/ -m performance                    # Performance tests
python -m pytest tests/ --cov=../ --cov-report=html       # HTML coverage
python -m pytest tests/ --cov=../ --cov-report=xml        # XML coverage for CI
```

#### **BDD Testing (Behave Framework)**
```bash
# BDD test execution
python tests/run_bdd_tests.py                           # Run all BDD scenarios
python tests/run_bdd_tests.py --feature user_authentication # Specific feature
python tests/run_bdd_tests.py --feature disease_detection  # Disease detection
python tests/run_bdd_tests.py --tags @security          # Security scenarios
python tests/run_bdd_tests.py --tags @performance       # Performance scenarios
python tests/run_bdd_tests.py --generate-reports       # Generate Allure reports
python tests/run_bdd_tests.py --install                # Install BDD dependencies
python tests/run_bdd_tests.py --setup                  # Setup test environment
```

#### **Frontend Testing**
```bash
cd src/frontend
npm test                                    # Run tests in watch mode
npm test -- --coverage                      # Generate coverage report
npm test -- --watchAll=false               # CI mode (single run)
npm test -- --testPathPattern=Login        # Test specific components
npm test -- --testPathPattern=Scan         # Test scanning functionality
npm test -- --coverage --watchAll=false    # Coverage in CI mode
```

#### **Mobile Testing**
```bash
cd src/mobileapp/riceguard
npm test                                      # Run mobile tests
npm test -- --coverage                       # Coverage with 80% threshold
npm test -- --watchAll=false                 # CI mode
npm test -- --testPathPattern=LoginScreen    # Test specific screens
npm test -- --coverage --watchAll=false      # Coverage for CI
```

#### **Test Report Generation**
```bash
# Unified test reporting
python scripts/generate-test-report.py             # Generate comprehensive report
python scripts/generate-test-report.py --project-root /path/to/riceguard

# Individual platform coverage
# Backend: src/backend/htmlcov/index.html
# Frontend: src/frontend/coverage/lcov-report/index.html
# Mobile: src/mobileapp/riceguard/coverage/lcov-report/index.html
# BDD: tests/reports/allure-report/index.html
```

#### **Development Health Checks**
```bash
# Backend health and API documentation
curl http://127.0.0.1:8000/health    # Backend health check
curl http://127.0.0.1:8000/docs      # Interactive API documentation
curl http://127.0.0.1:8000/redoc     # Alternative API docs

# Frontend development server
curl http://localhost:3000           # Frontend accessibility
```

## Critical Configuration

### Environment Files Required
**Backend (src/backend/.env)**:
```env
# Database
MONGO_URI=mongodb+srv://<user>:<pass>@<cluster>.mongodb.net/riceguard_db
DB_NAME=riceguard_db

# Security
JWT_SECRET=<generate_strong_random_string_32+chars>
JWT_ALGORITHM=HS256
TOKEN_EXPIRE_HOURS=6

# File Upload
UPLOAD_DIR=uploads
MAX_UPLOAD_MB=8

# ML Configuration
CONFIDENCE_THRESHOLD=0.45
CONFIDENCE_MARGIN=0.12
TEMPERATURE=1.25
IMG_SIZE=224

# CORS (comma-separated origins)
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173
```

**Frontend (src/frontend/.env)**:
```env
REACT_APP_API_URL=http://127.0.0.1:8000/api/v1
```

### Mobile Configuration
```bash
# Required environment variables for mobile development
export EXPO_PUBLIC_API_BASE_URL=http://<PC_IP>:8000/api/v1
export REACT_NATIVE_PACKAGER_HOSTNAME=<PC_IP>

# For Windows (Command Prompt)
set EXPO_PUBLIC_API_BASE_URL=http://<PC_IP>:8000/api/v1
set REACT_NATIVE_PACKAGER_HOSTNAME=<PC_IP>

# Get PC IP address (for LAN connectivity)
ipconfig    # Windows
ifconfig    # macOS/Linux
```

## Mobile Development Configuration

### **Mobile Technology Stack**
- **Framework**: React Native 0.81.4 with Expo 54 SDK
- **Navigation**: React Navigation 7 with native stack navigation
- **Testing**: Jest with React Native Testing Library
- **ML Integration**: TensorFlow Lite for on-device inference
- **Camera Integration**: Expo Image Picker for photo capture
- **Font System**: Expo Fonts with Google Fonts (Nunito)

### **Mobile Development Setup**

#### **Prerequisites**
```bash
# Node.js and npm required (automatically installed by main setup)
node --version    # Should be 16.x or higher
npm --version     # Should be 8.x or higher

# Expo CLI (global installation)
npm install -g @expo/cli
```

#### **Mobile Environment Configuration**
**Critical Step**: IP configuration for device connectivity

```bash
# 1. Find your PC's LAN IP address
# Windows:
ipconfig | findstr "IPv4"
# macOS/Linux:
ifconfig | grep "inet " | grep -v 127.0.0.1

# 2. Set environment variables with your PC IP
# Replace 192.168.1.100 with your actual IP address

# Linux/macOS:
export EXPO_PUBLIC_API_BASE_URL=http://192.168.1.100:8000/api/v1
export REACT_NATIVE_PACKAGER_HOSTNAME=192.168.1.100

# Windows Command Prompt:
set EXPO_PUBLIC_API_BASE_URL=http://192.168.1.100:8000/api/v1
set REACT_NATIVE_PACKAGER_HOSTNAME=192.168.1.100

# Windows PowerShell:
$env:EXPO_PUBLIC_API_BASE_URL="http://192.168.1.100:8000/api/v1"
$env:REACT_NATIVE_PACKAGER_HOSTNAME="192.168.1.100"
```

#### **Mobile Development Workflow**
```bash
# Navigate to mobile app directory
cd src/mobileapp/riceguard

# Install mobile dependencies (one-time)
npm install

# Start mobile development server
npx expo start                    # Start with QR code
npx expo start --lan             # Force LAN mode
npx expo start --clear           # Clear cache and start
npx expo start --web             # Web version for testing

# Testing workflow
npm test                          # Run Jest tests
npm test -- --coverage           # With coverage report
npm test -- --watchAll=false     # CI mode (single run)

# Production build
npx expo build:android           # Android APK/AAB
npx expo build:ios              # iOS IPA (requires Apple Developer account)
```

### **Mobile Testing Configuration**

#### **Jest Configuration** (`package.json`)
- **Coverage Thresholds**: 80% minimum for branches, functions, lines, statements
- **Test Environment**: React Native preset with Expo support
- **Test Patterns**: `**/__tests__/**/*.test.js` and `**/*.(test|spec).js`
- **Transform Ignore Patterns**: Handles React Native and Expo modules

#### **Mobile Test Categories**
```bash
# Component testing
npm test -- --testPathPattern=components   # Test UI components
npm test -- --testPathPattern=screens      # Test screen components

# Integration testing
npm test -- --testPathPattern=navigation   # Test navigation flows
npm test -- --testPathPattern=api          # Test API integration

# Device-specific testing
npm test -- --testPathPattern=camera       # Test camera integration
npm test -- --testPathPattern=ml           # Test ML inference
```

### **Device Testing & Deployment**

#### **Physical Device Testing**
1. **Install Expo Go**: Download from App Store (iOS) or Google Play Store (Android)
2. **Connect to WiFi**: Ensure device and PC are on same network
3. **Scan QR Code**: Use Expo Go app to scan QR code from terminal
4. **Test Features**: Camera integration, ML inference, API connectivity

#### **Simulator/Emulator Testing**
```bash
# Start specific platforms
npx expo start --ios              # iOS Simulator (macOS only)
npx expo start --android          # Android Emulator
npx expo start --web              # Web browser testing

# Platform-specific builds
npx expo run:ios                  # Run on iOS Simulator
npx expo run:android              # Run on Android Emulator
```

#### **Production Deployment**
```bash
# Build for app stores (requires Expo account)
npx expo build:android --type apk    # Android APK for testing
npx expo build:android --type app-bundle # Android App Bundle for Play Store
npx expo build:ios                  # iOS build for App Store (requires Apple Developer)

# Development builds
npx expo install --fix              # Fix dependency issues
npx expo doctor                     # Check for common issues
```

### **Mobile Development Troubleshooting**

#### **Common Issues & Solutions**
1. **Metro Bundler Issues**: Clear cache with `npx expo start --clear`
2. **Network Connectivity**: Verify PC IP and firewall settings
3. **Dependencies**: Run `npx expo install --fix` to resolve version conflicts
4. **Camera Permissions**: Enable camera access in device settings
5. **ML Model Issues**: Ensure TensorFlow Lite model is properly bundled

#### **Development Tools**
```bash
# Debugging tools
npx expo start --dev-client         # Use Expo Development Client
npx expo start --tunnel             # Tunnel through Expo servers
npx expo install @expo/metro-config  # Advanced Metro configuration

# Performance monitoring
npx expo start --performance-monitor   # Enable performance monitoring
```

### **Mobile App Architecture**
- **Screen-Based Navigation**: LoginScreen, ScanScreen, HistoryScreen
- **State Management**: React Context for authentication and app state
- **API Integration**: HTTP client for backend communication
- **File Handling**: Image processing and upload utilities
- **ML Integration**: TensorFlow Lite inference engine
- **Offline Support**: Local storage for scan history and settings

**⚠️ Mobile Development Note**: Mobile app requires backend server running on accessible IP address. Ensure backend is started with `python start.py --backend-only` and device can reach the PC's IP address on port 8000.

## ML Model Requirements
- **Critical**: `src/ml/model.h5` (128MB TensorFlow model) - NOT in Git repo
- Must be obtained separately from team distribution
- Disease classes: bacterial_leaf_blight, brown_spot, healthy, leaf_blast, leaf_scald, narrow_brown_spot

## Key Architecture Patterns

### Security Architecture (Basic School Project Level)
- **Authentication**: JWT implementation for academic demonstration
- **Input Validation**: Basic Pydantic validation for educational purposes
- **File Security**: Simple validation for project requirements
- **Rate Limiting**: Basic implementation for demo stability
- **CORS**: Development-friendly configuration

**⚠️ Security Note**: This is a school project with basic security implementation. NOT suitable for production deployment or external user access.

### ML Integration
- **Singleton Pattern**: Memory-efficient model loading
- **Temperature Scaling**: Configurable confidence calibration
- **Multi-criteria Decisions**: Confidence thresholds, entropy analysis
- **Debug Endpoints**: `/api/v1/debug/predict-sample`, `/api/v1/debug/config`

### Database Optimization
- **MongoDB Atlas**: Free tier with strategic indexes
- **Connection Pooling**: Efficient database connections
- **Pagination**: 100-item limits for performance
- **Indexing**: users.email, scans.userId, recommendations.diseaseKey

## Configuration Files & Quality Standards

### **Key Configuration Files**

#### **Backend Configuration**
- **`src/backend/requirements.txt`**: Python dependencies with version pinning
- **`src/backend/.env`**: Runtime configuration (database, JWT, ML parameters)
- **`src/backend/tests/pytest.ini`**: pytest configuration with markers and coverage
- **`src/backend/tests/conftest.py`**: Test fixtures and database setup

#### **Frontend Configuration**
- **`src/frontend/package.json`**: Node.js dependencies and scripts
- **`src/frontend/.env`**: API endpoint configuration
- **`src/frontend/.gitignore`**: Node.js exclusions and build artifacts

#### **Mobile Configuration**
- **`src/mobileapp/riceguard/package.json`**: React Native dependencies with Jest config
- **`src/mobileapp/riceguard/app.json`**: Expo app configuration
- **`src/mobileapp/riceguard/jest.setup.js`**: Jest testing environment setup

#### **BDD Configuration**
- **`tests/behave.ini`**: Behave framework configuration and formatters
- **`tests/requirements.txt`**: BDD testing dependencies (behave, allure, selenium)
- **`tests/features/`**: Gherkin feature files for behavior testing
- **`tests/steps/`**: Step definition implementations

#### **Development Configuration**
- **`setup.py`**: Cross-platform development environment setup
- **`start.py`**: Development server manager with service orchestration
- **`.gitignore`**: Version control exclusions for all platforms

### **Quality Gates & Coverage Standards**

#### **Automated Quality Thresholds**
| Platform | Coverage Requirement | Test Types | Quality Gates |
|----------|---------------------|------------|---------------|
| **Backend** | 90% minimum coverage | Unit, Integration, Security, ML, API | All tests must pass, coverage threshold met |
| **Frontend** | 80% minimum coverage | Component, Integration, E2E | Component validation required |
| **Mobile** | 80% all metrics | Component, Screen, Navigation, Device | Branches, functions, lines, statements |
| **BDD** | 100% scenario pass rate | User journeys, workflows | Critical paths must pass |

#### **Coverage Report Formats**
```bash
# Backend Coverage (pytest-cov)
src/backend/htmlcov/index.html          # Interactive HTML report
src/backend/coverage.xml                # XML for CI/CD integration
src/backend/coverage.json               # JSON for analysis

# Frontend Coverage (Jest)
src/frontend/coverage/lcov-report/index.html    # HTML with lcov format
src/frontend/coverage/coverage-final.json       # JSON summary

# Mobile Coverage (Jest)
src/mobileapp/riceguard/coverage/lcov-report/index.html  # HTML report
src/mobileapp/riceguard/coverage/coverage-final.json     # JSON summary

# BDD Reports (Allure + Behave)
tests/reports/allure-report/index.html    # Interactive Allure report
tests/reports/behave_report.json          # JSON for CI integration
tests/reports/junit/                      # JUnit XML files
```

#### **Test Categorization System**

**Backend Test Markers** (`src/backend/tests/pytest.ini`):
```ini
[tool:pytest]
markers =
    unit: Fast isolated tests (no external dependencies)
    integration: Database and external service integration
    security: Authentication, authorization, input validation
    performance: Load testing and response time validation
    ml: Machine learning pipeline and model testing
    api: RESTful API endpoint validation
    slow: Tests requiring >5 seconds execution time
```

**BDD Tags** (`tests/features/`):
- `@authentication`: User registration, login, session management
- `@disease-detection`: ML inference, image processing, confidence scoring
- `@security`: Rate limiting, input validation, file security
- `@performance`: Response times, load handling, resource usage
- `@privacy`: Data protection, GDPR compliance, user consent

#### **Continuous Integration Quality Gates**
```yaml
# Example CI Pipeline Quality Gates
quality_gates:
  backend_tests:
    command: "python src/backend/tests/run_tests.py all"
    coverage_threshold: 90
    fail_threshold: 0  # Zero tolerance for test failures

  frontend_tests:
    command: "cd src/frontend && npm test -- --coverage --watchAll=false"
    coverage_threshold: 80
    fail_threshold: 0

  mobile_tests:
    command: "cd src/mobileapp/riceguard && npm test -- --coverage --watchAll=false"
    coverage_threshold: 80
    fail_threshold: 0

  bdd_tests:
    command: "python tests/run_bdd_tests.py"
    scenario_pass_rate: 100
    fail_threshold: 0
```

### **Development Standards & Patterns**

#### **Code Quality Standards**
- **Backend**: PEP 8 compliance, type hints, docstrings for all functions
- **Frontend**: ESLint configuration, React best practices, component documentation
- **Mobile**: React Native conventions, TypeScript where applicable
- **Testing**: Descriptive test names, AAA pattern (Arrange-Act-Assert)

#### **Security Standards**
- **Input Validation**: All user inputs validated using Pydantic models
- **Authentication**: JWT tokens with expiration and refresh mechanisms
- **Rate Limiting**: Configurable rate limits per endpoint
- **File Security**: Size limits, type validation, malware scanning
- **Data Protection**: Encrypted sensitive data, secure password hashing

#### **Performance Standards**
- **API Response Times**: <200ms for simple endpoints, <500ms for complex operations
- **Database Queries**: Optimized with proper indexing, query analysis
- **Mobile Performance**: <3s app startup time, smooth animations
- **Frontend Performance**: <2s initial load, lazy loading for heavy components

### **Configuration Templates**

#### **Backend Environment Template** (`src/backend/.env.example`)
```env
# Database Configuration
MONGO_URI=mongodb+srv://<user>:<pass>@<cluster>.mongodb.net/riceguard_db
DB_NAME=riceguard_db

# Security Configuration
JWT_SECRET=<generate_32_char_random_string>
JWT_ALGORITHM=HS256
TOKEN_EXPIRE_HOURS=6

# File Upload Configuration
UPLOAD_DIR=uploads
MAX_UPLOAD_MB=8
ALLOWED_EXTENSIONS=jpg,jpeg,png

# ML Model Configuration
MODEL_PATH=../ml/model.h5
CONFIDENCE_THRESHOLD=0.45
CONFIDENCE_MARGIN=0.12
TEMPERATURE=1.25
IMG_SIZE=224

# CORS Configuration
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Development Settings
DEBUG=true
LOG_LEVEL=INFO
```

#### **Testing Environment Configuration**
```bash
# Automated test environment setup
export TESTING=true
export MONGO_URI=mongodb://localhost:27017/test_riceguard
export DB_NAME=test_riceguard
export JWT_SECRET=test_jwt_secret_key_for_testing_only
export UPLOAD_DIR=/tmp/test_uploads
export MAX_UPLOAD_MB=2
export MODEL_PATH=/tmp/test_model.h5
```

### **Development Tool Configuration**

#### **Pre-commit Hooks** (`.git/hooks/pre-commit`)
```bash
#!/bin/bash
# Pre-commit quality checks

echo "Running pre-commit quality checks..."

# Backend linting and testing
cd src/backend
python -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
python -m pytest tests/ -x -v

# Frontend linting and testing
cd ../frontend
npm run lint 2>/dev/null || npx eslint src/
npm test -- --watchAll=false --passWithNoTests

# Mobile testing
cd ../mobileapp/riceguard
npm test -- --watchAll=false --passWithNoTests

echo "All pre-commit checks passed!"
```

#### **IDE Configuration** (`.vscode/settings.json`)
```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "files.exclude": {
    "**/__pycache__": true,
    "**/node_modules": true,
    "**/coverage": true,
    "**/htmlcov": true
  }
}
```

**⚠️ Quality Standards Note**: These configurations represent comprehensive educational development standards. In a production environment, additional security, performance, and compliance measures would be required.

## Testing Framework (Comprehensive Educational TDD/BDD System)

### Architecture Overview
RiceGuard implements a **dual-framework testing approach** designed for educational development practices:
- **TDD Framework**: pytest-based unit and integration testing with comprehensive coverage
- **BDD Framework**: Behave-based behavior testing with Gherkin scenarios and Allure reporting
- **Quality Gates**: Automated coverage thresholds and test success criteria
- **Cross-Platform**: Backend, frontend, and mobile testing with unified reporting

### Backend TDD Testing (pytest Framework)

#### **Test Runner System**
**Main Test Runner**: `src/backend/tests/run_tests.py` with multiple test modes:

```bash
cd src/backend
python tests/run_tests.py fast          # Fast unit tests only (80% coverage threshold)
python tests/run_tests.py all           # All tests including integration and slow (90% threshold)
python tests/run_tests.py security      # Security-focused tests (auth, input validation, rate limiting)
python tests/run_tests.py performance   # Performance and load testing
python tests/run_tests.py ml           # ML service testing (model loading, inference, calibration)
python tests/run_tests.py api          # API endpoint comprehensive testing
python tests/run_tests.py coverage     # Generate detailed HTML/XML/annotated coverage reports
```

#### **Direct pytest Commands**
```bash
cd src/backend
python -m pytest tests/                                    # Run all tests
python -m pytest tests/ -m unit                           # Unit tests only
python -m pytest tests/ -m integration                    # Integration tests with database
python -m pytest tests/ -m security                       # Security test suite
python -m pytest tests/ -m performance                    # Performance benchmarks
python -m pytest tests/ -m ml                             # ML service validation
python -m pytest tests/ -m api                            # API endpoint testing
python -m pytest tests/ --cov=../ --cov-report=html       # HTML coverage report
python -m pytest tests/ --cov=../ --cov-report=xml        # XML coverage for CI
```

#### **Test Categories & Markers**
- **`@unit`**: Fast isolated tests (no external dependencies)
- **`@integration`**: Database and external service integration
- **`@security`**: Authentication, authorization, input validation
- **`@@performance`**: Load testing and response time validation
- **`@ml`**: Machine learning pipeline and model testing
- **`@api`**: RESTful API endpoint validation
- **`@slow`**: Tests requiring >5 seconds execution time

#### **Coverage Requirements**
- **Minimum Coverage**: 90% for full test suite, 80% for fast tests
- **Report Formats**: HTML (interactive), XML (CI), terminal (immediate feedback)
- **Coverage Reports**: Generated in `src/backend/htmlcov/` directory
- **Quality Gates**: Tests fail if coverage thresholds not met

#### **Test Dependencies**
```bash
# Core testing stack
pytest==8.3.3, pytest-asyncio==0.24.0, pytest-cov==6.0.0, pytest-mock==3.14.0

# Test utilities
mongomock==4.2.0, factory-boy==3.3.1, faker==30.8.1, freezegun==1.5.1, httpx==0.28.1
```

### BDD Testing Framework (Behave System)

#### **BDD Test Runner**
**Main BDD Runner**: `tests/run_bdd_tests.py` with comprehensive reporting:

```bash
python tests/run_bdd_tests.py                           # Run all BDD scenarios
python tests/run_bdd_tests.py --feature user_authentication # Run specific feature
python tests/run_bdd_tests.py --feature disease_detection  # Disease detection workflows
python tests/run_bdd_tests.py --tags @security          # Security-related scenarios
python tests/run_bdd_tests.py --tags @performance       # Performance validation
python tests/run_bdd_tests.py --generate-reports       # Generate Allure HTML reports
python tests/run_bdd_tests.py --cleanup               # Clean test artifacts
```

#### **BDD Feature Files (Gherkin Scenarios)**
**Location**: `tests/features/`

1. **`user_authentication.feature`**: Complete user auth workflows (11 scenarios)
   - User registration with email validation
   - Login with JWT token generation
   - Password reset and change flows
   - Account lockout after failed attempts
   - Session management and logout

2. **`disease_detection.feature`**: ML-powered disease detection workflows
   - Image upload and validation
   - ML model inference with confidence scoring
   - Multi-criteria disease classification
   - Result confidence calibration
   - Edge case handling (blurry images, invalid formats)

3. **`scan_history.feature`**: User scan data management
   - Historical scan storage and retrieval
   - Pagination and filtering of scan history
   - Data export functionality (JSON, CSV)
   - Privacy controls and data retention

4. **`security_and_privacy.feature`**: Security validation scenarios
   - Rate limiting enforcement
   - Input sanitization and XSS prevention
   - File upload security (size limits, type validation)
   - Data encryption at rest and in transit
   - GDPR compliance checks

5. **`performance_and_scalability.feature`**: System performance validation
   - API response time benchmarks
   - Concurrent user handling
   - Memory usage monitoring
   - Database query optimization
   - Mobile app performance under load

#### **BDD Configuration**
**Configuration File**: `tests/behave.ini`
- **Output Formats**: Pretty console output, JSON for CI, Allure for HTML reports
- **JUnit Integration**: XML output for test management systems
- **Step Definitions**: Python implementation files in `tests/steps/`
- **Environment Setup**: Test database and service configuration

#### **BDD Reporting**
```bash
# Generate comprehensive HTML report
python tests/run_bdd_tests.py --generate-reports

# Report locations
tests/reports/behave_report.json          # JSON report for CI
tests/reports/allure-report/index.html    # Interactive Allure HTML report
tests/reports/junit/                      # JUnit XML files
```

### Frontend Testing (React Testing Library)

#### **Frontend Test Commands**
```bash
cd src/frontend
npm test                                    # Run tests in watch mode
npm test -- --coverage                      # Generate coverage report
npm test -- --watchAll=false               # CI mode (single run)
npm test -- --testPathPattern=Login        # Test specific components
npm test -- --testPathPattern=Scan         # Test scanning functionality
```

#### **Frontend Test Coverage**
- **Framework**: React Testing Library with Jest
- **Coverage Reports**: HTML and JSON formats in `src/frontend/coverage/`
- **Component Testing**: User interaction simulation and UI validation
- **Integration Testing**: API integration and authentication flows

### Mobile Testing (React Native + Jest)

#### **Mobile Test Commands**
```bash
cd src/mobileapp/riceguard
npm test                                      # Run mobile tests
npm test -- --coverage                       # Coverage report with 80% threshold
npm test -- --watchAll=false                 # CI mode for automated testing
npm test -- --testPathPattern=LoginScreen    # Test specific screens
```

#### **Mobile Testing Configuration**
- **Jest Preset**: React Native with coverage thresholds
- **Coverage Requirements**: 80% minimum for branches, functions, lines, statements
- **Test Environment**: Expo Go compatibility testing
- **Device Testing**: Camera integration and ML on-device inference

### Test Report Generation

#### **Comprehensive Test Reports**
**Report Generator**: `scripts/generate-test-report.py`

```bash
python scripts/generate-test-report.py             # Generate unified test report
python scripts/generate-test-report.py --project-root /path/to/riceguard
```

**Report Features**:
- **Unified Dashboard**: Backend TDD, BDD, frontend, and mobile test results
- **Coverage Analysis**: Cross-platform coverage trends and gaps
- **Performance Metrics**: Test execution time and system resource usage
- **Trend Analysis**: Historical test performance and quality evolution
- **HTML Export**: Interactive reports for stakeholder review

### Quality Gates & Standards

#### **Automated Quality Thresholds**
- **Backend Tests**: 90% coverage minimum, all tests must pass
- **Frontend Tests**: 80% coverage minimum, component validation required
- **Mobile Tests**: 80% coverage across all metrics
- **BDD Scenarios**: 100% pass rate for critical user journeys
- **Security Tests**: Zero tolerance for security test failures
- **Performance Tests**: Response time benchmarks must be met

#### **Continuous Integration Requirements**
- **Pre-commit Hooks**: Automated linting and basic test validation
- **Pull Request Validation**: Full test suite execution with coverage checks
- **Merge Gates**: All quality thresholds must be met before merging
- **Deploy Validation**: End-to-end testing in staging environment

**⚠️ Educational Context**: This comprehensive testing framework is designed for learning TDD/BDD practices in an academic environment. Tests demonstrate proper development methodologies rather than production-level exhaustive validation.

## Development Access Points
- **Web Frontend**: http://localhost:3000
- **Backend API**: http://127.0.1.8000
- **API Documentation**: http://127.0.0.1:8000/docs
- **Health Check**: http://127.0.0.1:8000/health
- **Mobile**: Expo Go QR code (when mobile server running)

## Development Workflow & Best Practices

### **Getting Started (For New Development Sessions)**

#### **Environment Verification**
```bash
# 1. Verify complete development environment
python src/tools/verify-setup.py

# 2. Check critical configuration files
ls src/backend/.env                    # Should exist with MongoDB credentials
ls src/frontend/.env                   # Should exist with API URL
ls src/ml/model.h5                     # Critical: 128MB ML model (not in Git)

# 3. Start development services
python start.py                        # Recommended: Start all services
python start.py --backend-only         # Backend development only
python start.py --frontend-only        # Frontend development only
```

#### **Health Checks & Service Validation**
```bash
# Backend health verification
curl http://127.0.0.1:8000/health      # Service health status
curl http://127.0.0.1:8000/docs        # Interactive API documentation
curl http://127.0.0.1:8000/redoc       # Alternative API documentation

# Frontend accessibility
curl http://localhost:3000             # Frontend service check

# Mobile QR code verification (if mobile running)
# Scan QR code in terminal with Expo Go app
```

### **Testing-First Development Patterns**

#### **TDD Development Workflow**
```bash
# 1. Write failing test first
cd src/backend
# Create test file in tests/ directory
# Example: tests/test_new_feature.py

# 2. Run test to confirm failure
python -m pytest tests/test_new_feature.py -v

# 3. Implement minimal code to pass test
# Edit source code in main application files

# 4. Run test to confirm pass
python -m pytest tests/test_new_feature.py -v

# 5. Refactor and improve code
# Repeat test execution to ensure no regression

# 6. Run full test suite
python tests/run_tests.py all
```

#### **BDD Development Workflow**
```bash
# 1. Define behavior scenarios
# Edit/create feature files in tests/features/
# Example: tests/features/new_workflow.feature

# 2. Run BDD to see undefined steps
python tests/run_bdd_tests.py --feature new_workflow

# 3. Implement step definitions
# Create/update step implementations in tests/steps/

# 4. Run BDD again to validate scenarios
python tests/run_bdd_tests.py --feature new_workflow

# 5. Generate reports for stakeholder review
python tests/run_bdd_tests.py --feature new_workflow --generate-reports
```

### **Common Development Tasks**

#### **Backend Development**
```bash
# API endpoint development
# Location: src/backend/routers.py
# Add new endpoints, update Pydantic models in src/backend/models.py

# Database operations
# Update models in src/backend/models.py
# Database operations in src/backend/db.py
# Add database indexes in src/backend/settings.py

# ML service updates
# Model configuration in src/backend/ml_service.py
# Update ML parameters in .env file
# Calibrate confidence thresholds via debug endpoints

# Security implementation
# Authentication in src/backend/security.py
# Rate limiting in src/backend/rate_limiter.py
# Input validation via Pydantic models
```

#### **Frontend Development**
```bash
# Component development
# Location: src/frontend/src/components/
# Follow React functional component patterns with hooks

# Screen implementation
# Location: src/frontend/src/pages/
# Implement responsive design with CSS modules

# API integration
# Location: src/frontend/src/api.js
# Add new API endpoints, update error handling

# State management
# Use React Context for global state
# Local state with useState, effects with useEffect
```

#### **Mobile Development**
```bash
# Screen development
# Location: src/mobileapp/riceguard/src/screens/
# Follow React Native screen patterns

# Navigation setup
# Location: src/mobileapp/riceguard/src/navigation/
# Update screen routing and navigation flows

# Component development
# Location: src/mobileapp/riceguard/src/components/
# Create reusable React Native components

# Device integration
# Camera: Expo Image Picker integration
# ML: TensorFlow Lite on-device inference
# Storage: AsyncStorage for local data
```

### **Development Troubleshooting Guide**

#### **Common Issues & Solutions**

**Backend Issues**:
```bash
# Problem: Backend won't start
# Solution: Check virtual environment and dependencies
cd src/backend
python -m venv .venv              # Create virtual environment
source .venv/bin/activate         # macOS/Linux
.venv\Scripts\activate            # Windows
pip install -r requirements.txt   # Install dependencies

# Problem: Database connection issues
# Solution: Verify MongoDB Atlas configuration
# Check .env file for correct MONGO_URI
# Verify network connectivity to MongoDB Atlas

# Problem: ML model not loading
# Solution: Verify model file exists and permissions
ls -la src/ml/model.h5            # Should be 128MB file
# Ensure model file is readable by application
```

**Frontend Issues**:
```bash
# Problem: Frontend build failures
# Solution: Clear dependencies and reinstall
cd src/frontend
rm -rf node_modules package-lock.json
npm install                        # Fresh dependency install

# Problem: API connectivity issues
# Solution: Verify backend is running and CORS configuration
curl http://127.0.0.1:8000/health  # Test backend connectivity
# Check ALLOWED_ORIGINS in backend .env file
```

**Mobile Issues**:
```bash
# Problem: Metro bundler issues
# Solution: Clear Metro cache
cd src/mobileapp/riceguard
npx expo start --clear            # Start with cleared cache

# Problem: Network connectivity issues
# Solution: Verify IP configuration and firewall
ping <PC_IP>                      # Test network connectivity
# Check EXPO_PUBLIC_API_BASE_URL environment variable

# Problem: Build failures
# Solution: Fix dependency versions
npx expo install --fix            # Fix version conflicts
npx expo doctor                   # Check for common issues
```

**Testing Issues**:
```bash
# Problem: Test failures due to environment
# Solution: Set up test environment
export TESTING=true
export MONGO_URI=mongodb://localhost:27017/test_riceguard

# Problem: Coverage reporting issues
# Solution: Check coverage tool installation
pip install pytest-cov            # Backend coverage
npm install --save-dev jest       # Frontend/mobile coverage

# Problem: BDD step definitions missing
# Solution: Implement missing steps
python tests/run_bdd_tests.py    # Will show undefined steps
# Create corresponding step definitions in tests/steps/
```

### **Performance Optimization Guidelines**

#### **Backend Performance**
- **Database Queries**: Use appropriate indexes, limit query results
- **ML Inference**: Implement model caching and batch processing
- **API Responses**: Add response caching where appropriate
- **Memory Management**: Monitor memory usage, implement cleanup

#### **Frontend Performance**
- **Component Optimization**: Use React.memo, useMemo, useCallback
- **Bundle Size**: Implement code splitting and lazy loading
- **Image Optimization**: Compress images, use appropriate formats
- **Network Optimization**: Minimize API calls, implement caching

#### **Mobile Performance**
- **App Startup**: Optimize initial loading, use splash screens
- **Animation Performance**: Use native driver, avoid JS animations
- **Memory Management**: Monitor memory leaks, implement cleanup
- **Battery Usage**: Optimize background operations, use efficient algorithms

### **Development Best Practices**

#### **Code Quality Standards**
- **Commit Messages**: Use descriptive messages with conventional commit format
- **Branch Management**: Use feature branches, maintain clean main branch
- **Code Reviews**: Peer review all changes before merging
- **Documentation**: Update documentation with code changes

#### **Security Considerations**
- **Input Validation**: Validate all user inputs on server side
- **Error Handling**: Don't expose sensitive information in error messages
- **Dependency Management**: Keep dependencies updated, scan for vulnerabilities
- **Environment Variables**: Never commit sensitive data to version control

#### **Testing Practices**
- **Test Coverage**: Maintain coverage thresholds (90% backend, 80% frontend/mobile)
- **Test Organization**: Group tests logically, use descriptive names
- **Mocking**: Mock external dependencies for isolated testing
- **CI/CD**: Integrate testing into continuous integration pipeline

### **Project Success Criteria**

#### **Functional Requirements**
- ✅ Working disease detection system with ML integration
- ✅ Multi-platform support (web, mobile, API)
- ✅ User authentication and data management
- ✅ Image upload and processing pipeline
- ✅ Scan history and analytics

#### **Quality Requirements**
- ✅ Comprehensive TDD/BDD testing framework
- ✅ Code coverage standards compliance
- ✅ Clean, documented codebase
- ✅ Cross-platform development workflow
- ✅ Educational development practices demonstration

#### **Educational Objectives**
- ✅ TDD/BDD methodology implementation
- ✅ Full-stack development practices
- ✅ Machine learning integration
- ✅ Mobile development with React Native
- ✅ CI/CD pipeline implementation

**⚠️ Project Context Reminder**: This is an academic capstone project for educational purposes. Security implementation is basic and suitable for demonstration, not production deployment. Focus is on learning modern development practices and technologies.

## Development Guidelines for School Project

### Code Quality Standards (Educational Context)
- **TDD Approach**: Write tests before implementing features for learning
- **BDD Practices**: Use Gherkin scenarios to define user behavior requirements
- **Basic Security**: Implement fundamental security measures for academic demonstration
- **Documentation**: Maintain clear code comments and API documentation
- **Version Control**: Follow git best practices for team collaboration

### When Working on This Project:
1. **Educational Focus**: Remember this is a learning project, not production software
2. **Security Awareness**: Basic security is sufficient for academic environment
3. **Testing Practices**: Use TDD/BDD to learn proper development methodologies
4. **Scope Management**: Focus on core functionality required for capstone demonstration
5. **Team Collaboration**: Follow development standards for academic team projects

### Project Success Criteria:
- ✅ Working disease detection system with ML integration
- ✅ Functional web and mobile applications
- ✅ Proper TDD/BDD implementation demonstration
- ✅ Clean, documented codebase
- ✅ Successful capstone project presentation
- ✅ Learning objectives achieved for CPE025/CPE026