"""
Work Item Model - Daily Logger Assist

Model for storing processed work activities and AI analysis results.
"""

from sqlalchemy import Column, String, Text, Integer, Float, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel

class WorkItem(BaseModel):
    """Work item model for processed activities"""
    __tablename__ = "work_items"
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=True, index=True)
    jira_ticket_id = Column(UUID(as_uuid=True), ForeignKey("jira_tickets.id"), nullable=True, index=True)
    
    # Work description and analysis
    description = Column(Text, nullable=False)
    summary = Column(String(500), nullable=True)  # Brief summary for reports
    category = Column(String(100), nullable=True, index=True)  # Work category
    
    # Time tracking
    time_spent_minutes = Column(Integer, nullable=False, default=0)
    time_estimate_minutes = Column(Integer, nullable=True)  # AI estimated time
    
    # AI analysis results
    confidence_score = Column(Float, nullable=False, default=0.0, index=True)
    ai_analysis = Column(JSON, nullable=True)  # Full AI analysis results
    
    # Processing status
    status = Column(String(50), nullable=False, default="pending", index=True)
    # Status values: pending, approved, rejected, needs_review
    
    # Manual override flags
    manual_override = Column(String(50), nullable=True)  # manual, ai_assisted, auto
    review_notes = Column(Text, nullable=True)  # Human review comments
    
    # Project and task classification
    project_keywords = Column(JSON, nullable=True)  # Extracted keywords
    technical_tags = Column(JSON, nullable=True)    # Technical classification
    
    # Quality metrics
    extraction_quality = Column(Float, nullable=True)  # Quality of info extraction
    match_quality = Column(Float, nullable=True)       # Quality of JIRA matching
    
    # Relationships
    user = relationship("User", back_populates="work_items")
    message = relationship("Message", back_populates="work_items")
    jira_ticket = relationship("JIRATicket", back_populates="work_items")
    
    @property
    def hours_spent(self) -> float:
        """Get time spent in hours"""
        return self.time_spent_minutes / 60.0 if self.time_spent_minutes else 0.0
    
    @property
    def is_high_confidence(self) -> bool:
        """Check if this is a high confidence work item"""
        return self.confidence_score >= 0.8
    
    def __repr__(self):
        return f"<WorkItem(description={self.description[:30]}..., time={self.time_spent_minutes}min, confidence={self.confidence_score})>" 