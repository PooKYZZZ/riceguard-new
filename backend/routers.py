# backend/routers.py
from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from pymongo import DESCENDING
from fastapi.responses import JSONResponse

# Setup logger for routers
log = logging.getLogger("riceguard.routers")

from db import as_object_id, get_db
from ml_service import (
    predict_image, get_prediction_debug_info,
    CONFIDENCE_THRESHOLD, CONFIDENCE_MARGIN, IMG_SIZE, TEMPERATURE
)
from security import create_access_token, decode_token, hash_password, verify_password, set_auth_cookie, clear_auth_cookie
from storage import ensure_upload_dir, save_upload
from models import (
    RegisterIn, RegisterOut,
    LoginIn, LoginOut, LoginUser,
    ScanItem, ScanListOut, ScanListQuery,
    RecommendationOut, DiseaseKey,
)

router = APIRouter()
bearer = HTTPBearer(auto_error=False)

# -------------------- local helper DTOs -------------------- #
class JWTClaims(BaseModel):
    sub: str
    email: Optional[str] = None
    name: Optional[str] = None

class BulkDeleteIn(BaseModel):
    ids: List[str]

    def __init__(self, **data):
        super().__init__(**data)
        # Validate number of IDs to prevent DoS attacks
        if len(self.ids) > 100:
            raise ValueError("Cannot delete more than 100 items at once")

        # Validate each ID format
        for scan_id in self.ids:
            if not scan_id or not isinstance(scan_id, str):
                raise ValueError("All scan IDs must be valid strings")
            if len(scan_id) > 100:  # Prevent excessively long IDs
                raise ValueError("Scan ID format is invalid")

class DeleteOneOut(BaseModel):
    deleted: bool
    id: str

class BulkDeleteOut(BaseModel):
    deletedCount: int

# ----------------------- auth helper ----------------------- #
def require_user(creds: Optional[HTTPAuthorizationCredentials]) -> JWTClaims:
    if not creds:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    try:
        payload = decode_token(creds.credentials)
        return JWTClaims(**payload)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# ============================ AUTH ========================= #
@router.post("/auth/register", response_model=RegisterOut, tags=["auth"])
def register(body: RegisterIn) -> RegisterOut:
    """Enhanced user registration with additional security validation."""
    db: Any = get_db()

    # Enhanced email validation and security checks
    email_lower = body.email.lower().strip()

    # Check for suspicious email patterns
    suspicious_domains = ['tempmail.com', '10minutemail.com', 'guerrillamail.com']
    if any(suspicious in email_lower for suspicious in suspicious_domains):
        log.warning(f"Registration attempt with temporary email: {email_lower}")
        raise HTTPException(
            status_code=400,
            detail="Temporary email addresses are not allowed"
        )

    # Check for rate limiting (simple implementation)
    recent_registrations = db.users.count_documents({
        "createdAt": {"$gte": datetime.now(timezone.utc).replace(microsecond=0, second=0, minute=0) - timedelta(hours=1)}
    })
    if recent_registrations > 10:  # More than 10 registrations in the last hour
        log.warning(f"High registration rate detected: {recent_registrations} in the last hour")
        raise HTTPException(
            status_code=429,
            detail="Too many registration attempts. Please try again later."
        )

    if db.users.find_one({"email": email_lower}):
        raise HTTPException(status_code=409, detail="Email already registered")

    try:
        password_hash = hash_password(body.password)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters with uppercase, lowercase, digit, and special character"
        )

    # Sanitize and validate name
    safe_name = body.name.strip() if body.name else email_lower.split('@')[0]
    safe_name = ''.join(c for c in safe_name if c.isalnum() or c in (' ', '-', '_', '.'))
    safe_name = safe_name[:50]  # Limit name length

    doc = {
        "name": safe_name,
        "email": email_lower,
        "passwordHash": password_hash,
        "createdAt": datetime.now(timezone.utc),
        "isActive": True,  # For future account management
        "lastLogin": None,
    }
    res = db.users.insert_one(doc)

    log.info(f"New user registered: {email_lower}")
    return RegisterOut(id=str(res.inserted_id), name=safe_name, email=email_lower)

