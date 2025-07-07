"""
User Schemas - Daily Logger Assist

Pydantic schemas for user-related requests and responses.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    is_active: bool = True

class UserCreate(UserBase):
    """User creation schema"""
    preferences: Optional[Dict[str, Any]] = None

class UserUpdate(BaseModel):
    """User update schema"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    is_active: Optional[bool] = None
    preferences: Optional[Dict[str, Any]] = None

class UserResponse(UserBase):
    """User response schema"""
    id: UUID
    full_name: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Connection status
    teams_connected: bool = False
    jira_connected: bool = False
    email_connected: bool = False
    
    class Config:
        from_attributes = True

class UserPreferences(BaseModel):
    """User preferences schema"""
    ai_confidence_threshold: float = Field(0.7, ge=0.0, le=1.0)
    auto_approve_high_confidence: bool = True
    teams_sync_interval_hours: int = Field(1, ge=1, le=24)
    email_sync_interval_hours: int = Field(2, ge=1, le=24)
    jira_sync_interval_hours: int = Field(4, ge=1, le=24)
    default_report_template: Optional[str] = None
    timezone: str = "UTC"
    work_hours_start: str = "09:00"
    work_hours_end: str = "17:00" 