import logging
import os
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from routers import router as api_router
from db import ensure_indexes
from seed import seed_recommendations
from settings import ALLOWED_ORIGINS, UPLOAD_DIR

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


@asynccontextmanager
async def lifespan(app: FastAPI):
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
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# ---------------------- HEALTH ------------------------
@app.get("/health")
def health():
    return {"status": "ok", "message": "RiceGuard backend (Web + Mobile) is running."}

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
    # Log full error for debugging
    log.error(f"Unhandled exception: {type(exc).__name__}: {str(exc)}")
    log.error(f"Request: {request.method} {request.url}")
    log.error(f"Traceback: {traceback.format_exc()}")

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


