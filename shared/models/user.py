"""
User Model - Daily Logger Assist

User model for authentication and credential management.
"""

from sqlalchemy import Column, String, JSON, Boolean
from sqlalchemy.orm import relationship
from .base import BaseModel

class User(BaseModel):
    """User model"""
    __tablename__ = "users"
    
    # Basic user information
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Encrypted credentials for external services
    teams_credentials = Column(JSON, nullable=True)  # Encrypted Teams OAuth tokens
    jira_credentials = Column(JSON, nullable=True)   # Encrypted JIRA credentials
    email_credentials = Column(JSON, nullable=True)  # Encrypted email credentials
    
    # User preferences
    preferences = Column(JSON, nullable=True)
    
    # Relationships
    messages = relationship("Message", back_populates="user", cascade="all, delete-orphan")
    work_items = relationship("WorkItem", back_populates="user", cascade="all, delete-orphan")
    jira_tickets = relationship("JIRATicket", back_populates="user", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")
    
    @property
    def full_name(self) -> str:
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self):
        return f"<User(email={self.email}, name={self.full_name})>" 