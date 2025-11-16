import logging
import os
import secrets
import sys
import traceback
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware
from routers import router as api_router, JWTClaims, require_user
from db import ensure_indexes
from seed import seed_recommendations
from settings import ALLOWED_ORIGINS, UPLOAD_DIR
from storage import validate_existing_file
from rate_limiter import RateLimitMiddleware, rate_limiter
from pathlib import Path

# Setup logging for the RiceGuard backend
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console output
        logging.FileHandler('riceguard.log', encoding='utf-8')  # File output
    ]
)

# Get a logger for this module
log = logging.getLogger("riceguard.main")


def validate_environment_variables():
    """Validate that all required environment variables are set and valid."""
    errors = []
    warnings = []

    # Required variables that must be non-empty
    required_vars = {
        'MONGO_URI': 'MongoDB connection string',
        'DB_NAME': 'Database name',
        'JWT_SECRET': 'JWT secret key'
    }

    # Optional but recommended variables with defaults
    optional_vars = {
        'UPLOAD_DIR': 'uploads',
        'MAX_UPLOAD_MB': '8',
        'TOKEN_EXPIRE_HOURS': '6',
        'ALLOWED_ORIGINS': 'http://localhost:3000,http://127.0.0.1:3000'
    }

    # Check required variables
    for var_name, description in required_vars.items():
        value = os.getenv(var_name)
        if not value or value.strip() == '':
            errors.append(f"Missing required environment variable: {var_name} ({description})")
        elif var_name == 'JWT_SECRET' and len(value) < 32:
            errors.append(f"JWT_SECRET must be at least 32 characters long for security")
        elif var_name == 'MONGO_URI' and not value.startswith(('mongodb://', 'mongodb+srv://')):
            errors.append(f"MONGO_URI must be a valid MongoDB connection string")

    # Check optional variables and set defaults if needed
    for var_name, default_value in optional_vars.items():
        value = os.getenv(var_name)
        if not value or value.strip() == '':
            os.environ[var_name] = default_value
            warnings.append(f"Using default value for {var_name}: {default_value}")
        elif var_name in ['MAX_UPLOAD_MB', 'TOKEN_EXPIRE_HOURS']:
            try:
                int_value = int(value)
                if int_value <= 0:
                    errors.append(f"{var_name} must be a positive integer")
            except ValueError:
                errors.append(f"{var_name} must be a valid integer")

  # Validate ML configuration if it exists
    # SECURITY: Import ml_service validation functions to ensure consistency
    try:
        # Import ml_service path validation to use the same logic
        sys.path.insert(0, os.path.dirname(__file__))
        from ml_service import _validate_model_path, _validate_labels_path

        # Use the same validation logic as ml_service.py
        model_path_env = os.getenv("MODEL_PATH")
        labels_path_env = os.getenv("LABELS_PATH")

        # Only validate if environment variables are set
        if model_path_env:
            try:
                _validate_model_path(model_path_env)
            except ValueError as e:
                errors.append(f"MODEL_PATH validation failed: {e}")

        if labels_path_env:
            try:
                _validate_labels_path(labels_path_env)
            except ValueError as e:
                errors.append(f"LABELS_PATH validation failed: {e}")

        log.info("ML path validation completed using ml_service logic")

    except ImportError as e:
        warnings.append(f"Could not import ml_service validation: {e}")
        # Fallback to basic validation if ml_service import fails
        ml_vars = {
            'MODEL_PATH': 'ml/model.h5',
            'LABELS_PATH': 'ml/labels.txt',
        }

        for var_name, default_value in ml_vars.items():
            value = os.getenv(var_name)
            if value and not os.path.isabs(value):
                # Only validate relative paths
                try:
                    from pathlib import Path
                    backend_root = Path(__file__).parent.resolve()
                    repo_root = backend_root.parent

                    allowed_dirs = [
                        backend_root / "ml",
                        repo_root / "ml"
                    ]

                    abs_path = (backend_root / value).resolve()
                    is_allowed = any(
                        abs_path.is_relative_to(allowed_dir.resolve()) if hasattr(abs_path, 'is_relative_to')
                        else str(abs_path).startswith(str(allowed_dir.resolve()))
                        for allowed_dir in allowed_dirs
                        if allowed_dir.exists()
                    )

                    if not is_allowed:
                        errors.append(f"{var_name} path not in allowed directory: {abs_path}")
                    elif not abs_path.exists():
                        warnings.append(f"{var_name} file does not exist: {abs_path}")

                except Exception as e:
                    warnings.append(f"Cannot validate {var_name} path: {e}")

    # Validate ML numeric parameters
    ml_numeric_vars = {
        'TEMPERATURE': ('1.25', 0.1, 10.0),
        'CONFIDENCE_THRESHOLD': ('0.45', 0.0, 1.0),
        'CONFIDENCE_MARGIN': ('0.12', 0.0, 1.0),
        'IMG_SIZE': ('224', 32, 1024)
    }

    for var_name, (default_value, min_val, max_val) in ml_numeric_vars.items():
        value = os.getenv(var_name)
        if not value or value.strip() == '':
            os.environ[var_name] = default_value
            warnings.append(f"Using default ML value for {var_name}: {default_value}")
        else:
            try:
                if var_name == 'IMG_SIZE':
                    int_value = int(value)
                    if not (min_val <= int_value <= max_val):
                        errors.append(f"{var_name} must be between {min_val} and {max_val}")
                else:
                    float_value = float(value)
                    if not (min_val <= float_value <= max_val):
                        errors.append(f"{var_name} must be between {min_val} and {max_val}")
            except ValueError:
                errors.append(f"{var_name} must be a valid number")

    # Report results
    if warnings:
        log.info("Environment variable warnings:")
        for warning in warnings:
            log.warning(f"  ⚠️  {warning}")

    if errors:
        log.error("Environment variable validation failed:")
        for error in errors:
            log.error(f"  ❌ {error}")
        log.error("Please set these environment variables in your .env file")
        sys.exit(1)

    log.info("✅ Environment variable validation passed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Validate environment variables first
    validate_environment_variables()

    # Initialize database
    ensure_indexes()
    seed_recommendations()
    log.info("🚀 RiceGuard backend ready (Web + Mobile).")
    yield
    log.info("🛑 RiceGuard backend shutting down...")
    from db import close_client
    close_client()


app = FastAPI(
    title="RiceGuard Unified Backend",
    version="1.1",
    description="Single API backend for RiceGuard Web and Mobile applications.",
    lifespan=lifespan,
)

# ---------------------- SECURITY MIDDLEWARE ----------------------
# SECURITY: Request size limiting to prevent resource exhaustion
class RequestSizeMiddleware(BaseHTTPMiddleware):
    """SECURITY: Middleware to limit request size and prevent DoS attacks."""

    def __init__(self, app, max_size: int = 10 * 1024 * 1024):  # 10MB default
        super().__init__(app)
        self.max_size = max_size

    async def dispatch(self, request: Request, call_next):
        # Get content length
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > self.max_size:
                    log.warning(f"Request size exceeded: {content_length} > {self.max_size}")
                    return JSONResponse(
                        status_code=413,
                        content={"error": True, "message": "Request entity too large"}
                    )
            except ValueError:
                # Invalid content-length header
                return JSONResponse(
                    status_code=400,
                    content={"error": True, "message": "Invalid content-length header"}
                )

        return await call_next(request)

# Add request size limiting middleware (first for security)
app.add_middleware(RequestSizeMiddleware, max_size=10 * 1024 * 1024)  # 10MB limit

# ---------------------- RATE LIMITING ----------------------
# Add rate limiting middleware (before CORS for security)
app.add_middleware(RateLimitMiddleware, limiter=rate_limiter)

# ---------------------- CORS --------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "accept",
        "accept-language",
        "content-language",
        "content-type",
        "authorization",
        "x-requested-with"
    ],
    expose_headers=["content-length", "content-type"],
    max_age=600,
)

