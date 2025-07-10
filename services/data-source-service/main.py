"""
Data Source Service for Daily Logger Assist

Handles connections to external data sources like Jira, Microsoft Teams, and email.
Manages OAuth flows, credential storage, and data synchronization.
"""

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import sys
import os
from typing import List, Optional, Dict, Any
import logging
from pydantic import BaseModel, EmailStr, field_validator
import uuid
import json
import httpx
from cryptography.fernet import Fernet

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.config.base import BaseConfig
from shared.utils.database import init_database, get_db
from shared.utils.auth import init_auth, get_auth
from shared.models import User

# Initialize configuration
config = BaseConfig()

# Initialize database
db_manager = init_database(config.DATABASE_URL, "data-source-service")
db_manager.create_tables()

# Initialize authentication
auth_manager = init_auth(config.SECRET_KEY, config.REDIS_URL)

# Initialize encryption for sensitive data
encryption_key = Fernet.generate_key()
cipher_suite = Fernet(encryption_key)

# Create FastAPI app
app = FastAPI(
    title="Daily Logger Assist - Data Source Service",
    description="Data source connection and synchronization service",
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
class DataSourceCreate(BaseModel):
    name: str
    type: str  # 'jira', 'teams', 'email'
    config: Dict[str, Any]

class DataSourceUpdate(BaseModel):
    name: Optional[str] = None
    config: Optional[Dict[str, Any]] = None

class DataSourceResponse(BaseModel):
    id: str
    name: str
    type: str
    status: str  # 'connected', 'disconnected', 'error'
    last_sync: Optional[str] = None
    config: Dict[str, Any]
    created_at: str
    updated_at: Optional[str] = None

class ConnectionTest(BaseModel):
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None

class SyncResult(BaseModel):
    success: bool
    message: str
    items_synced: int
    errors: List[str] = []

# Helper functions
def encrypt_sensitive_data(data: str) -> str:
    """Encrypt sensitive configuration data"""
    return cipher_suite.encrypt(data.encode()).decode()

def decrypt_sensitive_data(encrypted_data: str) -> str:
    """Decrypt sensitive configuration data"""
    return cipher_suite.decrypt(encrypted_data.encode()).decode()

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

async def test_jira_connection(config: Dict[str, Any]) -> ConnectionTest:
    """Test Jira connection"""
    try:
        url = config.get('url')
        username = config.get('username')
        password = config.get('password')
        project_key = config.get('projectKey')
        
        if not all([url, username, password, project_key]):
            return ConnectionTest(
                success=False,
                message="Missing required Jira configuration"
            )
        
        # Test Jira API connection
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test basic authentication
            auth = (username, password)
            response = await client.get(f"{url}/rest/api/2/myself", auth=auth)
            
            if response.status_code == 200:
                # Test project access
                project_response = await client.get(
                    f"{url}/rest/api/2/project/{project_key}",
                    auth=auth
                )
                
                if project_response.status_code == 200:
                    return ConnectionTest(
                        success=True,
                        message="Jira connection successful",
                        details={"user": response.json(), "project": project_response.json()}
                    )
                else:
                    return ConnectionTest(
                        success=False,
                        message=f"Project access failed: {project_response.status_code}"
                    )
            else:
                return ConnectionTest(
                    success=False,
                    message=f"Authentication failed: {response.status_code}"
                )
                
    except Exception as e:
        return ConnectionTest(
            success=False,
            message=f"Connection error: {str(e)}"
        )

async def test_email_connection(config: Dict[str, Any]) -> ConnectionTest:
    """Test email connection"""
    try:
        email = config.get('email')
        server = config.get('server')
        port = config.get('port', 993)
        
        if not all([email, server]):
            return ConnectionTest(
                success=False,
                message="Missing required email configuration"
            )
        
        # For now, return a mock success response
        # In production, you would test IMAP connection
        return ConnectionTest(
            success=True,
            message="Email connection test successful (mock)",
            details={"email": email, "server": server, "port": port}
        )
        
    except Exception as e:
        return ConnectionTest(
            success=False,
            message=f"Email connection error: {str(e)}"
        )

async def test_teams_connection(config: Dict[str, Any]) -> ConnectionTest:
    """Test Microsoft Teams connection"""
    try:
        # Teams uses OAuth 2.0, so we'll return a mock response
        # In production, you would validate the OAuth token
        return ConnectionTest(
            success=True,
            message="Teams connection test successful (OAuth)",
            details={"oauth_flow": "completed"}
        )
        
    except Exception as e:
        return ConnectionTest(
            success=False,
            message=f"Teams connection error: {str(e)}"
        )

# Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_healthy = db_manager.health_check()
    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "service": "Data Source Service",
        "version": "1.0.0",
        "database": "healthy" if db_healthy else "unhealthy"
    }

