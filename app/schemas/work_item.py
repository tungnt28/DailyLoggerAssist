"""
Work Item Schemas - Daily Logger Assist

Pydantic schemas for work item-related requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

class WorkItemBase(BaseModel):
    """Base work item schema"""
    description: str = Field(..., min_length=1, max_length=2000)
    time_spent_minutes: int = Field(..., ge=0, le=480)  # Max 8 hours
    category: Optional[str] = Field(None, max_length=100)
    summary: Optional[str] = Field(None, max_length=500)

class WorkItemCreate(WorkItemBase):
    """Work item creation schema"""
    message_id: Optional[UUID] = None
    jira_ticket_id: Optional[UUID] = None
    manual_override: Optional[str] = Field(None, pattern="^(manual|ai_assisted|auto)$")
    project_keywords: Optional[List[str]] = None
    technical_tags: Optional[List[str]] = None

class WorkItemUpdate(BaseModel):
    """Work item update schema"""
    description: Optional[str] = Field(None, min_length=1, max_length=2000)
    time_spent_minutes: Optional[int] = Field(None, ge=0, le=480)
    category: Optional[str] = Field(None, max_length=100)
    summary: Optional[str] = Field(None, max_length=500)
    jira_ticket_id: Optional[UUID] = None
    status: Optional[str] = Field(None, pattern="^(pending|approved|rejected|needs_review)$")
    review_notes: Optional[str] = None
    project_keywords: Optional[List[str]] = None
    technical_tags: Optional[List[str]] = None

class WorkItemResponse(WorkItemBase):
    """Work item response schema"""
    id: UUID
    user_id: UUID
    message_id: Optional[UUID] = None
    jira_ticket_id: Optional[UUID] = None
    
    # AI analysis results
    confidence_score: float
    ai_analysis: Optional[Dict[str, Any]] = None
    
    # Processing status
    status: str
    manual_override: Optional[str] = None
    review_notes: Optional[str] = None
    
    # Classification
    project_keywords: List[str] = []
    technical_tags: List[str] = []
    
    # Quality metrics
    extraction_quality: Optional[float] = None
    match_quality: Optional[float] = None
    
    # Time estimates
    time_estimate_minutes: Optional[int] = None
    hours_spent: float
    is_high_confidence: bool
    
    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class WorkItemSummary(BaseModel):
    """Work item summary for reports"""
    id: UUID
    description: str
    summary: Optional[str] = None
    time_spent_minutes: int
    hours_spent: float
    confidence_score: float
    status: str
    jira_ticket_key: Optional[str] = None
    category: Optional[str] = None

class WorkItemBulkProcess(BaseModel):
    """Bulk processing request schema"""
    work_item_ids: List[UUID] = Field(..., min_items=1)
    action: str = Field(..., pattern="^(approve|reject|reprocess)$")
    review_notes: Optional[str] = None

class WorkItemFilter(BaseModel):
    """Work item filtering schema"""
    status: Optional[str] = None
    confidence_min: Optional[float] = Field(None, ge=0.0, le=1.0)
    confidence_max: Optional[float] = Field(None, ge=0.0, le=1.0)
    category: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    has_jira_ticket: Optional[bool] = None
    project_keyword: Optional[str] = None 