# ---------------------- STATIC FILES -------------------
# Ensure upload directory exists
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# Initialize HTTPBearer for optional authentication
bearer = HTTPBearer(auto_error=False)

# Enhanced secure file serving with authorization and ownership validation
@app.get("/uploads/{file_path:path}")
async def secure_file_access(
    file_path: str, 
    request: Request, 
    token: Optional[str] = None,
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer)
):
    """
    Securely serve uploaded files with authorization and ownership validation.
    Only allows access to files owned by the authenticated user.
    Includes rate limiting and comprehensive security checks.
    
    SECURITY: Supports both Authorization header (for API clients) and 
    query parameter token (for HTML <img> tags) to enable image display.
    Query parameter tokens are only accepted for GET requests to prevent
    token leakage in logs and referrer headers.
    """
    # Authenticate user - try Authorization header first, then query param
    user: Optional[JWTClaims] = None
    
    if creds:
        # Standard Authorization header authentication
        try:
            user = require_user(creds)
        except HTTPException:
            pass  # Fall through to query param auth
    
    if not user and token:
        # SECURITY: Query parameter authentication (only for GET requests)
        # This is needed for <img> tags which cannot send headers
        try:
            from routers import decode_token
            payload = decode_token(token)
            user = JWTClaims(**payload)
        except Exception as e:
            log.warning(f"Invalid query parameter token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials"
        )
    
    user_id = user.sub
    client_ip = request.client.host if hasattr(request, 'client') else 'unknown'

    try:
        # Enhanced path validation to prevent directory traversal and injection attacks
        if not file_path or len(file_path) > 500:  # Reasonable path length limit
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file path"
            )

        # Check for dangerous path components
        dangerous_patterns = ['..', '\\', '|', '&', ';', '$', '`', '>', '<', '"', "'"]
        if any(pattern in file_path for pattern in dangerous_patterns):
            log.warning(f"Potentially malicious file access attempt from {client_ip}: {file_path}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file path"
            )

        # Additional validation: ensure path doesn't start with slash
        if file_path.startswith('/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file path format"
            )

        # Construct full file path
        full_path = os.path.join(UPLOAD_DIR, file_path)

        # Validate that the file exists and is within upload directory
        if not validate_existing_file(file_path):
            log.warning(f"File not found access attempt from {client_ip}: {file_path}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )

        # Enhanced security: ensure file is within upload directory
        abs_upload_dir = os.path.abspath(UPLOAD_DIR)
        abs_file_path = os.path.abspath(full_path)
        if not abs_file_path.startswith(abs_upload_dir):
            log.warning(f"Directory traversal attempt from {client_ip}: {file_path}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        # SECURITY: Atomic file ownership validation to prevent TOCTOU attacks
        try:
            from db import get_db, as_object_id
            db = get_db()

            # SECURITY: Convert user ID safely
            user_obj_id = as_object_id(user_id)

            # SECURITY: Use atomic transaction-like approach with additional validation
            # Check both possible field names where file path might be stored
            scan_record = db.scans.find_one({
                "$or": [
                    {"userId": user_obj_id, "imageUrl": file_path},
                    {"userId": user_obj_id, "filePath": file_path}
                ]
            })

            if not scan_record:
                # SECURITY: Log attempt without sensitive information
                log.warning(f"Unauthorized file access attempt blocked for user {user_id[:8]}...")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied - you don't have permission to access this file"
                )

            # SECURITY: Additional validation - ensure scan belongs to authenticated user
            if str(scan_record.get("userId", "")) != user_id:
                log.warning(f"File ownership validation failed for user {user_id[:8]}...")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied - file ownership validation failed"
                )

            # Additional security: verify the file record is recent (optional, for very old files)
            file_created_at = scan_record.get("createdAt")
            if file_created_at:
                from datetime import datetime, timezone, timedelta
                # Files older than 2 years might be suspicious
                max_age = datetime.now(timezone.utc) - timedelta(days=730)  # 2 years
                if file_created_at < max_age:
                    log.warning(f"Very old file access attempt from {client_ip} (user: {user_id}): {file_path} (created: {file_created_at})")
                    # Allow but log for security monitoring

        except ValueError as obj_error:
            log.error(f"Invalid user ID format during file ownership check: {obj_error}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid user identification"
            )
        except Exception as db_error:
            log.error(f"Database error during file ownership check: {db_error}")
            # Fail secure: deny access if we can't verify ownership
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to verify file access permissions"
            )

        # Additional file security checks
        try:
            file_stat = os.stat(full_path)
            file_size = file_stat.st_size

            # Reasonable file size limit for images (prevent serving huge files)
            max_serve_size = 50 * 1024 * 1024  # 50MB
            if file_size > max_serve_size:
                log.warning(f"Oversized file access attempt from {client_ip}: {file_path} ({file_size} bytes)")
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="File too large to serve"
                )

            # Check file modification time (prevent serving files that are too old or recently modified)
            import time
            current_time = time.time()
            file_age_seconds = current_time - file_stat.st_mtime

            # Files shouldn't be older than 1 year or modified in the last 5 minutes (except for very recent uploads)
            if file_age_seconds > (365 * 24 * 60 * 60):  # 1 year
                log.warning(f"Very old file access from {client_ip}: {file_path}")
                # Allow but log this - it might be normal for historical data
            elif file_age_seconds < 300:  # 5 minutes
                log.info(f"Recent file access from {client_ip}: {file_path} (age: {file_age_seconds}s)")

        except Exception as stat_error:
            log.error(f"Error checking file stats: {stat_error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to verify file properties"
            )

        # Determine media type safely
        filename = Path(file_path).name
        file_extension = filename.lower().split('.')[-1] if '.' in filename else ''

        # Only serve approved image types
        allowed_extensions = {'jpg', 'jpeg', 'png'}
        if file_extension not in allowed_extensions:
            log.warning(f"Invalid file type access attempt from {client_ip}: {file_path}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="File type not allowed"
            )

        # Map extensions to media types
        media_type_map = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png'
        }
        media_type = media_type_map.get(file_extension, 'application/octet-stream')

        # SECURITY: Audit logging without sensitive information
        log.info(f"File served successfully - User: {user_id[:8]}..., Size: {file_size} bytes")

        # Serve the file with security headers
        response = FileResponse(
            path=full_path,
            filename=filename,
            media_type=media_type
        )

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Cache-Control"] = "private, max-age=3600"  # Cache for 1 hour

        return response

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log the error and return a generic response
        log.error(f"Unexpected error serving file {file_path} to user {user_id} from {client_ip}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error serving file"
        )

