"""
Message Model - Daily Logger Assist

Model for storing messages from Teams, email, and other sources.
"""

from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel

class Message(BaseModel):
    """Message model for communications"""
    __tablename__ = "messages"
    
    # Foreign key to user
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Message source and identification
    source = Column(String(50), nullable=False, index=True)  # 'teams', 'email', 'manual'
    channel_id = Column(String(255), nullable=True, index=True)  # Teams channel or email folder
    thread_id = Column(String(255), nullable=True)  # Message thread identifier
    external_id = Column(String(255), nullable=True, index=True)  # External system message ID
    
    # Message content
    content = Column(Text, nullable=False)
    sender = Column(String(255), nullable=False)
    subject = Column(String(500), nullable=True)  # Email subject or Teams message title
    
    # Timestamps
    message_timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Processing status
    processed = Column(Boolean, default=False, nullable=False, index=True)
    processing_error = Column(Text, nullable=True)
    
    # Metadata storage
    message_metadata = Column(JSON, nullable=True)  # Source-specific metadata
    
    # Relationships
    user = relationship("User", back_populates="messages")
    work_items = relationship("WorkItem", back_populates="message", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Message(source={self.source}, sender={self.sender}, processed={self.processed})>" 