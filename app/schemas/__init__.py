"""
Schemas Package - Daily Logger Assist

Contains all Pydantic schemas for request/response validation.
"""

from .auth import TokenResponse, LoginRequest
from .user import UserCreate, UserResponse, UserUpdate
from .message import MessageCreate, MessageResponse, MessageUpdate
from .work_item import WorkItemCreate, WorkItemResponse, WorkItemUpdate
from .jira_ticket import JIRATicketCreate, JIRATicketResponse, JIRATicketUpdate
from .report import ReportCreate, ReportResponse, ReportUpdate

__all__ = [
    "TokenResponse", "LoginRequest",
    "UserCreate", "UserResponse", "UserUpdate",
    "MessageCreate", "MessageResponse", "MessageUpdate", 
    "WorkItemCreate", "WorkItemResponse", "WorkItemUpdate",
    "JIRATicketCreate", "JIRATicketResponse", "JIRATicketUpdate",
    "ReportCreate", "ReportResponse", "ReportUpdate"
] 