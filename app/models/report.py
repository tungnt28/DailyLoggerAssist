"""
Report Model - Daily Logger Assist

Model for storing generated reports and JIRA updates.
"""

from sqlalchemy import Column, String, Text, Date, ForeignKey, JSON, Integer, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel

class Report(BaseModel):
    """Report model for daily/weekly summaries"""
    __tablename__ = "reports"
    
    # Foreign key to user
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Report identification
    report_type = Column(String(20), nullable=False, index=True)  # 'daily', 'weekly'
    report_date = Column(Date, nullable=False, index=True)  # Date for daily, start date for weekly
    week_start_date = Column(Date, nullable=True)  # For weekly reports
    
    # Report content
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)  # Formatted report content
    raw_content = Column(JSON, nullable=True)  # Structured data
    
    # Summary statistics
    total_time_minutes = Column(Integer, nullable=False, default=0)
    total_work_items = Column(Integer, nullable=False, default=0)
    high_confidence_items = Column(Integer, nullable=False, default=0)
    
    # JIRA integration
    jira_updates = Column(JSON, nullable=True)  # List of JIRA updates made
    jira_update_status = Column(String(50), nullable=True)  # Status of JIRA updates
    jira_update_error = Column(Text, nullable=True)  # Error message if updates failed
    
    # Report generation metadata
    generation_method = Column(String(50), nullable=False, default="ai")  # 'ai', 'manual', 'hybrid'
    template_used = Column(String(100), nullable=True)  # Template identifier
    ai_model_used = Column(String(100), nullable=True)  # AI model used for generation
    
    # Status and approval
    status = Column(String(50), nullable=False, default="draft", index=True)
    # Status values: draft, approved, sent_to_jira, archived
    
    approved_by = Column(String(255), nullable=True)  # Who approved the report
    approval_notes = Column(Text, nullable=True)  # Approval/rejection notes
    
    # Quality metrics
    report_quality_score = Column(Float, nullable=True)  # Overall quality assessment
    completeness_score = Column(Float, nullable=True)   # How complete the report is
    
    # Relationships
    user = relationship("User", back_populates="reports")
    
    @property
    def total_hours(self) -> float:
        """Get total time in hours"""
        return self.total_time_minutes / 60.0 if self.total_time_minutes else 0.0
    
    @property
    def confidence_percentage(self) -> float:
        """Get percentage of high confidence items"""
        if self.total_work_items == 0:
            return 0.0
        return (self.high_confidence_items / self.total_work_items) * 100
    
    def __repr__(self):
        return f"<Report(type={self.report_type}, date={self.report_date}, status={self.status}, items={self.total_work_items})>" 