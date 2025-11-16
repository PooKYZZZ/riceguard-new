"""
Security module for RiceGuard application
Handles authentication, password hashing, and JWT token management
"""

import os
import hashlib
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configuration from environment
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-here")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
TOKEN_EXPIRE_HOURS = int(os.getenv("TOKEN_EXPIRE_HOURS", "6"))

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to verify against

    Returns:
        True if password matches hash, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token

    Args:
        data: Dictionary of claims to include in token
        expires_delta: Optional expiration time delta

    Returns:
        JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate a JWT token

    Args:
        token: JWT token string

    Returns:
        Dictionary of claims if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None

def set_auth_cookie(response, token: str) -> None:
    """
    Set authentication cookie in response

    Args:
        response: FastAPI response object
        token: JWT token string
    """
    expires = datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS)
    response.set_cookie(
        key="access_token",
        value=token,
        expires=expires,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax"
    )

def clear_auth_cookie(response) -> None:
    """
    Clear authentication cookie from response

    Args:
        response: FastAPI response object
    """
    response.delete_cookie(key="access_token")

def generate_secure_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token

    Args:
        length: Length of token to generate

    Returns:
        Secure random token string
    """
    return secrets.token_urlsafe(length)

def create_api_key(user_id: str, name: str) -> str:
    """
    Create an API key for a user

    Args:
        user_id: User ID
        name: API key name/identifier

    Returns:
        API key string
    """
    timestamp = str(int(datetime.now(timezone.utc).timestamp()))
    data = f"{user_id}:{name}:{timestamp}"
    return hashlib.sha256(data.encode()).hexdigest()

# Rate limiting functions
def create_rate_limit_identifier(user_id: str, ip_address: str) -> str:
    """
    Create a consistent identifier for rate limiting

    Args:
        user_id: User ID (may be None for anonymous)
        ip_address: Client IP address

    Returns:
        Rate limit identifier string
    """
    if user_id:
        return f"user:{user_id}"
    else:
        return f"ip:{ip_address}"