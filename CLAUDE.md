# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RiceGuard is a full-stack web application for rice leaf disease detection using machine learning. The project consists of a FastAPI backend with MongoDB Atlas database, React frontend, and TensorFlow ML model integration for disease classification.

**Core Architecture:**
- Backend: FastAPI with MongoDB Atlas for user management, scan history, and ML predictions
- Frontend: React SPA with JWT authentication and file upload capabilities
- ML Pipeline: TensorFlow model (128MB model.h5) with confidence calibration and disease similarity detection
- Database: Cloud-hosted MongoDB with proper indexing and query optimization

## Development Commands

### Quick Start (Recommended)
```bash
# Start both backend and frontend with one command
python dev_runner.py
```

### Backend Development
```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\Activate.ps1
# Linux/Mac:
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend Development
```bash
cd frontend
npm install
npm start
```

### Testing
```bash
# Backend tests
cd backend
python -m pytest tests/

# Frontend tests
cd frontend
npm test
```

### Environment Setup
Backend requires `.env` file:
```env
MONGO_URI=mongodb+srv://<user>:<pass>@<cluster>.mongodb.net/riceguard_db
DB_NAME=riceguard_db
JWT_SECRET=CHANGE_ME_SUPER_SECRET
JWT_ALGORITHM=HS256
TOKEN_EXPIRE_HOURS=6
UPLOAD_DIR=uploads
MAX_UPLOAD_MB=8
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173
```

Frontend requires `.env` file:
```env
REACT_APP_API_URL=http://127.0.0.1:8000/api/v1
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
The ML service uses a singleton pattern for model loading and includes:
- Temperature scaling for confidence calibration (optimized to 1.05)
- Disease similarity detection for commonly confused conditions
- Enhanced debug endpoints for transparency and monitoring
- Performance tracking with prediction time monitoring

### Frontend Structure
- `src/api.js`: HTTP client for backend communication with JWT handling
- `src/AuthContext.js`: React context for authentication state management
- `src/pages/`: Page components (ScanPage, HistoryPage, LoginPage)
- `src/components/`: Reusable components (UploadScan, Navbar, AuthModals)

### Database Schema
- `users`: User accounts with email/password authentication
- `scans`: Image upload records with ML predictions and metadata
- `recommendations`: Disease treatment guidance and information

## Key Implementation Details

### ML Model Management
- Model file location: `backend/ml/model.h5` (128MB, not tracked in Git)
- Singleton pattern prevents multiple model loading
- Image preprocessing: resize to 224x224, normalize to [0,1]
- Classes: ["brown_spot", "blast", "blight", "healthy"]
- Confidence calibration using temperature scaling

### Authentication Flow
- JWT tokens with bcrypt password hashing
- Token expiration: 6 hours (configurable)
- Secure password storage with salted hashing
- CORS configuration for cross-origin requests

### File Upload Handling
- Supported formats: JPEG, PNG, JPG
- Maximum file size: 5MB (configurable)
- Image validation and preprocessing
- Static file serving via `/uploads` endpoint

### API Design Principles
- RESTful endpoints with `/api/v1/` prefix
- Consistent error responses with proper HTTP status codes
- Automatic OpenAPI documentation at `/docs`
- Health check endpoint at `/health`

## Development Workflow

### Git Strategy
- Main branch: `main`
- Feature branches for new functionality
- Pull requests for code review
- Conflict resolution via manual merge

### Testing Strategy
- Backend: pytest with API endpoint testing
- Frontend: React Testing Library for component testing
- Manual testing via Swagger UI at `/docs`
- ML model validation via debug endpoints

### Environment Management
- Development: local `.env` files
- Production: environment-specific configuration
- Secure credential handling with python-dotenv
- CORS configuration for multiple origins

## Common Issues & Solutions

### React Version Compatibility
- Project uses React 18.3.1 for Create React App compatibility
- Node.js 18 LTS recommended for development
- Use `npm cache clean --force` for dependency issues

### ML Model Loading
- Model file must be placed at `backend/ml/model.h5`
- Ensure TensorFlow version compatibility (2.20.0)
- Memory management via singleton pattern
- Model inference requires proper image preprocessing

### Database Connectivity
- MongoDB Atlas requires IP whitelist for development
- Connection string format: `mongodb+srv://user:pass@cluster.mongodb.net/db`
- Proper indexing for query optimization
- Connection pooling via pymongo

## Performance Considerations

### Database Optimization
- Indexes on `users.email`, `scans.userId`, and `recommendations.diseaseKey`
- Pagination for scan history queries
- Aggregation pipelines for complex queries

### ML Model Performance
- Singleton pattern reduces memory usage
- Confidence calibration improves prediction reliability
- Disease similarity detection enhances user experience
- Performance monitoring for inference times

### Frontend Optimization
- Lazy loading for components
- Image preview before upload
- Loading states during API calls
- Error boundaries for better UX

## Security Best Practices

### Input Validation
- Pydantic models for request validation
- Email format validation with regex
- Password strength requirements
- File type and size restrictions

### Authentication Security
- JWT tokens with expiration
- bcrypt password hashing
- CORS configuration for allowed origins
- Rate limiting considerations

### Data Protection
- Environment variables for sensitive data
- Secure file upload handling
- Database connection encryption
- Input sanitization to prevent injection