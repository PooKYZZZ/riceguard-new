# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RiceGuard is a multi-platform rice leaf disease detection system developed by Team 27 for an academic capstone project (CPE025 Software Design, CPE026 Emerging Technologies 3). The system combines a FastAPI backend, React web portal, and mobile app with shared TensorFlow ML models for detecting 6 classes of rice leaf diseases.

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
- ML Pipeline: TensorFlow model (backend/ml/model.h5, 128MB) with temperature scaling calibration
- Mobile: React Native (Expo) with TensorFlow Lite for on-device inference
- Database: MongoDB Atlas with comprehensive indexing and query optimization

## Development Commands

### 🚀 Automated Setup (Recommended)
```bash
# Clone repository
git clone https://github.com/PooKYZZZ/riceguard-new.git
cd riceguard-new

# One-command setup for your platform
setup/setup.bat                    # Windows
chmod +x setup/setup.sh && ./setup/setup.sh  # macOS/Linux
python setup/setup.py              # Cross-platform Python

# Configure environment files
cp setup/environment/backend.env.example backend/.env
cp setup/environment/frontend.env.example frontend/.env

# Edit backend/.env with your MongoDB Atlas credentials

# Start development servers
python start-dev.py                # Start both backend and frontend
```

### Individual Component Development
```bash
# Backend only
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\Activate.ps1
# Linux/Mac:
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend only
cd frontend
npm install
npm start

# Mobile app only
cd mobileapp/riceguard
npm install
# Set environment variables:
$env:EXPO_PUBLIC_API_BASE_URL="http://<PC_IP>:8000/api/v1"  # PowerShell
export EXPO_PUBLIC_API_BASE_URL="http://<PC_IP>:8000/api/v1"  # bash/zsh
npx expo start --lan --clear
```

### Testing & Verification
```bash
# Verify setup is working
python verify-setup.py            # Comprehensive system verification

# Backend tests
cd backend
python -m pytest tests/
python -m pytest tests/test_fc_login.py

# Frontend tests
cd frontend
npm test
npm test --watch --coverage
```

### Environment Setup
Backend requires `.env` file:
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

Frontend requires `.env` file:
```env
REACT_APP_API_URL=http://127.0.0.1:8000/api/v1
```

Mobile app environment variables (set in terminal before running Expo):
```bash
EXPO_PUBLIC_API_BASE_URL=http://<PC_IP>:8000/api/v1
REACT_NATIVE_PACKAGER_HOSTNAME=<PC_IP>
```

## Architecture & Code Organization

### Backend Structure
- `main.py`: FastAPI application setup with CORS, static files, and lifespan management
- `routers.py`: API endpoints for authentication, scans, recommendations, and debug
- `db.py`: MongoDB connection management and index creation
- `models.py`: Pydantic models for request/response validation
- `ml_service.py`: TensorFlow model integration with singleton pattern and confidence calibration
- `storage.py`: File upload handling and validation
- `settings.py`: Environment configuration and constants
- `security.py`: JWT authentication and password hashing

### ML Integration Architecture
The ML service (`ml_service.py`) uses a singleton pattern for model loading with advanced features:
- **Temperature Scaling**: Confidence calibration with configurable temperature (default T=1.25)
- **Entropy-Based Decision Making**: Shannon entropy calculation for uncertainty detection
- **Disease Similarity**: Detection of commonly confused conditions with confidence margins
- **Comprehensive Debug Endpoints**: `/api/v1/debug/predict-sample`, `/api/v1/debug/config`
- **Image Processing**: 224x224 RGB preprocessing with centered square padding and normalization

**ML Decision Logic:**
- High confidence override (0.78+) with low entropy ratio (<0.45) yields certain predictions
- Multiple confidence/entropy criteria for balanced decision making
- Disease alias mapping for model compatibility (blast → leaf_blast, blight → bacterial_leaf_blight)

