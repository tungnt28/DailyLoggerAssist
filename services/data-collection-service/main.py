"""
Data Collection Service for Daily Logger Assist

Handles data collection from Microsoft Teams, Email, and JIRA.
"""

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import sys
import os
from typing import List, Optional
import logging
from datetime import datetime, timedelta
from pydantic import BaseModel

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.config.base import BaseConfig
from shared.utils.database import init_database, get_db
from shared.models import Message, JIRATicket, User

# Initialize configuration
config = BaseConfig()

# Initialize database
db_manager = init_database(config.DATABASE_URL, "data-collection-service")
db_manager.create_tables()

# Create FastAPI app
app = FastAPI(
    title="Daily Logger Assist - Data Collection Service",
    description="Data collection from Teams, Email, and JIRA",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS if config.ENVIRONMENT == "production" else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Pydantic models
class MessageResponse(BaseModel):
    id: str
    user_id: str
    source: str
    content: str
    sender: str
    timestamp: str
    metadata: dict
    created_at: str

    class Config:
        from_attributes = True

class JIRATicketResponse(BaseModel):
    id: str
    user_id: str
    ticket_key: str
    summary: str
    description: str
    status: str
    priority: str
    assignee: str
    project: str
    created_at: str
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True

class SyncRequest(BaseModel):
    source: str  # "teams", "email", "jira"
    since: Optional[datetime] = None
    force: bool = False

class SyncResponse(BaseModel):
    source: str
    status: str
    items_collected: int
    errors: List[str] = []
    timestamp: str

# Helper functions
def get_current_user_from_header(request: Request, db: Session = Depends(get_db)) -> User:
    """Get current user from X-User-ID header (set by gateway)"""
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID header missing"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

def get_messages_by_user(db: Session, user_id: str, source: Optional[str] = None, 
                        since: Optional[datetime] = None, limit: int = 100) -> List[Message]:
    """Get messages for a user with optional filtering"""
    query = db.query(Message).filter(Message.user_id == user_id)
    
    if source:
        query = query.filter(Message.source == source)
    
    if since:
        query = query.filter(Message.timestamp >= since)
    
    return query.order_by(Message.timestamp.desc()).limit(limit).all()

def get_jira_tickets_by_user(db: Session, user_id: str, status: Optional[str] = None,
                            project: Optional[str] = None) -> List[JIRATicket]:
    """Get JIRA tickets for a user with optional filtering"""
    query = db.query(JIRATicket).filter(JIRATicket.user_id == user_id)
    
    if status:
        query = query.filter(JIRATicket.status == status)
    
    if project:
        query = query.filter(JIRATicket.project == project)
    
    return query.order_by(JIRATicket.updated_at.desc()).all()

# Endpoints

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_healthy = db_manager.health_check()
    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "service": "Data Collection Service",
        "version": "1.0.0",
        "database": "healthy" if db_healthy else "unhealthy"
    }

@app.get("/api/v1/data/messages", response_model=List[MessageResponse])
async def get_messages(
    source: Optional[str] = None,
    since: Optional[datetime] = None,
    limit: int = 100,
    current_user: User = Depends(get_current_user_from_header),
    db: Session = Depends(get_db)
):
    """Get messages for the current user"""
    messages = get_messages_by_user(
        db, 
        str(current_user.id), 
        source, 
        since, 
        limit
    )
    return [MessageResponse.from_orm(msg) for msg in messages]

@app.get("/api/v1/data/messages/{message_id}", response_model=MessageResponse)
async def get_message(
    message_id: str,
    current_user: User = Depends(get_current_user_from_header),
    db: Session = Depends(get_db)
):
    """Get a specific message by ID"""
    message = db.query(Message).filter(
        Message.id == message_id,
        Message.user_id == str(current_user.id)
    ).first()
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    return MessageResponse.from_orm(message)