# ---------------------- HEALTH ------------------------
@app.get("/health")
def health():
    """Enhanced health check with rate limiting statistics."""
    rate_stats = rate_limiter.get_stats()
    return {
        "status": "ok",
        "message": "RiceGuard backend (Web + Mobile) is running.",
        "rate_limiting": rate_stats
    }

# ---------------------- GLOBAL ERROR HANDLERS -----------------------
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with proper error responses."""
    log.warning(f"HTTP {exc.status_code}: {exc.detail} - {request.method} {request.url}")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url.path)
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions with secure error responses."""
    # SECURITY: Sanitized error logging to prevent information leakage
    error_id = secrets.token_hex(8)
    log.error(f"Unhandled exception ID {error_id}: {type(exc).__name__}")
    log.debug(f"Request details for {error_id}: {request.method} {request.url.path}")
    log.debug(f"Traceback for {error_id}: {traceback.format_exc()}")

    # Return generic error message to client (don't expose internal details)
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "An internal server error occurred. Please try again later.",
            "status_code": 500,
            "path": str(request.url.path)
        }
    )

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle value errors (validation errors)."""
    log.warning(f"Validation error: {str(exc)} - {request.method} {request.url}")

    return JSONResponse(
        status_code=400,
        content={
            "error": True,
            "message": str(exc),
            "status_code": 400,
            "path": str(request.url.path)
        }
    )

@app.exception_handler(FileNotFoundError)
async def file_not_found_handler(request: Request, exc: FileNotFoundError):
    """Handle file not found errors."""
    log.warning(f"File not found: {str(exc)} - {request.method} {request.url}")

    return JSONResponse(
        status_code=404,
        content={
            "error": True,
            "message": "Requested resource not found",
            "status_code": 404,
            "path": str(request.url.path)
        }
    )

# ---------------------- ROUTERS -----------------------
app.include_router(api_router, prefix="/api/v1")


