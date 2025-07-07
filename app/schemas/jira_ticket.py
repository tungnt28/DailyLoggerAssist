"""
JIRA Ticket Schemas - Daily Logger Assist

Pydantic schemas for JIRA ticket-related requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

class JIRATicketBase(BaseModel):
    """Base JIRA ticket schema"""
    ticket_key: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=1, max_length=500)
    status: str = Field(..., min_length=1, max_length=100)
    project: str = Field(..., min_length=1, max_length=100)
    project_key: str = Field(..., min_length=1, max_length=20)

class JIRATicketCreate(JIRATicketBase):
    """JIRA ticket creation schema"""
    ticket_id: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    priority: Optional[str] = Field(None, max_length=50)
    assignee: Optional[str] = Field(None, max_length=255)
    reporter: Optional[str] = Field(None, max_length=255)
    issue_type: Optional[str] = Field(None, max_length=50)
    labels: Optional[List[str]] = None
    components: Optional[List[str]] = None
    jira_created_at: Optional[datetime] = None
    jira_updated_at: Optional[datetime] = None
    due_date: Optional[datetime] = None
    time_estimate: Optional[str] = Field(None, max_length=50)
    time_spent: Optional[str] = Field(None, max_length=50)
    ticket_metadata: Optional[Dict[str, Any]] = None

class JIRATicketUpdate(BaseModel):
    """JIRA ticket update schema"""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    status: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    priority: Optional[str] = Field(None, max_length=50)
    assignee: Optional[str] = Field(None, max_length=255)
    labels: Optional[List[str]] = None
    components: Optional[List[str]] = None
    jira_updated_at: Optional[datetime] = None
    due_date: Optional[datetime] = None
    time_estimate: Optional[str] = Field(None, max_length=50)
    time_spent: Optional[str] = Field(None, max_length=50)
    last_sync_at: Optional[datetime] = None
    sync_error: Optional[str] = None

class JIRATicketResponse(JIRATicketBase):
    """JIRA ticket response schema"""
    id: UUID
    user_id: UUID
    ticket_id: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    assignee: Optional[str] = None
    reporter: Optional[str] = None
    issue_type: Optional[str] = None
    labels: List[str] = []
    components: List[str] = []
    jira_created_at: Optional[datetime] = None
    jira_updated_at: Optional[datetime] = None
    due_date: Optional[datetime] = None
    time_estimate: Optional[str] = None
    time_spent: Optional[str] = None
    last_sync_at: Optional[datetime] = None
    sync_error: Optional[str] = None
    ticket_metadata: Dict[str, Any] = {}
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True 