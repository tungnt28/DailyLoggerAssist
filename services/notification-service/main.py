"""
Notification Service for Daily Logger Assist

Handles email alerts, webhooks, and notifications.
"""

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import sys
import os
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime
from pydantic import BaseModel

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.config.base import BaseConfig
from shared.utils.database import init_database, get_db
from shared.models import User

# Initialize configuration
config = BaseConfig()

# Initialize database
db_manager = init_database(config.DATABASE_URL, "notification-service")
db_manager.create_tables()

# Create FastAPI app
app = FastAPI(
    title="Daily Logger Assist - Notification Service",
    description="Email alerts, webhooks, and notifications",
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
class EmailNotification(BaseModel):
    to_email: str
    subject: str
    body: str
    template: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None

class WebhookNotification(BaseModel):
    url: str
    payload: Dict[str, Any]
    headers: Optional[Dict[str, str]] = None
    method: str = "POST"

class NotificationResponse(BaseModel):
    id: str
    type: str  # "email", "webhook", "in_app"
    status: str  # "pending", "sent", "failed"
    recipient: str
    subject: Optional[str] = None
    created_at: str
    sent_at: Optional[str] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True

class NotificationTemplate(BaseModel):
    name: str
    type: str
    subject: str
    body: str
    variables: List[str]

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

def send_email_notification(notification: EmailNotification) -> bool:
    """Send email notification - mock implementation"""
    # TODO: Implement actual email sending (SMTP, SendGrid, etc.)
    logging.info(f"Sending email to {notification.to_email}: {notification.subject}")
    return True

def send_webhook_notification(notification: WebhookNotification) -> bool:
    """Send webhook notification - mock implementation"""
    # TODO: Implement actual webhook sending
    logging.info(f"Sending webhook to {notification.url}: {notification.payload}")
    return True

def get_notification_template(template_name: str) -> Optional[NotificationTemplate]:
    """Get notification template"""
    # TODO: Implement template management
    templates = {
        "daily_report": NotificationTemplate(
            name="daily_report",
            type="email",
            subject="Daily Report - {date}",
            body="Your daily report is ready. View it at: {report_url}",
            variables=["date", "report_url"]
        ),
        "weekly_summary": NotificationTemplate(
            name="weekly_summary",
            type="email",
            subject="Weekly Summary - {week_start}",
            body="Your weekly summary is available. Total hours: {total_hours}",
            variables=["week_start", "total_hours"]
        ),
        "sync_error": NotificationTemplate(
            name="sync_error",
            type="email",
            subject="Data Sync Error - {source}",
            body="There was an error syncing data from {source}. Error: {error}",
            variables=["source", "error"]
        )
    }
    return templates.get(template_name)

# Endpoints

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_healthy = db_manager.health_check()
    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "service": "Notification Service",
        "version": "1.0.0",
        "database": "healthy" if db_healthy else "unhealthy"
    }

@app.post("/api/v1/notifications/email", response_model=NotificationResponse)
async def send_email(
    notification: EmailNotification,
    current_user: User = Depends(get_current_user_from_header)
):
    """Send email notification"""
    try:
        # Generate notification ID
        notification_id = f"email_{datetime.utcnow().timestamp()}"
        
        # Send email
        success = send_email_notification(notification)
        
        # Create response
        response = NotificationResponse(
            id=notification_id,
            type="email",
            status="sent" if success else "failed",
            recipient=notification.to_email,
            subject=notification.subject,
            created_at=datetime.utcnow().isoformat(),
            sent_at=datetime.utcnow().isoformat() if success else None,
            error_message=None if success else "Failed to send email"
        )
        
        return response
        
    except Exception as e:
        logging.error(f"Failed to send email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send email"
        )

@app.post("/api/v1/notifications/webhook", response_model=NotificationResponse)
async def send_webhook(
    notification: WebhookNotification,
    current_user: User = Depends(get_current_user_from_header)
):
    """Send webhook notification"""
    try:
        # Generate notification ID
        notification_id = f"webhook_{datetime.utcnow().timestamp()}"
        
        # Send webhook
        success = send_webhook_notification(notification)
        
        # Create response
        response = NotificationResponse(
            id=notification_id,
            type="webhook",
            status="sent" if success else "failed",
            recipient=notification.url,
            created_at=datetime.utcnow().isoformat(),
            sent_at=datetime.utcnow().isoformat() if success else None,
            error_message=None if success else "Failed to send webhook"
        )
        
        return response
        
    except Exception as e:
        logging.error(f"Failed to send webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send webhook"
        )

