"""
Authentication Schemas - Daily Logger Assist

Pydantic schemas for authentication-related requests and responses.
"""

from pydantic import BaseModel, EmailStr
from typing import Optional

class LoginRequest(BaseModel):
    """Login request schema"""
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None

class TeamsAuthRequest(BaseModel):
    """Teams OAuth request schema"""
    redirect_uri: str

class TeamsAuthCallback(BaseModel):
    """Teams OAuth callback schema"""
    code: str
    state: Optional[str] = None

class JIRAAuthRequest(BaseModel):
    """JIRA authentication request schema"""
    server_url: str
    username: str
    api_token: str

class EmailAuthRequest(BaseModel):
    """Email authentication request schema"""
    email: EmailStr
    password: str
    server: str = "outlook.office365.com"
    port: int = 993
    use_tls: bool = True

class AuthStatusResponse(BaseModel):
    """Authentication status response"""
    authenticated: bool
    user_id: Optional[str] = None
    teams_connected: bool = False
    jira_connected: bool = False
    email_connected: bool = False
    expires_at: Optional[str] = None 