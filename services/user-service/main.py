"""
User Service for Daily Logger Assist

Handles user authentication, registration, and profile management.
"""

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import timedelta
import sys
import os
from typing import List, Optional
import logging
from pydantic import BaseModel, EmailStr, field_validator
import uuid
from datetime import datetime

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.config.base import BaseConfig
from shared.utils.database import init_database, get_db
from shared.utils.auth import init_auth, get_auth
from shared.models import User, Message, WorkItem, JIRATicket, Report

# Initialize configuration
config = BaseConfig()

# Initialize database
db_manager = init_database(config.DATABASE_URL, "user-service")
db_manager.create_tables()

# Initialize authentication
auth_manager = init_auth(config.SECRET_KEY, config.REDIS_URL)

# Create FastAPI app
app = FastAPI(
    title="Daily Logger Assist - User Service",
    description="User authentication and management service",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS if config.ENVIRONMENT == "production" else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Pydantic models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    is_active: bool
    created_at: str
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

class LoginForm(BaseModel):
    email: EmailStr
    password: str

# Helper functions
def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()

def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
    """Get user by ID"""
    return db.query(User).filter(User.id == user_id).first()

def create_user(db: Session, user: UserCreate) -> User:
    """Create a new user"""
    hashed_password = auth_manager.hash_password(user.password)
    db_user = User(
        email=user.email,
        hashed_password=hashed_password,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate user with email and password"""
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not auth_manager.verify_password(password, user.hashed_password):
        return None
    return user

def get_current_user_from_header(request: Request, db: Session = Depends(get_db)) -> User:
    """Get current user from X-User-ID header (set by gateway)"""
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID header missing"
        )
    
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

# Endpoints

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_healthy = db_manager.health_check()
    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "service": "User Service",
        "version": "1.0.0",
        "database": "healthy" if db_healthy else "unhealthy"
    }

@app.post("/api/v1/auth/register", response_model=UserResponse)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    db_user = get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    new_user = create_user(db, user)
    return UserResponse(
        id=str(new_user.id),
        email=new_user.email,
        first_name=new_user.first_name,
        last_name=new_user.last_name,
        is_active=new_user.is_active,
        created_at=str(new_user.created_at) if new_user.created_at else None,
        updated_at=str(new_user.updated_at) if new_user.updated_at else None
    )

@app.post("/api/v1/auth/login", response_model=Token)
async def login_user(login_data: LoginForm, db: Session = Depends(get_db)):
    """Login user and return JWT tokens"""
    user = authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Create tokens
    access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=config.REFRESH_TOKEN_EXPIRE_DAYS)
    
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "scopes": ["user"]
    }
    
    access_token = auth_manager.create_access_token(
        data=token_data,
        expires_delta=access_token_expires
    )
    
    refresh_token = auth_manager.create_refresh_token(
        data=token_data,
        expires_delta=refresh_token_expires
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@app.post("/api/v1/auth/refresh", response_model=Token)
async def refresh_token(refresh_token: str):
    """Refresh access token using refresh token"""
    new_access_token = auth_manager.refresh_access_token(refresh_token)
    if not new_access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    return {
        "access_token": new_access_token,
        "refresh_token": refresh_token,  # Keep the same refresh token
        "token_type": "bearer"
    }

@app.post("/api/v1/auth/logout")
async def logout_user(request: Request):
    """Logout user and blacklist token"""
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required"
        )
    
    token = auth_header.split(" ")[1]
    success = auth_manager.blacklist_token(token)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to logout"
        )
    
    return {"message": "Successfully logged out"}

@app.get("/api/v1/users/me", response_model=UserResponse)
async def get_current_user(current_user: User = Depends(get_current_user_from_header)):
    """Get current user profile"""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        is_active=current_user.is_active,
        created_at=str(current_user.created_at) if current_user.created_at else None,
        updated_at=str(current_user.updated_at) if current_user.updated_at else None
    )

@app.put("/api/v1/users/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user_from_header),
    db: Session = Depends(get_db)
):
    """Update current user profile"""
    for field, value in user_update.dict(exclude_unset=True).items():
        setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        is_active=current_user.is_active,
        created_at=str(current_user.created_at) if current_user.created_at else None,
        updated_at=str(current_user.updated_at) if current_user.updated_at else None
    )

@app.post("/api/v1/users/change-password")
async def change_password(
    password_change: PasswordChange,
    current_user: User = Depends(get_current_user_from_header),
    db: Session = Depends(get_db)
):
    """Change user password"""
    # Verify current password
    if not auth_manager.verify_password(password_change.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    # Update password
    current_user.hashed_password = auth_manager.hash_password(password_change.new_password)
    db.commit()
    
    return {"message": "Password changed successfully"}

@app.get("/api/v1/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_user_from_header),
    db: Session = Depends(get_db)
):
    """Get user by ID (admin or self only)"""
    # For now, users can only access their own profile
    if str(current_user.id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=str(user.id),
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        created_at=str(user.created_at) if user.created_at else None,
        updated_at=str(user.updated_at) if user.updated_at else None
    )

@app.get("/api/v1/users", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user_from_header),
    db: Session = Depends(get_db)
):
    """List users (admin only - for now returns empty list)"""
    # TODO: Implement admin role checking
    # For now, return empty list as regular users shouldn't see other users
    return []

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Application startup tasks"""
    logging.info("User Service starting...")
    logging.info(f"Environment: {config.ENVIRONMENT}")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks"""
    logging.info("User Service shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    ) 