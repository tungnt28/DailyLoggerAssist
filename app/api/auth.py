"""
Authentication API Routes - Daily Logger Assist

API endpoints for user authentication, OAuth flows, and token management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from typing import Dict, Any

from app.database.connection import get_db
from app.schemas.auth import (
    TokenResponse, TeamsAuthRequest, TeamsAuthCallback,
    JIRAAuthRequest, EmailAuthRequest, AuthStatusResponse
)
from app.schemas.user import UserCreate, UserResponse
from app.models.user import User
from app.utils.auth import (
    create_access_token, create_refresh_token, verify_token,
    encrypt_credentials, generate_state_token
)
from app.dependencies import get_current_user, get_optional_user
from app.config import settings
from loguru import logger

router = APIRouter()

# In-memory state storage for OAuth flows (use Redis in production)
oauth_states: Dict[str, Dict[str, Any]] = {}

@router.get("/status", response_model=AuthStatusResponse)
async def get_auth_status(
    current_user: User = Depends(get_optional_user)
):
    """Get current authentication status"""
    if not current_user:
        return AuthStatusResponse(authenticated=False)
    
    return AuthStatusResponse(
        authenticated=True,
        user_id=str(current_user.id),
        teams_connected=bool(current_user.teams_credentials),
        jira_connected=bool(current_user.jira_credentials),
        email_connected=bool(current_user.email_credentials)
    )

@router.post("/teams/login")
async def initiate_teams_oauth(
    request: TeamsAuthRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_optional_user)
):
    """Initiate Microsoft Teams OAuth flow"""
    
    if not settings.TEAMS_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Teams integration not configured"
        )
    
    # Generate state token for security
    state = generate_state_token()
    
    # Store state information
    oauth_states[state] = {
        "user_id": str(current_user.id) if current_user else None,
        "redirect_uri": request.redirect_uri,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Construct OAuth URL
    oauth_url = (
        f"https://login.microsoftonline.com/{settings.TEAMS_TENANT_ID}/oauth2/v2.0/authorize"
        f"?client_id={settings.TEAMS_CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={settings.TEAMS_REDIRECT_URI}"
        f"&response_mode=query"
        f"&scope=https://graph.microsoft.com/ChannelMessage.Read.All"
        f"&state={state}"
    )
    
    return {"authorization_url": oauth_url, "state": state}

@router.get("/teams/callback")
async def teams_oauth_callback(
    code: str,
    state: str,
    db: Session = Depends(get_db)
):
    """Handle Microsoft Teams OAuth callback"""
    
    # Verify state
    if state not in oauth_states:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter"
        )
    
    state_info = oauth_states.pop(state)
    
    try:
        # TODO: Exchange code for tokens using Microsoft Graph API
        # This is a placeholder implementation
        
        # Simulate token exchange
        access_token = f"teams_access_token_{code[:10]}"
        refresh_token = f"teams_refresh_token_{code[:10]}"
        
        # Store credentials
        teams_credentials = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
        }
        
        encrypted_credentials = encrypt_credentials(teams_credentials)
        
        # Update user or create new user
        user_id = state_info.get("user_id")
        if user_id:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.teams_credentials = encrypted_credentials
                db.commit()
                
                return {"message": "Teams integration successful", "status": "connected"}
        
        # If no current user, redirect to complete registration
        return {
            "message": "Teams authorization successful",
            "status": "needs_registration",
            "temp_credentials": encrypted_credentials
        }
        
    except Exception as e:
        logger.error(f"Teams OAuth callback error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth callback failed"
        )

@router.post("/jira/login")
async def connect_jira(
    request: JIRAAuthRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Connect JIRA account"""
    
    try:
        # TODO: Validate JIRA credentials by making test API call
        # This is a placeholder implementation
        
        jira_credentials = {
            "server_url": request.server_url,
            "username": request.username,
            "api_token": request.api_token,
            "connected_at": datetime.utcnow().isoformat()
        }
        
        encrypted_credentials = encrypt_credentials(jira_credentials)
        current_user.jira_credentials = encrypted_credentials
        db.commit()
        
        return {"message": "JIRA connected successfully", "status": "connected"}
        
    except Exception as e:
        logger.error(f"JIRA connection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to connect to JIRA"
        )

@router.post("/email/login")
async def connect_email(
    request: EmailAuthRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Connect email account"""
    
    try:
        # TODO: Validate email credentials by making test connection
        # This is a placeholder implementation
        
        email_credentials = {
            "email": request.email,
            "password": request.password,  # Should be encrypted
            "server": request.server,
            "port": request.port,
            "use_tls": request.use_tls,
            "connected_at": datetime.utcnow().isoformat()
        }
        
        encrypted_credentials = encrypt_credentials(email_credentials)
        current_user.email_credentials = encrypted_credentials
        db.commit()
        
        return {"message": "Email connected successfully", "status": "connected"}
        
    except Exception as e:
        logger.error(f"Email connection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to connect email account"
        )

@router.post("/register", response_model=TokenResponse)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Register new user and return access token"""
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user = User(
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        preferences=user_data.preferences or {}
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        refresh_token=refresh_token
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token"""
    
    try:
        # Verify refresh token
        user_id = await verify_token(refresh_token)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Verify user exists
        from uuid import UUID
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        user = db.query(User).filter(User.id == user_uuid).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new access token
        access_token = create_access_token(data={"sub": str(user.id)})
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not refresh token"
        )

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user)
):
    """Logout user (invalidate tokens)"""
    
    # TODO: Add token to blacklist if using token blacklisting
    # For now, just return success message
    
    return {"message": "Successfully logged out"}

@router.delete("/disconnect/{service}")
async def disconnect_service(
    service: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disconnect external service"""
    
    if service not in ["teams", "jira", "email"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid service"
        )
    
    try:
        if service == "teams":
            current_user.teams_credentials = None
        elif service == "jira":
            current_user.jira_credentials = None
        elif service == "email":
            current_user.email_credentials = None
        
        db.commit()
        
        return {"message": f"{service.title()} disconnected successfully"}
        
    except Exception as e:
        logger.error(f"Service disconnection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disconnect service"
        ) 