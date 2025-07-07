"""
Authentication Utilities - Daily Logger Assist

Utilities for JWT token management, password hashing, and user authentication.
"""

from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings
import uuid

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
ALGORITHM = "HS256"

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token.
    
    Args:
        data: Data to encode in token
        expires_delta: Token expiration time
        
    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """
    Create JWT refresh token.
    
    Args:
        data: Data to encode in token
        
    Returns:
        str: Encoded JWT refresh token
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def verify_token(token: str) -> Optional[str]:
    """
    Verify JWT token and extract user ID.
    
    Args:
        token: JWT token to verify
        
    Returns:
        Optional[str]: User ID if token is valid, None otherwise
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return user_id
    except JWTError:
        return None

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password
        
    Returns:
        bool: True if password matches
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Hash password.
    
    Args:
        password: Plain text password
        
    Returns:
        str: Hashed password
    """
    return pwd_context.hash(password)

def generate_password_reset_token(email: str) -> str:
    """
    Generate password reset token.
    
    Args:
        email: User email
        
    Returns:
        str: Password reset token
    """
    delta = timedelta(hours=1)  # Token valid for 1 hour
    now = datetime.utcnow()
    expires = now + delta
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "sub": email, "type": "reset"},
        settings.SECRET_KEY, 
        algorithm=ALGORITHM
    )
    return encoded_jwt

def verify_password_reset_token(token: str) -> Optional[str]:
    """
    Verify password reset token.
    
    Args:
        token: Password reset token
        
    Returns:
        Optional[str]: Email if token is valid, None otherwise
    """
    try:
        decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        if decoded_token.get("type") != "reset":
            return None
        return decoded_token.get("sub")
    except JWTError:
        return None

def generate_state_token() -> str:
    """
    Generate state token for OAuth flows.
    
    Returns:
        str: Random state token
    """
    return str(uuid.uuid4())

def encrypt_credentials(credentials: dict) -> str:
    """
    Encrypt user credentials for storage.
    
    Args:
        credentials: Credentials dictionary
        
    Returns:
        str: Encrypted credentials
    """
    # TODO: Implement actual encryption
    # For now, we'll use JWT encoding as placeholder
    return jwt.encode(credentials, settings.SECRET_KEY, algorithm=ALGORITHM)

def decrypt_credentials(encrypted_credentials: str) -> Optional[dict]:
    """
    Decrypt user credentials.
    
    Args:
        encrypted_credentials: Encrypted credentials string
        
    Returns:
        Optional[dict]: Decrypted credentials or None if invalid
    """
    try:
        return jwt.decode(encrypted_credentials, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None 