"""
Security and Authentication Utilities

JWT token generation, validation, password hashing, and security utilities.
Implements 7-day JWT expiration with refresh tokens.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from jose import JWTError, jwt
from passlib.context import CryptContext

from cloud_backend.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7
REFRESH_TOKEN_EXPIRE_DAYS = 30


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
    
    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password
    
    Returns:
        True if password matches
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in token
        expires_delta: Optional expiration delta (defaults to 7 days)
    
    Returns:
        Encoded JWT token
    """
    if expires_delta is None:
        expires_delta = timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    
    expire = datetime.utcnow() + expires_delta
    
    to_encode = data.copy()
    to_encode.update({"exp": expire, "type": "access"})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=JWT_ALGORITHM
    )
    
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    Create a JWT refresh token.
    
    Args:
        data: Data to encode in token
    
    Returns:
        Encoded refresh token
    """
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode = data.copy()
    to_encode.update({"exp": expire, "type": "refresh"})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=JWT_ALGORITHM
    )
    
    return encoded_jwt


def decode_token(token: str, token_type: str = "access") -> Optional[dict]:
    """
    Decode and validate a JWT token.
    
    Args:
        token: JWT token string
        token_type: Expected token type (access or refresh)
    
    Returns:
        Decoded token data or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )
        
        if payload.get("type") != token_type:
            logger.warning(f"Token type mismatch: expected {token_type}")
            return None
        
        return payload
    
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        return None


def sanitize_input(value: str) -> str:
    """
    Sanitize user input to prevent injection attacks.
    
    Args:
        value: Input string
    
    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        return str(value)
    
    sanitized = value.strip()
    
    dangerous_chars = ["<", ">", "'", '"', "&", ";", "|", "`", "$", "(", ")", "{", "}"]
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, "")
    
    return sanitized


def validate_redirect_url(url: str, allowed_domains: list) -> bool:
    """
    Validate redirect URL to prevent open redirect vulnerabilities.
    
    Args:
        url: Redirect URL to validate
        allowed_domains: List of allowed domain names
    
    Returns:
        True if URL is safe to redirect to
    """
    from urllib.parse import urlparse
    
    try:
        parsed = urlparse(url)
        
        if not parsed.netloc:
            return True
        
        domain = parsed.netloc.lower()
        
        for allowed in allowed_domains:
            if domain == allowed.lower() or domain.endswith(f".{allowed.lower()}"):
                return True
        
        return False
    
    except Exception as e:
        logger.error(f"Error validating redirect URL: {e}")
        return False