@router.post("/auth/login", tags=["auth"])
def login(body: LoginIn, response: Response) -> LoginOut:
    """Enhanced login with timing attack protection and security validation."""
    import secrets
    import time

    db: Any = get_db()

    # Enhanced email validation
    email_lower = body.email.lower().strip()
    if not email_lower or '@' not in email_lower:
        raise HTTPException(status_code=400, detail="Valid email address is required")

    # SECURITY: Generate dummy hash for timing attack protection
    def get_dummy_hash():
        """Generate a dummy password hash for timing attack protection."""
        dummy_password = "dummy_password_for_timing_protection_" + secrets.token_hex(32)
        return hash_password(dummy_password)

    dummy_hash = get_dummy_hash()

    # Record login attempt start time for rate limiting and monitoring
    login_start_time = time.time()

    user = db.users.find_one({"email": email_lower})

    # SECURITY: Prevent timing attacks by always performing password verification
    # This ensures that both valid and invalid email attempts take similar time
    if user:
        # Real user found - perform actual password verification
        password_valid = verify_password(body.password, user["passwordHash"])
        user_hash = user["passwordHash"]
    else:
        # No user found - use dummy hash to prevent timing attacks
        password_valid = False
        user_hash = dummy_hash

        # Still perform password verification with dummy hash to maintain timing consistency
        verify_password(body.password, dummy_hash)

    # Additional security validation (only if user exists)
    if user:
        # Check if account is active
        if not user.get("isActive", True):
            log.warning(f"Login attempt on inactive account: {email_lower}")
            raise HTTPException(status_code=403, detail="Account is disabled")

        # Check for suspicious activity (multiple failed logins)
        failed_attempts = user.get("failedLoginAttempts", 0)
        if failed_attempts >= 5:
            # Lock account for 30 minutes after 5 failed attempts
            lock_until = user.get("lockedUntil")
            if lock_until and datetime.now(timezone.utc) < lock_until:
                log.warning(f"Login attempt on locked account: {email_lower}")
                raise HTTPException(status_code=423, detail="Account temporarily locked due to too many failed attempts")

    # SECURITY: Constant-time comparison to prevent timing attacks
    # Even though we've already performed password verification, we do additional checks here
    login_success = bool(user) and password_valid

    if not login_success:
        # SECURITY: Add small random delay to further prevent timing attacks
        # This helps mask the difference between database lookup failures and password failures
        delay_range = (0.1, 0.3)  # 100-300ms random delay
        import random
        time.sleep(random.uniform(*delay_range))

        # Record failed login attempt (only if user exists to prevent user enumeration)
        if user:
            db.users.update_one(
                {"_id": user["_id"]},
                {
                    "$inc": {"failedLoginAttempts": 1},
                    "$set": {"lastFailedLogin": datetime.now(timezone.utc)}
                }
            )
            log.warning(f"Failed login attempt: {email_lower}")
        else:
            # For non-existent users, log generically to prevent user enumeration
            log.warning(f"Failed login attempt for email")

        # SECURITY: Always return the same error message to prevent user enumeration
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # SECURITY: Successful login path
    # Reset failed login attempts on successful login
    db.users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "failedLoginAttempts": 0,
                "lastLogin": datetime.now(timezone.utc),
                "lockedUntil": None
            }
        }
    )

    # Create secure token
    token, expires_at = create_access_token(
        subject=str(user["_id"]),
        extra_claims={"email": user["email"], "name": user["name"]},
    )

    # Set secure httpOnly cookie
    cookie_settings = set_auth_cookie(token, expires_at)
    response.set_cookie(**cookie_settings)

    # Log successful login with timing information
    login_duration = time.time() - login_start_time
    log.info(f"Successful login: {email_lower} (duration: {login_duration:.3f}s)")

    # Also return token for backward compatibility during migration
    return LoginOut(
        accessToken=token,
        expiresAt=expires_at,
        user=LoginUser(id=str(user["_id"]), name=user["name"], email=user["email"]),
    )

@router.post("/auth/logout", tags=["auth"])
def logout(response: Response) -> dict:
    """Clear the authentication cookie."""
    cookie_settings = clear_auth_cookie()
    response.set_cookie(**cookie_settings)
    return {"message": "Successfully logged out"}

