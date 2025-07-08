"""
FastAPI Dependencies - Daily Logger Assist

Common dependencies for authentication, database access, and request validation.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from app.database.connection import get_db
from app.models.user import User
from app.utils.auth import verify_token
from loguru import logger

# Security scheme for bearer token
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from token.
    
    Args:
        credentials: HTTP Bearer token credentials
        db: Database session
        
    Returns:
        User: Current authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    try:
        # Verify token and get user ID
        user_id = await verify_token(credentials.credentials)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Convert string user_id to UUID
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            logger.error(f"Invalid UUID format for user_id: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user ID format",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user from database
        user = db.query(User).filter(User.id == user_uuid).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user.
    
    Args:
        current_user: Current user from get_current_user dependency
        
    Returns:
        User: Current active user
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current user if authenticated, otherwise return None.
    
    This dependency is useful for endpoints that work with or without authentication.
    
    Args:
        credentials: Optional HTTP Bearer token credentials
        db: Database session
        
    Returns:
        Optional[User]: Current user if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    try:
        user_id = await verify_token(credentials.credentials)
        if not user_id:
            return None
        
        # Convert string user_id to UUID
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            logger.warning(f"Invalid UUID format for user_id: {user_id}")
            return None
        
        user = db.query(User).filter(User.id == user_uuid).first()
        if not user or not user.is_active:
            return None
        
        return user
    except Exception as e:
        logger.warning(f"Optional authentication failed: {e}")
        return None

class CommonQueryParams:
    """Common query parameters for list endpoints"""
    
    def __init__(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: str = "created_at",
        order_desc: bool = True
    ):
        self.skip = skip
        self.limit = min(limit, 1000)  # Maximum 1000 items per request
        self.order_by = order_by
        self.order_desc = order_desc 