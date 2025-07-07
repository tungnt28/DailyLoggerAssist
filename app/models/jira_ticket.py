"""
JIRA Ticket Model - Daily Logger Assist

Model for storing JIRA ticket information and metadata.
"""

from sqlalchemy import Column, String, Text, ForeignKey, JSON, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel

class JIRATicket(BaseModel):
    """JIRA ticket model"""
    __tablename__ = "jira_tickets"
    
    # Foreign key to user
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # JIRA ticket identification
    ticket_key = Column(String(50), nullable=False, index=True)  # e.g., "PROJ-123"
    ticket_id = Column(String(50), nullable=True)  # Internal JIRA ID
    
    # Ticket details
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(100), nullable=False, index=True)
    priority = Column(String(50), nullable=True)
    
    # Assignment and project info
    assignee = Column(String(255), nullable=True)
    reporter = Column(String(255), nullable=True)
    project = Column(String(100), nullable=False, index=True)
    project_key = Column(String(20), nullable=False)
    
    # Categorization
    issue_type = Column(String(50), nullable=True)
    labels = Column(JSON, nullable=True)  # List of labels
    components = Column(JSON, nullable=True)  # List of components
    
    # Timestamps
    jira_created_at = Column(DateTime(timezone=True), nullable=True)
    jira_updated_at = Column(DateTime(timezone=True), nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=True)
    
    # Estimated and logged time (in minutes)
    time_estimate = Column(String(50), nullable=True)  # Original estimate
    time_spent = Column(String(50), nullable=True)     # Time already logged
    
    # Sync status
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    sync_error = Column(Text, nullable=True)
    
    # Additional metadata
    ticket_metadata = Column(JSON, nullable=True)  # JIRA-specific metadata
    
    # Relationships
    user = relationship("User", back_populates="jira_tickets")
    work_items = relationship("WorkItem", back_populates="jira_ticket", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<JIRATicket(key={self.ticket_key}, title={self.title[:50]}, status={self.status})>" 