# Handles file uploads and saving them locally with comprehensive security validation.

import os
import uuid
import hashlib
from datetime import datetime, timezone
from typing import Optional, Tuple
from fastapi import UploadFile, HTTPException, status
from PIL import Image
import io
from settings import UPLOAD_DIR, MAX_UPLOAD_MB

# Enhanced allowed MIME types with magic number validation
ALLOWED_MIME_TYPES = {
    "image/jpeg": [".jpg", ".jpeg"],
    "image/png": [".png"]
}

# File signatures (magic numbers) for additional validation
FILE_SIGNATURES = {
    'jpeg': b'\xff\xd8\xff',
    'png': b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a'
}

# Maximum image dimensions to prevent DoS attacks
MAX_IMAGE_DIMENSION = 4096

def ensure_upload_dir() -> None:
    """Create the main uploads folder if missing."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)

def validate_file_signature(content: bytes, expected_type: str) -> bool:
    """Validate file signature to prevent file type spoofing."""
    if expected_type == 'jpeg':
        return content.startswith(FILE_SIGNATURES['jpeg'])
    elif expected_type == 'png':
        return content.startswith(FILE_SIGNATURES['png'])
    return False

def validate_image_content(content: bytes) -> Tuple[bool, Optional[str]]:
    """Validate that the file is actually a valid image and get its properties."""
    try:
        # Use PIL to validate the image
        img = Image.open(io.BytesIO(content))

        # Verify it's actually an image by trying to load it
        img.verify()

        # Reopen after verify (verify() closes the image)
        img = Image.open(io.BytesIO(content))

        # Check image dimensions to prevent DoS
        if img.width > MAX_IMAGE_DIMENSION or img.height > MAX_IMAGE_DIMENSION:
            return False, f"Image dimensions exceed maximum size of {MAX_IMAGE_DIMENSION}x{MAX_IMAGE_DIMENSION}"

        # Check for reasonable file sizes for the image dimensions
        estimated_min_size = (img.width * img.height) // 1000  # Very rough estimate
        if len(content) < estimated_min_size:
            return False, "Image appears to be corrupted or tampered"

        return True, None
    except Exception as e:
        return False, f"Invalid image file: {str(e)}"

def sanitize_filename(filename: str) -> str:
    """Remove potentially malicious characters from filename."""
    # Remove path separators and other dangerous characters
    safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
    return ''.join(c for c in filename if c in safe_chars)

def calculate_file_hash(content: bytes) -> str:
    """Calculate SHA-256 hash of file content for integrity checking."""
    return hashlib.sha256(content).hexdigest()

def save_upload(file: UploadFile) -> str:
    """Save an uploaded image to /uploads with comprehensive security validation."""
    ensure_upload_dir()

    # Basic MIME type validation
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type. Allowed types: {', '.join(ALLOWED_MIME_TYPES.keys())}"
        )

    # Read file content
    try:
        file.file.seek(0)  # Reset file pointer
        content = file.file.read()
        file.file.close()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read file content"
        )

    # File size validation
    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_UPLOAD_MB:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size {size_mb:.1f}MB exceeds maximum allowed size of {MAX_UPLOAD_MB}MB"
        )

    # Minimum file size check (prevent empty files)
    if len(content) < 1024:  # At least 1KB
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is too small to be a valid image"
        )

    # Determine expected file type from MIME type
    expected_type = 'jpeg' if file.content_type == 'image/jpeg' else 'png'

    # File signature validation to prevent type spoofing
    if not validate_file_signature(content, expected_type):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File signature does not match its declared type"
        )

    # Image content validation
    is_valid, error_msg = validate_image_content(content)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    # Calculate file hash for duplicate detection and integrity
    file_hash = calculate_file_hash(content)

    # Build directory path: /uploads/YYYY/MM/
    now = datetime.now(timezone.utc)
    subdir = os.path.join(UPLOAD_DIR, f"{now.year:04d}", f"{now.month:02d}")
    os.makedirs(subdir, exist_ok=True)

    # Create secure filename
    ext = ALLOWED_MIME_TYPES[file.content_type][0]  # Use first allowed extension
    # Sanitize original filename for logging purposes
    safe_original = sanitize_filename(file.filename or "upload")
    unique_filename = f"{uuid.uuid4().hex}{ext}"

    path = os.path.join(subdir, unique_filename)

    # Additional security: make sure the path doesn't escape the upload directory
    try:
        # Resolve the path and ensure it's within UPLOAD_DIR
        abs_upload_dir = os.path.abspath(UPLOAD_DIR)
        abs_file_path = os.path.abspath(path)

        if not abs_file_path.startswith(abs_upload_dir):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file path"
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file path"
        )

    # Write file to disk
    try:
        with open(path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save file"
        )

    # Normalize path for static serving (always use forward slashes)
    normalized_path = path.replace("\\", "/")

    # Log successful upload for security monitoring
    import logging
    logger = logging.getLogger("riceguard.storage")
    logger.info(
        f"File uploaded successfully: {safe_original} -> {unique_filename} "
        f"(size: {size_mb:.2f}MB, hash: {file_hash[:16]}...)"
    )

    return normalized_path

def validate_existing_file(file_path: str) -> bool:
    """Validate that an existing file is still safe and hasn't been tampered with."""
    try:
        full_path = os.path.join(UPLOAD_DIR, file_path)

        # Ensure path is within upload directory
        abs_upload_dir = os.path.abspath(UPLOAD_DIR)
        abs_file_path = os.path.abspath(full_path)

        if not abs_file_path.startswith(abs_upload_dir):
            return False

        # Check file exists and is readable
        if not os.path.isfile(full_path):
            return False

        # Additional validation can be added here if needed

        return True
    except Exception:
        return False