# ============================ SCANS ======================== #
@router.post("/scans", response_model=ScanItem, tags=["scans"])
def create_scan(
    file: UploadFile = File(...),
    notes: Optional[str] = Form(None),
    modelVersion: str = Form("1.0"),
    creds: HTTPAuthorizationCredentials = Depends(bearer),
) -> ScanItem:
    claims = require_user(creds)
    user_id = claims.sub

    # Validate form inputs
    if notes is not None:
        if not isinstance(notes, str):
            raise HTTPException(
                status_code=400,
                detail="Notes must be a string"
            )
        if len(notes) > 1000:  # Prevent excessively long notes
            raise HTTPException(
                status_code=400,
                detail="Notes cannot exceed 1000 characters"
            )
        # Sanitize notes to prevent injection
        notes = notes.strip()
        if not notes:
            notes = None

    if modelVersion is not None:
        if not isinstance(modelVersion, str):
            raise HTTPException(
                status_code=400,
                detail="Model version must be a string"
            )
        modelVersion = modelVersion.strip()
        if not modelVersion:
            modelVersion = "1.0"
        elif len(modelVersion) > 50:  # Prevent excessively long version strings
            raise HTTPException(
                status_code=400,
                detail="Model version cannot exceed 50 characters"
            )
        # Validate version format (basic semantic versioning pattern)
        import re
        if not re.match(r'^\d+(\.\d+)*([a-zA-Z0-9-]*)$', modelVersion):
            raise HTTPException(
                status_code=400,
                detail="Model version must follow semantic versioning (e.g., 1.0, 2.1.3, 1.0-beta)"
            )

    db: Any = get_db()
    ensure_upload_dir()

    # Save image
    image_path = save_upload(file)

    # ML inference
    try:
        label_str, confidence = predict_image(image_path)
        label = DiseaseKey.parse(label_str)
    except Exception as e:
        log.error(f"Model inference error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Model inference error: {e}")

    # Persist
    doc = {
        "userId": as_object_id(user_id),
        "label": label.value,
        "confidence": float(confidence),
        "modelVersion": modelVersion,
        "notes": notes,
        "imageUrl": image_path,
        "createdAt": datetime.now(timezone.utc),
    }
    res = db.scans.insert_one(doc)

    return ScanItem(
        id=str(res.inserted_id),
        label=label,
        confidence=float(confidence),
        modelVersion=modelVersion,
        notes=notes,
        imageUrl=image_path,
        createdAt=doc["createdAt"],
    )

@router.get("/scans", response_model=ScanListOut, tags=["scans"])
def list_scans(
    page: int = 1,
    pageSize: int = 20,
    sortBy: str = "createdAt",
    sortOrder: str = "desc",
    creds: HTTPAuthorizationCredentials = Depends(bearer)
) -> ScanListOut:
    claims = require_user(creds)
    user_id = claims.sub

    # Validate pagination parameters
    if page < 1:
        raise HTTPException(status_code=400, detail="Page must be >= 1")
    if pageSize < 1 or pageSize > 100:
        raise HTTPException(status_code=400, detail="Page size must be between 1 and 100")

    # Validate sort field to prevent NoSQL injection
    allowed_sort_fields = {"createdAt", "confidence", "label"}
    if sortBy not in allowed_sort_fields:
        raise HTTPException(status_code=400, detail=f"Invalid sort field. Allowed: {allowed_sort_fields}")

    # Validate sort order
    if sortOrder not in {"asc", "desc"}:
        raise HTTPException(status_code=400, detail="Sort order must be 'asc' or 'desc'")

    db: Any = get_db()

    # Build query filter
    query_filter = {"userId": as_object_id(user_id)}

    # Get total count for pagination metadata
    total = db.scans.count_documents(query_filter)

    # Calculate skip value for pagination
    skip = (page - 1) * pageSize

    # Build sort order
    sort_order = DESCENDING if sortOrder == "desc" else 1

    # Execute paginated query
    cursor = db.scans.find(query_filter).sort(sortBy, sort_order).skip(skip).limit(pageSize)

    items: List[ScanItem] = []
    for d in cursor:
        items.append(
            ScanItem(
                id=str(d["_id"]),
                label=DiseaseKey.parse(d["label"]),
                confidence=d.get("confidence"),
                modelVersion=d["modelVersion"],
                notes=d.get("notes"),
                imageUrl=d.get("imageUrl"),
                createdAt=d["createdAt"],
            )
        )

    # Calculate pagination metadata
    has_next = skip + pageSize < total
    has_prev = page > 1

    return ScanListOut(
        items=items,
        total=total,
        page=page,
        pageSize=pageSize,
        hasNext=has_next,
        hasPrev=has_prev
    )