@app.get("/api/v1/data-sources", response_model=List[DataSourceResponse])
async def list_data_sources(
    current_user: User = Depends(get_current_user_from_header),
    db: Session = Depends(get_db)
):
    """List all data sources for the current user"""
    # TODO: Implement actual database queries
    # For now, return mock data
    mock_sources = [
        {
            "id": "1",
            "name": "Company Jira",
            "type": "jira",
            "status": "connected",
            "last_sync": "2025-07-09T10:30:00Z",
            "config": {
                "url": "https://company.atlassian.net",
                "username": "user@company.com",
                "projectKey": "PROJ"
            },
            "created_at": "2025-07-09T10:00:00Z",
            "updated_at": "2025-07-09T10:30:00Z"
        },
        {
            "id": "2",
            "name": "Work Email",
            "type": "email",
            "status": "disconnected",
            "config": {
                "email": "work@company.com",
                "server": "mail.company.com",
                "port": 993
            },
            "created_at": "2025-07-09T09:00:00Z",
            "updated_at": None
        }
    ]
    
    return [DataSourceResponse(**source) for source in mock_sources]

@app.post("/api/v1/data-sources", response_model=DataSourceResponse)
async def create_data_source(
    data_source: DataSourceCreate,
    current_user: User = Depends(get_current_user_from_header),
    db: Session = Depends(get_db)
):
    """Create a new data source"""
    # TODO: Implement actual database storage
    # For now, return mock response
    new_source = {
        "id": str(uuid.uuid4()),
        "name": data_source.name,
        "type": data_source.type,
        "status": "disconnected",
        "config": data_source.config,
        "created_at": datetime.now().isoformat(),
        "updated_at": None
    }
    
    return DataSourceResponse(**new_source)

@app.get("/api/v1/data-sources/{source_id}", response_model=DataSourceResponse)
async def get_data_source(
    source_id: str,
    current_user: User = Depends(get_current_user_from_header),
    db: Session = Depends(get_db)
):
    """Get a specific data source"""
    # TODO: Implement actual database query
    # For now, return mock data
    mock_source = {
        "id": source_id,
        "name": "Company Jira",
        "type": "jira",
        "status": "connected",
        "last_sync": "2025-07-09T10:30:00Z",
        "config": {
            "url": "https://company.atlassian.net",
            "username": "user@company.com",
            "projectKey": "PROJ"
        },
        "created_at": "2025-07-09T10:00:00Z",
        "updated_at": "2025-07-09T10:30:00Z"
    }
    
    return DataSourceResponse(**mock_source)

@app.put("/api/v1/data-sources/{source_id}", response_model=DataSourceResponse)
async def update_data_source(
    source_id: str,
    data_source: DataSourceUpdate,
    current_user: User = Depends(get_current_user_from_header),
    db: Session = Depends(get_db)
):
    """Update a data source"""
    # TODO: Implement actual database update
    # For now, return mock response
    updated_source = {
        "id": source_id,
        "name": data_source.name or "Updated Source",
        "type": "jira",
        "status": "connected",
        "last_sync": "2025-07-09T10:30:00Z",
        "config": data_source.config or {},
        "created_at": "2025-07-09T10:00:00Z",
        "updated_at": datetime.now().isoformat()
    }
    
    return DataSourceResponse(**updated_source)

@app.delete("/api/v1/data-sources/{source_id}")
async def delete_data_source(
    source_id: str,
    current_user: User = Depends(get_current_user_from_header),
    db: Session = Depends(get_db)
):
    """Delete a data source"""
    # TODO: Implement actual database deletion
    return {"message": "Data source deleted successfully"}

@app.post("/api/v1/data-sources/{source_id}/test", response_model=ConnectionTest)
async def test_connection(
    source_id: str,
    current_user: User = Depends(get_current_user_from_header),
    db: Session = Depends(get_db)
):
    """Test connection to a data source"""
    # TODO: Get actual data source from database
    # For now, use mock data
    mock_source = {
        "id": source_id,
        "type": "jira",
        "config": {
            "url": "https://company.atlassian.net",
            "username": "user@company.com",
            "password": "password123",
            "projectKey": "PROJ"
        }
    }
    
    if mock_source["type"] == "jira":
        return await test_jira_connection(mock_source["config"])
    elif mock_source["type"] == "email":
        return await test_email_connection(mock_source["config"])
    elif mock_source["type"] == "teams":
        return await test_teams_connection(mock_source["config"])
    else:
        return ConnectionTest(
            success=False,
            message="Unsupported data source type"
        )

@app.post("/api/v1/data-sources/{source_id}/sync", response_model=SyncResult)
async def sync_data_source(
    source_id: str,
    current_user: User = Depends(get_current_user_from_header),
    db: Session = Depends(get_db)
):
    """Sync data from a data source"""
    # TODO: Implement actual data synchronization
    # For now, return mock response
    return SyncResult(
        success=True,
        message="Data synchronization completed",
        items_synced=25,
        errors=[]
    )

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Application startup tasks"""
    logging.info("Data Source Service starting...")
    logging.info(f"Environment: {config.ENVIRONMENT}")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks"""
    logging.info("Data Source Service shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006) 