@app.get("/api/v1/data/jira-tickets", response_model=List[JIRATicketResponse])
async def get_jira_tickets(
    status: Optional[str] = None,
    project: Optional[str] = None,
    current_user: User = Depends(get_current_user_from_header),
    db: Session = Depends(get_db)
):
    """Get JIRA tickets for the current user"""
    tickets = get_jira_tickets_by_user(
        db,
        str(current_user.id),
        status,
        project
    )
    return [JIRATicketResponse.from_orm(ticket) for ticket in tickets]

@app.get("/api/v1/data/jira-tickets/{ticket_id}", response_model=JIRATicketResponse)
async def get_jira_ticket(
    ticket_id: str,
    current_user: User = Depends(get_current_user_from_header),
    db: Session = Depends(get_db)
):
    """Get a specific JIRA ticket by ID"""
    ticket = db.query(JIRATicket).filter(
        JIRATicket.id == ticket_id,
        JIRATicket.user_id == str(current_user.id)
    ).first()
    
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="JIRA ticket not found"
        )
    
    return JIRATicketResponse.from_orm(ticket)

@app.post("/api/v1/data/sync", response_model=SyncResponse)
async def sync_data(
    sync_request: SyncRequest,
    current_user: User = Depends(get_current_user_from_header),
    db: Session = Depends(get_db)
):
    """Sync data from external sources"""
    try:
        # TODO: Implement actual sync logic for each source
        # For now, return a mock response
        
        if sync_request.source == "teams":
            # Mock Teams sync
            items_collected = 5
            status_msg = "completed"
        elif sync_request.source == "email":
            # Mock Email sync
            items_collected = 3
            status_msg = "completed"
        elif sync_request.source == "jira":
            # Mock JIRA sync
            items_collected = 2
            status_msg = "completed"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported source: {sync_request.source}"
            )
        
        return SyncResponse(
            source=sync_request.source,
            status=status_msg,
            items_collected=items_collected,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logging.error(f"Sync failed for {sync_request.source}: {e}")
        return SyncResponse(
            source=sync_request.source,
            status="failed",
            items_collected=0,
            errors=[str(e)],
            timestamp=datetime.utcnow().isoformat()
        )

@app.get("/api/v1/data/sources")
async def get_available_sources():
    """Get available data sources"""
    return {
        "sources": [
            {
                "name": "teams",
                "display_name": "Microsoft Teams",
                "description": "Messages from Teams channels",
                "enabled": True
            },
            {
                "name": "email",
                "display_name": "Email",
                "description": "Emails from configured folders",
                "enabled": True
            },
            {
                "name": "jira",
                "display_name": "JIRA",
                "description": "JIRA tickets and updates",
                "enabled": True
            }
        ]
    }

@app.get("/api/v1/data/stats")
async def get_data_stats(
    current_user: User = Depends(get_current_user_from_header),
    db: Session = Depends(get_db)
):
    """Get data collection statistics for the user"""
    # Get message counts by source
    teams_count = db.query(Message).filter(
        Message.user_id == str(current_user.id),
        Message.source == "teams"
    ).count()
    
    email_count = db.query(Message).filter(
        Message.user_id == str(current_user.id),
        Message.source == "email"
    ).count()
    
    jira_count = db.query(JIRATicket).filter(
        JIRATicket.user_id == str(current_user.id)
    ).count()
    
    # Get recent activity
    recent_messages = db.query(Message).filter(
        Message.user_id == str(current_user.id),
        Message.timestamp >= datetime.utcnow() - timedelta(days=7)
    ).count()
    
    return {
        "message_counts": {
            "teams": teams_count,
            "email": email_count,
            "jira_tickets": jira_count
        },
        "recent_activity": {
            "messages_last_7_days": recent_messages
        },
        "last_sync": {
            "teams": "2025-01-08T10:00:00Z",
            "email": "2025-01-08T09:30:00Z",
            "jira": "2025-01-08T09:00:00Z"
        }
    }

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Application startup tasks"""
    logging.info("Data Collection Service starting...")
    logging.info(f"Environment: {config.ENVIRONMENT}")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks"""
    logging.info("Data Collection Service shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        reload=True
    ) 