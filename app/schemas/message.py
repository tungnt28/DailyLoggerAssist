"""
Message Schemas - Daily Logger Assist

Pydantic schemas for message-related requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

class MessageBase(BaseModel):
    """Base message schema"""
    content: str = Field(..., min_length=1)
    sender: str = Field(..., min_length=1, max_length=255)
    subject: Optional[str] = Field(None, max_length=500)
    source: str = Field(..., pattern="^(teams|email|manual)$")

class MessageCreate(MessageBase):
    """Message creation schema"""
    channel_id: Optional[str] = Field(None, max_length=255)
    thread_id: Optional[str] = Field(None, max_length=255)
    external_id: Optional[str] = Field(None, max_length=255)
    message_timestamp: datetime
    message_metadata: Optional[Dict[str, Any]] = None

class MessageUpdate(BaseModel):
    """Message update schema"""
    content: Optional[str] = Field(None, min_length=1)
    processed: Optional[bool] = None
    processing_error: Optional[str] = None

class MessageResponse(MessageBase):
    """Message response schema"""
    id: UUID
    user_id: UUID
    channel_id: Optional[str] = None
    thread_id: Optional[str] = None
    external_id: Optional[str] = None
    message_timestamp: datetime
    processed: bool
    processing_error: Optional[str] = None
    message_metadata: Dict[str, Any] = {}
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True 