### Frontend Structure
- `src/api.js`: HTTP client with JWT handling and automatic error boundary integration
- `src/secureStorage.js`: Secure token management with httpOnly cookie support
- `src/errorHandler.js`: Safe fetch wrapper with comprehensive error handling
- `src/pages/`: Page components (ScanPage, HistoryPage) with file upload capabilities
- `src/components/`: Reusable components including ErrorBoundary for crash recovery

### Database Schema
- `users`: User accounts with email/password authentication and bcrypt hashing
- `scans`: Image upload records with ML predictions, metadata, and pagination support
- `recommendations`: Disease treatment guidance indexed by canonical disease keys

## Key Implementation Details

### ML Model Management
- **Model File**: `backend/ml/model.h5` (128MB, not tracked in Git, must be obtained separately)
- **Singleton Pattern**: Prevents multiple model loading for memory efficiency
- **Image Preprocessing**: 224x224 RGB resize with centered square padding and [0,1] normalization
- **Classes**: 6 canonical disease keys with legacy alias support
- **Confidence Calibration**: Temperature scaling with configurable optimization
- **Debug Tools**: Sample prediction endpoints for model validation

### Authentication Flow
- **JWT Implementation**: Tokens with 6-hour expiration (configurable via `TOKEN_EXPIRE_HOURS`)
- **Password Security**: bcrypt hashing with 12 rounds (configurable via `BCRYPT_ROUNDS`)
- **Secure Storage**: httpOnly cookies for XSS protection, with fallback support
- **CORS Configuration**: Strict origin validation with environment-based configuration
- **Session Management**: Automatic token refresh and secure logout handling

### File Upload Security
- **Format Validation**: JPEG, PNG, JPG with magic number verification
- **Size Limits**: Configurable (default 8MB via `MAX_UPLOAD_MB`)
- **Content Verification**: PIL-based image validation and dimension checking
- **Path Security**: UUID-based filenames with path traversal protection
- **Static Serving**: Secure file serving via `/uploads` endpoint with proper headers

### API Design Principles
- **RESTful Architecture**: `/api/v1/` prefix with consistent endpoint patterns
- **Error Handling**: Standardized error responses with appropriate HTTP status codes
- **Documentation**: Auto-generated OpenAPI docs at `/docs` with request/response examples
- **Health Monitoring**: `/health` endpoint for application status and dependency checks
- **Security**: Input validation via Pydantic models with comprehensive sanitization

### Core API Endpoints
```http
# Authentication
POST /api/v1/auth/register    # User account creation
POST /api/v1/auth/login       # Login with token generation
POST /api/v1/auth/logout      # Secure logout handling

# Scan Management
POST /api/v1/scans           # Upload and classify images
GET /api/v1/scans           # Paginated scan history
DELETE /api/v1/scans/{id}   # Individual scan deletion
POST /api/v1/scans/bulk-delete  # Bulk scan operations

# Disease Information
GET /api/v1/recommendations/{diseaseKey}  # Treatment guidance
GET /api/v1/debug/predict-sample          # ML model testing
GET /api/v1/debug/config                 # Configuration display
```

## Development Workflow

### Git Strategy
- **Main Branch**: `main` - production-ready code
- **Development Flow**: Feature branches → Pull requests → Code review → Merge
- **Team Structure**: Team 27 capstone project with specialized roles
- **Merge Strategy**: Manual conflict resolution with comprehensive testing

### Testing Strategy
- **Backend**: pytest framework with mongomock for database testing
  - API endpoint testing with comprehensive coverage
  - Authentication flow validation
  - File upload security testing
  - ML service integration testing
- **Frontend**: React Testing Library with Jest
  - Component testing for UI interactions
  - Error boundary validation
  - API client testing with mock responses
- **Manual Testing**: Swagger UI at `/docs` for API exploration
- **ML Validation**: Debug endpoints for model transparency and monitoring

### Environment Management
- **Development**: Local `.env` files with secure credential handling
- **Production**: Environment-specific configuration via environment variables
- **Mobile**: Terminal environment variables for Expo development
- **CORS**: Multi-origin support for development and mobile app integration

## Common Issues & Solutions

