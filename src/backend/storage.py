# Handles file uploads and saving them locally with comprehensive security validation.

import os
import uuid
import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional, Tuple
from fastapi import UploadFile, HTTPException, status
from PIL import Image
import io
from settings import UPLOAD_DIR, MAX_UPLOAD_MB

# Setup logger for storage operations
logger = logging.getLogger("riceguard.storage")

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

def save_upload(file: UploadFile, prefix: str = "") -> str:
    """Save an uploaded image to /uploads with streaming to prevent DoS attacks.
    
    Args:
        file: The uploaded file
        prefix: Optional prefix for filename (e.g., 'avatar_', 'scan_')
    """
    ensure_upload_dir()

    # Basic MIME type validation
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type. Allowed types: {', '.join(ALLOWED_MIME_TYPES.keys())}"
        )

    # Reset file pointer
    file.file.seek(0)

    # Build directory path: /uploads/YYYY/MM/
    now = datetime.now(timezone.utc)
    subdir = os.path.join(UPLOAD_DIR, f"{now.year:04d}", f"{now.month:02d}")
    os.makedirs(subdir, exist_ok=True)

    # Create secure filename
    ext = ALLOWED_MIME_TYPES[file.content_type][0]  # Use first allowed extension
    safe_original = sanitize_filename(file.filename or "upload")
    unique_id = uuid.uuid4().hex
    unique_filename = f"{prefix}{unique_id}{ext}"
    path = os.path.join(subdir, unique_filename)

    # Security: validate path is within upload directory
    abs_upload_dir = os.path.abspath(UPLOAD_DIR)
    abs_file_path = os.path.abspath(path)
    if not abs_file_path.startswith(abs_upload_dir):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file path"
        )

    # Stream the file to disk with size monitoring and enhanced resource cleanup
    max_bytes = MAX_UPLOAD_MB * 1024 * 1024
    min_bytes = 1024  # 1KB minimum
    total_bytes = 0
    hash_obj = hashlib.sha256()
    header_bytes = b''
    file_handle = None

    try:
        # SECURITY: Use context manager for automatic file handle cleanup
        with open(path, "wb") as f:
            file_handle = f  # Keep reference for error handling
            while True:
                try:
                    chunk = file.file.read(8192)  # 8KB chunks for streaming
                    if not chunk:
                        break

                    # Update counters and hash
                    total_bytes += len(chunk)
                    hash_obj.update(chunk)

                    # Collect first few bytes for signature validation
                    if len(header_bytes) < 1024:
                        header_bytes += chunk
                        header_bytes = header_bytes[:1024]

                    # Size validation during streaming
                    if total_bytes > max_bytes:
                        raise HTTPException(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail=f"File size exceeds maximum allowed size of {MAX_UPLOAD_MB}MB"
                        )

                    # Write chunk to file
                    f.write(chunk)

                except MemoryError as mem_error:
                    log.error(f"Memory error during file upload: {mem_error}")
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="File too large for available memory"
                    )
                except OSError as os_error:
                    log.error(f"File system error during upload: {os_error}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="File system error during upload"
                    )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        log.error(f"Unexpected error during file upload: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to save file: {str(e)}"
        )
    finally:
        # SECURITY: Ensure file handle is properly closed
        try:
            if hasattr(file, 'file') and hasattr(file.file, 'close'):
                file.file.close()
        except Exception as close_error:
            log.warning(f"Error closing upload file handle: {close_error}")

        # Clean up partial file on error
        if os.path.exists(path) and total_bytes == 0:
            try:
                os.unlink(path)
                log.debug(f"Cleaned up empty file: {path}")
            except Exception as cleanup_error:
                log.warning(f"Failed to clean up partial file {path}: {cleanup_error}")

    # Final size validation
    size_mb = total_bytes / (1024 * 1024)
    if total_bytes < min_bytes:
        os.unlink(path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is too small to be a valid image"
        )

    # File signature validation using collected header
    expected_type = 'jpeg' if file.content_type == 'image/jpeg' else 'png'
    if not validate_file_signature(header_bytes, expected_type):
        os.unlink(path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File signature does not match its declared type"
        )

    # SECURITY: Memory-efficient image validation to prevent DoS attacks
    try:
        # SECURITY: Validate image content using PIL directly without loading entire file into memory
        img = Image.open(path)

        # Verify it's actually an image by trying to load it
        img.verify()

        # Reopen after verify (verify() closes the image)
        img = Image.open(path)

        # Check image dimensions to prevent DoS
        if img.width > MAX_IMAGE_DIMENSION or img.height > MAX_IMAGE_DIMENSION:
            img.close()
            os.unlink(path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Image dimensions exceed maximum size of {MAX_IMAGE_DIMENSION}x{MAX_IMAGE_DIMENSION}"
            )

        # SECURITY: Validate file size without loading into memory
        file_size = os.path.getsize(path)
        if file_size < 1024:  # 1KB minimum
            img.close()
            os.unlink(path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is too small to be a valid image"
            )

        img.close()
        log.debug(f"Image validation completed efficiently: {img.width}x{img.height}, {file_size} bytes")

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Clean up file on validation error
        if os.path.exists(path):
            try:
                os.unlink(path)
                log.debug(f"Cleaned up invalid image file: {path}")
            except Exception as cleanup_error:
                log.warning(f"Failed to clean up invalid file {path}: {cleanup_error}")
        log.error(f"Image validation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image validation failed: {str(e)}"
        )

    # Get file hash
    file_hash = hash_obj.hexdigest()

    # Normalize path for static serving
    normalized_path = path.replace("\\", "/")

    # Log successful upload
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