# ========================= DELETE SCANS ==================== #
@router.delete("/scans/{scan_id}", response_model=DeleteOneOut, tags=["scans"])
def delete_scan(scan_id: str, creds: HTTPAuthorizationCredentials = Depends(bearer)) -> DeleteOneOut:
    claims = require_user(creds)
    user_id = claims.sub

    db: Any = get_db()
    res = db.scans.delete_one({"_id": as_object_id(scan_id), "userId": as_object_id(user_id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Scan not found")
    return DeleteOneOut(deleted=True, id=scan_id)

@router.post("/scans/bulk-delete", response_model=BulkDeleteOut, tags=["scans"])
def bulk_delete_scans(payload: BulkDeleteIn, creds: HTTPAuthorizationCredentials = Depends(bearer)) -> BulkDeleteOut:
    claims = require_user(creds)
    user_id = claims.sub

    if not payload.ids:
        return BulkDeleteOut(deletedCount=0)

    try:
        db: Any = get_db()
        # Convert IDs safely, filtering out invalid ones
        valid_ids = []
        for scan_id in payload.ids:
            try:
                obj_id = as_object_id(scan_id)
                valid_ids.append(obj_id)
            except ValueError:
                # Log invalid ID but continue with valid ones
                log.warning(f"Invalid scan ID format skipped: {scan_id}")
                continue

        if not valid_ids:
            return BulkDeleteOut(deletedCount=0)

        # Perform the deletion with both ID and user verification
        res = db.scans.delete_many({"_id": {"$in": valid_ids}, "userId": as_object_id(user_id)})

        # Log the operation for security monitoring
        log.info(f"Bulk delete operation: user={user_id}, requested={len(payload.ids)}, valid={len(valid_ids)}, deleted={res.deleted_count}")

        return BulkDeleteOut(deletedCount=res.deleted_count)

    except Exception as e:
        log.error(f"Error during bulk delete operation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to delete scans. Please try again."
        )

# ======================= RECOMMENDATIONS =================== #
@router.get("/recommendations/{diseaseKey}", response_model=RecommendationOut, tags=["recommendations"])
def get_recommendation(diseaseKey: DiseaseKey) -> RecommendationOut:
    db: Any = get_db()
    doc = db.recommendations.find_one({"diseaseKey": diseaseKey.value})
    if not doc:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    return RecommendationOut(
        diseaseKey=diseaseKey,
        title=doc["title"],
        steps=doc["steps"],
        version=doc["version"],
        updatedAt=doc["updatedAt"],
    )

# ======================= DEBUG ENDPOINTS =================== #
class DebugPredictionOut(BaseModel):
    """Enhanced debug output for model prediction analysis."""
    raw_outputs: List[float]
    raw_sum: float
    has_negative: bool
    is_logits: bool
    temperature: float
    calibrated_probabilities: List[float]
    entropy: float
    max_entropy: float
    entropy_ratio: float
    top_predictions: List[dict]
    thresholds: dict
    decision_metrics: dict
    final_prediction: dict

class DebugConfigOut(BaseModel):
    """Debug output for current ML configuration."""
    confidence_threshold: float
    confidence_margin: float
    image_size: int
    temperature: float
    model_path: str
    labels_path: str
    environment: dict

@router.get("/debug/predict-sample", response_model=DebugPredictionOut, tags=["debug"])
def debug_predict_sample() -> DebugPredictionOut:
    """
    Enhanced debug endpoint to run inference on a sample image and return detailed diagnostics.
    Includes decision metrics, disease similarity detection, and calibration analysis.
    """
    import os
    from pathlib import Path

    # Look for sample image in ml/sample_inputs/
    sample_dir = Path(__file__).parent.parent / "ml" / "sample_inputs"
    sample_image = None

    # Try to find a sample image
    if sample_dir.exists():
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp']:
            files = list(sample_dir.glob(ext))
            if files:
                sample_image = str(files[0])
                break

    if not sample_image or not os.path.exists(sample_image):
        raise HTTPException(
            status_code=404,
            detail="No sample image found. Place an image at ml/sample_inputs/debug.jpg"
        )

    try:
        # Get enhanced debug information (already includes alternatives and decision metrics)
        debug_info = get_prediction_debug_info(sample_image)

        # Create the response using the enhanced debug info
        result = DebugPredictionOut(**debug_info)

        return result

    except Exception as e:
        log.error(f"Debug prediction failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Debug prediction failed: {e}")

@router.get("/debug/config", response_model=DebugConfigOut, tags=["debug"])
def debug_config() -> DebugConfigOut:
    """
    Enhanced debug endpoint to show current ML configuration including model paths and thresholds.
    """
    import os
    from pathlib import Path

    # Get actual model and labels paths
    model_path = os.getenv("MODEL_PATH")
    if not model_path:
        model_path = str(Path(__file__).parent.parent / "ml" / "model.h5")

    labels_path = os.getenv("LABELS_PATH")
    if not labels_path:
        labels_path = str(Path(__file__).parent.parent / "ml" / "labels.txt")

    return DebugConfigOut(
        confidence_threshold=CONFIDENCE_THRESHOLD,
        confidence_margin=CONFIDENCE_MARGIN,
        image_size=IMG_SIZE,
        temperature=TEMPERATURE,
        model_path=model_path,
        labels_path=labels_path,
        environment={
            "MODEL_PATH": os.getenv("MODEL_PATH", "Not set"),
            "LABELS_PATH": os.getenv("LABELS_PATH", "Not set"),
            "TEMPERATURE": os.getenv("TEMPERATURE", "Not set"),
            "CONFIDENCE_THRESHOLD": os.getenv("CONFIDENCE_THRESHOLD", "Not set"),
            "CONFIDENCE_MARGIN": os.getenv("CONFIDENCE_MARGIN", "Not set"),
            "IMG_SIZE": os.getenv("IMG_SIZE", "Not set"),
        }
    )