### Environment Setup
- **TensorFlow Compatibility**: Python 3.12+ requires TensorFlow alternative; use Python < 3.13 for full ML features
- **Node.js Requirements**: Use Node.js 18 LTS for optimal React development
- **Dependency Resolution**: `npm cache clean --force` for persistent npm issues
- **Virtual Environment**: Always activate Python venv before backend development

### ML Model Management
- **Critical Dependency**: `backend/ml/model.h5` (128MB) must be obtained separately - not tracked in Git
- **Version Compatibility**: TensorFlow 2.20.0 with proper Python version matching
- **Memory Optimization**: Singleton pattern prevents multiple model loading
- **Preprocessing Requirements**: Images must be properly preprocessed for accurate predictions
- **Temperature Calibration**: Use `temperature_calibrate.py` script for confidence optimization

### Database Connectivity
- **MongoDB Atlas**: IP whitelist required for development environments
- **Connection String**: Format: `mongodb+srv://user:pass@cluster.mongodb.net/db`
- **Index Strategy**: Proper indexing on `users.email`, `scans.userId`, `recommendations.diseaseKey`
- **Connection Management**: Connection pooling via pymongo with proper error handling

### Mobile Development
- **Network Configuration**: Use PC's LAN IP for mobile app connectivity (not phone's IP)
- **Firewall Settings**: Open ports 8000 (backend), 8081 (Metro), 19000-19002 (Expo)
- **CORS Origins**: Add mobile development origins to `ALLOWED_ORIGINS` environment variable
- **Expo Development**: Prefer `--lan` mode over tunnel for better performance

### Production Deployment
- **Environment Security**: Never commit `.env` files - use `.env.example` as template
- **Secret Management**: Generate strong JWT secrets (32+ characters) for production
- **SSL/TLS**: Configure HTTPS for production API endpoints
- **Monitoring**: Set up health check monitoring via `/health` endpoint

## Performance Optimization

### Database Performance
- **Index Strategy**: Comprehensive indexing on `users.email`, `scans.userId`, `recommendations.diseaseKey`
- **Pagination**: 100-item limit for scan history queries with pagination support
- **Query Optimization**: Aggregation pipelines for complex data operations
- **Connection Management**: Connection pooling via pymongo for efficient resource usage

### ML Model Performance
- **Memory Efficiency**: Singleton pattern prevents duplicate model loading
- **Inference Speed**: Optimized image preprocessing and prediction pipeline
- **Confidence Calibration**: Temperature scaling for reliable prediction confidence
- **Performance Monitoring**: Inference time tracking and model health checks
- **Caching Strategy**: Model weights cached in memory for rapid inference

### Frontend Performance
- **Component Optimization**: Lazy loading and React.memo for unnecessary re-renders
- **Image Handling**: Preview before upload with client-side validation
- **Network Efficiency**: Loading states and error boundaries for better UX
- **Bundle Optimization**: Code splitting and lazy route loading
- **Memory Management**: Proper cleanup and error boundary implementations

## Security Architecture

### Input Validation & Sanitization
- **Pydantic Models**: Comprehensive request/response validation with custom validators
- **Email Security**: RFC-compliant email format validation
- **Password Requirements**: 8+ characters with complexity requirements
- **File Upload Security**: Magic number validation, content scanning, and path protection

### Authentication & Authorization
- **JWT Implementation**: Secure token generation with configurable expiration
- **Password Security**: bcrypt hashing with 12-round salt (configurable)
- **Session Management**: Secure httpOnly cookies with XSS protection
- **CORS Configuration**: Strict origin validation with environment-based settings

### Data Protection & Privacy
- **Credential Management**: Environment variables with proper secret handling
- **File Security**: Secure file storage with validation and access controls
- **Database Encryption**: MongoDB Atlas TLS encryption for data in transit
- **Injection Prevention**: Comprehensive input sanitization and parameter validation

### Infrastructure Security
- **Network Security**: Proper firewall configuration for development ports
- **Environment Isolation**: Separate configurations for development and production
- **Error Handling**: Secure error responses without information leakage
- **Monitoring**: Security event logging and brute force detection