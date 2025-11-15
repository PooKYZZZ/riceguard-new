# backend/routers.py
from __future__ import annotations

import logging
from datetime import datetime, timezone
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
    db: Any = get_db()
    if db.users.find_one({"email": body.email}):
        raise HTTPException(status_code=409, detail="Email already registered")

    try:
        password_hash = hash_password(body.password)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters with uppercase, lowercase, digit, and special character"
        )

    doc = {
        "name": body.name,
        "email": body.email,
        "passwordHash": password_hash,
        "createdAt": datetime.now(timezone.utc),
    }
    res = db.users.insert_one(doc)
    return RegisterOut(id=str(res.inserted_id), name=body.name, email=body.email)

@router.post("/auth/login", tags=["auth"])
def login(body: LoginIn, response: Response) -> LoginOut:
    db: Any = get_db()
    user = db.users.find_one({"email": body.email})
    if not user or not verify_password(body.password, user["passwordHash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token, expires_at = create_access_token(
        subject=str(user["_id"]),
        extra_claims={"email": user["email"], "name": user["name"]},
    )

    # Set secure httpOnly cookie
    cookie_settings = set_auth_cookie(token, expires_at)
    response.set_cookie(**cookie_settings)

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

    db: Any = get_db()
    ids = [as_object_id(i) for i in payload.ids]
    res = db.scans.delete_many({"_id": {"$in": ids}, "userId": as_object_id(user_id)})
    return BulkDeleteOut(deletedCount=res.deleted_count)

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