@app.post("/api/v1/notifications/template/{template_name}")
async def send_template_notification(
    template_name: str,
    variables: Dict[str, Any],
    recipient: str,
    current_user: User = Depends(get_current_user_from_header)
):
    """Send notification using a template"""
    try:
        # Get template
        template = get_notification_template(template_name)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template '{template_name}' not found"
            )
        
        # Validate variables
        missing_vars = [var for var in template.variables if var not in variables]
        if missing_vars:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required variables: {missing_vars}"
            )
        
        # Format template
        subject = template.subject.format(**variables)
        body = template.body.format(**variables)
        
        # Send notification based on type
        if template.type == "email":
            notification = EmailNotification(
                to_email=recipient,
                subject=subject,
                body=body
            )
            return await send_email(notification, current_user)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported template type: {template.type}"
            )
        
    except Exception as e:
        logging.error(f"Failed to send template notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send template notification"
        )

@app.get("/api/v1/notifications/templates", response_model=List[NotificationTemplate])
async def get_templates(
    current_user: User = Depends(get_current_user_from_header)
):
    """Get available notification templates"""
    templates = [
        get_notification_template("daily_report"),
        get_notification_template("weekly_summary"),
        get_notification_template("sync_error")
    ]
    return [t for t in templates if t is not None]

@app.get("/api/v1/notifications/history", response_model=List[NotificationResponse])
async def get_notification_history(
    notification_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user_from_header)
):
    """Get notification history for the current user"""
    # TODO: Implement actual notification history storage
    # For now, return mock data
    mock_history = [
        NotificationResponse(
            id="email_123",
            type="email",
            status="sent",
            recipient=current_user.email,
            subject="Daily Report - 2025-01-08",
            created_at="2025-01-08T10:00:00Z",
            sent_at="2025-01-08T10:00:01Z"
        ),
        NotificationResponse(
            id="webhook_456",
            type="webhook",
            status="sent",
            recipient="https://api.example.com/webhook",
            created_at="2025-01-08T09:30:00Z",
            sent_at="2025-01-08T09:30:01Z"
        )
    ]
    
    if notification_type:
        mock_history = [n for n in mock_history if n.type == notification_type]
    
    if status:
        mock_history = [n for n in mock_history if n.status == status]
    
    return mock_history[:limit]

@app.post("/api/v1/notifications/bulk")
async def send_bulk_notifications(
    notifications: List[Dict[str, Any]],
    current_user: User = Depends(get_current_user_from_header)
):
    """Send multiple notifications in bulk"""
    try:
        results = []
        
        for notification_data in notifications:
            notification_type = notification_data.get("type")
            
            if notification_type == "email":
                notification = EmailNotification(**notification_data)
                result = await send_email(notification, current_user)
            elif notification_type == "webhook":
                notification = WebhookNotification(**notification_data)
                result = await send_webhook(notification, current_user)
            else:
                result = NotificationResponse(
                    id=f"error_{datetime.utcnow().timestamp()}",
                    type=notification_type or "unknown",
                    status="failed",
                    recipient="unknown",
                    created_at=datetime.utcnow().isoformat(),
                    error_message=f"Unsupported notification type: {notification_type}"
                )
            
            results.append(result)
        
        return {
            "total": len(notifications),
            "successful": len([r for r in results if r.status == "sent"]),
            "failed": len([r for r in results if r.status == "failed"]),
            "results": results
        }
        
    except Exception as e:
        logging.error(f"Failed to send bulk notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send bulk notifications"
        )

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Application startup tasks"""
    logging.info("Notification Service starting...")
    logging.info(f"Environment: {config.ENVIRONMENT}")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks"""
    logging.info("Notification Service shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8005,
        reload=True
    ) 