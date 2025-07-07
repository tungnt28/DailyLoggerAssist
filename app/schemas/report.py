"""
Report Schemas - Daily Logger Assist

Pydantic schemas for report-related requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID

class ReportBase(BaseModel):
    """Base report schema"""
    title: str = Field(..., min_length=1, max_length=200)
    report_type: str = Field(..., pattern="^(daily|weekly)$")
    report_date: date

class ReportCreate(ReportBase):
    """Report creation schema"""
    week_start_date: Optional[date] = None
    content: str = Field(..., min_length=1)
    raw_content: Optional[Dict[str, Any]] = None
    generation_method: str = Field("ai", pattern="^(ai|manual|hybrid)$")
    template_used: Optional[str] = Field(None, max_length=100)
    ai_model_used: Optional[str] = Field(None, max_length=100)

class ReportUpdate(BaseModel):
    """Report update schema"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    status: Optional[str] = Field(None, pattern="^(draft|approved|sent_to_jira|archived)$")
    approved_by: Optional[str] = Field(None, max_length=255)
    approval_notes: Optional[str] = None
    jira_update_status: Optional[str] = Field(None, max_length=50)
    jira_update_error: Optional[str] = None

class ReportResponse(ReportBase):
    """Report response schema"""
    id: UUID
    user_id: UUID
    week_start_date: Optional[date] = None
    content: str
    raw_content: Optional[Dict[str, Any]] = None
    
    # Summary statistics
    total_time_minutes: int
    total_work_items: int
    high_confidence_items: int
    total_hours: float
    confidence_percentage: float
    
    # JIRA integration
    jira_updates: List[Dict[str, Any]] = []
    jira_update_status: Optional[str] = None
    jira_update_error: Optional[str] = None
    
    # Report generation metadata
    generation_method: str
    template_used: Optional[str] = None
    ai_model_used: Optional[str] = None
    
    # Status and approval
    status: str
    approved_by: Optional[str] = None
    approval_notes: Optional[str] = None
    
    # Quality metrics
    report_quality_score: Optional[float] = None
    completeness_score: Optional[float] = None
    
    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ReportGenerate(BaseModel):
    """Report generation request schema"""
    report_type: str = Field(..., pattern="^(daily|weekly)$")
    report_date: date
    week_start_date: Optional[date] = None
    template: Optional[str] = None
    auto_approve: bool = False
    send_to_jira: bool = False

class ReportSummary(BaseModel):
    """Report summary for listing"""
    id: UUID
    title: str
    report_type: str
    report_date: date
    status: str
    total_hours: float
    total_work_items: int
    confidence_percentage: float
    created_at: datetime 