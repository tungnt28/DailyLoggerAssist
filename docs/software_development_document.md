# Software Development Document
## Daily Logger Assist Application

**Version:** 1.0  
**Date:** December 2024  
**Status:** Draft  

---

## Table of Contents

1. [Development Environment Setup](#1-development-environment-setup)
2. [Project Structure](#2-project-structure)
3. [Development Guidelines](#3-development-guidelines)
4. [Implementation Phases](#4-implementation-phases)
5. [API Development Guide](#5-api-development-guide)
6. [Database Development](#6-database-development)
7. [AI Integration Guide](#7-ai-integration-guide)
8. [Testing Guidelines](#8-testing-guidelines)
9. [Deployment Guide](#9-deployment-guide)
10. [Maintenance Procedures](#10-maintenance-procedures)

---

## 1. Development Environment Setup

### 1.1 Prerequisites

**System Requirements:**
- Python 3.11 or higher
- Redis Server 6.0+
- Git
- Docker (optional, for containerized development)

**Required Tools:**
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install development tools
pip install pre-commit black flake8 mypy

# Setup pre-commit hooks
pre-commit install
```

### 1.2 Environment Configuration

**Step 1: Clone and Setup**
```bash
git clone <repository-url>
cd DailyLoggerAssist
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Step 2: Environment Variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

**Step 3: Database Setup**
```bash
# Initialize database
python scripts/setup_db.py

# Run migrations
alembic upgrade head
```

**Step 4: Start Development Server**
```bash
# Start Redis (if not running)
redis-server

# Start Celery worker (separate terminal)
celery -A app.core.celery_app worker --loglevel=info

# Start FastAPI development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 1.3 IDE Configuration

**VS Code Settings (`.vscode/settings.json`):**
```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.sortImports.args": ["--profile", "black"],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

---

## 2. Project Structure

### 2.1 Directory Organization

```
daily_logger_assist/
├── app/                           # Main application package
│   ├── __init__.py
│   ├── main.py                    # FastAPI entry point
│   ├── config.py                  # Configuration management
│   ├── dependencies.py            # FastAPI dependencies
│   │
│   ├── api/                       # API route handlers
│   │   ├── __init__.py
│   │   ├── auth.py                # Authentication endpoints
│   │   ├── data.py                # Data management endpoints
│   │   ├── reports.py             # Reporting endpoints
│   │   └── admin.py               # Administration endpoints
│   │
│   ├── core/                      # Core business logic
│   │   ├── __init__.py
│   │   ├── collectors/            # Data collection modules
│   │   │   ├── __init__.py
│   │   │   ├── teams.py           # Microsoft Teams collector
│   │   │   ├── email.py           # Email collector
│   │   │   └── jira.py            # JIRA collector
│   │   ├── processors/            # AI processing modules
│   │   │   ├── __init__.py
│   │   │   ├── ai_engine.py       # Main AI processing
│   │   │   ├── matcher.py         # Task matching logic
│   │   │   └── summarizer.py      # Report summarization
│   │   └── generators/            # Report generators
│   │       ├── __init__.py
│   │       ├── daily_report.py    # Daily report generation
│   │       └── weekly_report.py   # Weekly report generation
│   │
│   ├── models/                    # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── base.py                # Base model class
│   │   ├── user.py                # User model
│   │   ├── message.py             # Message model
│   │   ├── work_item.py           # Work item model
│   │   └── report.py              # Report model
│   │
│   ├── schemas/                   # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── auth.py                # Authentication schemas
│   │   ├── work_item.py           # Work item schemas
│   │   └── report.py              # Report schemas
│   │
│   ├── services/                  # External service integrations
│   │   ├── __init__.py
│   │   ├── teams_service.py       # Teams API integration
│   │   ├── email_service.py       # Email API integration
│   │   ├── jira_service.py        # JIRA API integration
│   │   └── ai_service.py          # OpenRoute AI integration
│   │
│   ├── utils/                     # Utility functions
│   │   ├── __init__.py
│   │   ├── auth.py                # Authentication utilities
│   │   ├── text_processing.py     # Text processing utilities
│   │   └── time_utils.py          # Time handling utilities
│   │
│   └── database/                  # Database configuration
│       ├── __init__.py
│       ├── connection.py          # Database connection
│       └── migrations/            # Alembic migrations
│
├── tests/                         # Test files
│   ├── __init__.py
│   ├── conftest.py               # Test configuration
│   ├── test_api/                 # API tests
│   ├── test_core/                # Core logic tests
│   └── test_services/            # Service tests
│
├── scripts/                       # Utility scripts
│   ├── setup_db.py               # Database setup
│   ├── collect_data.py           # Data collection script
│   └── generate_reports.py       # Report generation script
│
├── docs/                          # Documentation
├── logs/                          # Log files
├── .env.example                   # Environment template
├── requirements.txt               # Dependencies
├── docker-compose.yml             # Docker setup
├── Dockerfile                     # Docker configuration
└── README.md                      # Project README
```

### 2.2 File Naming Conventions

- **Python files**: snake_case (e.g., `teams_collector.py`)
- **Classes**: PascalCase (e.g., `TeamsCollector`)
- **Functions/variables**: snake_case (e.g., `collect_messages`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_RETRY_ATTEMPTS`)
- **Environment variables**: UPPER_SNAKE_CASE (e.g., `DATABASE_URL`)

---

## 3. Development Guidelines

### 3.1 Code Style

**Python Style Guide:**
- Follow PEP 8 standards
- Use Black for code formatting
- Use isort for import sorting
- Use type hints for all functions
- Maximum line length: 88 characters

**Example Code Style:**
```python
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

class WorkItem(BaseModel):
    """Work item representation"""
    
    id: Optional[int] = None
    description: str
    time_spent_minutes: int
    confidence_score: float
    created_at: datetime
    
    class Config:
        from_attributes = True

async def process_work_items(
    items: List[WorkItem], 
    confidence_threshold: float = 0.7
) -> List[WorkItem]:
    """
    Process work items with confidence filtering.
    
    Args:
        items: List of work items to process
        confidence_threshold: Minimum confidence score
        
    Returns:
        Filtered list of processed work items
    """
    processed_items = []
    
    for item in items:
        if item.confidence_score >= confidence_threshold:
            # Process high-confidence items
            processed_item = await ai_service.enhance_item(item)
            processed_items.append(processed_item)
    
    return processed_items
```

### 3.2 Error Handling Standards

**Exception Hierarchy:**
```python
class DailyLoggerException(Exception):
    """Base exception for Daily Logger Assist"""
    pass

class ValidationError(DailyLoggerException):
    """Validation error"""
    pass

class ExternalServiceError(DailyLoggerException):
    """External service integration error"""
    pass

class AIProcessingError(DailyLoggerException):
    """AI processing error"""
    pass
```

**Error Handling Pattern:**
```python
from loguru import logger

async def risky_operation():
    try:
        result = await external_service.call()
        return result
    except ExternalServiceError as e:
        logger.error(f"External service failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise DailyLoggerException(f"Operation failed: {e}")
```

### 3.3 Logging Standards

**Logging Configuration:**
```python
from loguru import logger
import sys

# Configure logger
logger.remove()
logger.add(
    sys.stdout,
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
)
logger.add(
    "logs/app.log",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
    rotation="10 MB",
    retention="30 days"
)
```

**Logging Usage:**
```python
@logger.catch
async def collect_teams_messages(user_id: str) -> List[Message]:
    """Collect messages from Teams"""
    logger.info(f"Starting Teams collection for user {user_id}")
    
    try:
        messages = await teams_service.get_messages(user_id)
        logger.info(f"Collected {len(messages)} messages")
        return messages
    except Exception as e:
        logger.error(f"Teams collection failed for user {user_id}: {e}")
        raise
```

---

## 4. Implementation Phases

### 4.1 Phase 1: Foundation (Weeks 1-2)

**Goals:**
- Set up FastAPI application
- Implement authentication system
- Create database models
- Integrate OpenRoute AI

**Tasks:**
1. **FastAPI Setup**
   ```python
   # app/main.py implementation
   # app/config.py configuration
   # app/dependencies.py dependency injection
   ```

2. **Authentication System**
   ```python
   # OAuth 2.0 implementation for Teams
   # JIRA API token management
   # Session management
   ```

3. **Database Models**
   ```python
   # SQLAlchemy models
   # Alembic migrations
   # Repository pattern implementation
   ```

4. **AI Integration**
   ```python
   # OpenRoute API client
   # Prompt engineering
   # Response parsing
   ```

### 4.2 Phase 2: Data Collection (Weeks 3-4)

**Goals:**
- Implement Teams message collector
- Implement email collector
- Implement JIRA ticket fetcher
- Set up background tasks

**Implementation Priority:**
1. Teams Collector → Email Collector → JIRA Collector
2. Background task system with Celery
3. Data validation and storage
4. Error handling and retry logic

### 4.3 Phase 3: AI Processing (Weeks 5-6)

**Goals:**
- Develop content analyzer
- Implement task matching
- Create time estimation
- Build summary generation

**AI Pipeline:**
```python
# Content Analysis Pipeline
Raw Content → Cleaning → Extraction → Matching → Validation → Storage
```

### 4.4 Phase 4: Reporting (Weeks 7-8)

**Goals:**
- Daily report generation
- Weekly work distribution
- JIRA update functionality
- API endpoints

### 4.5 Phase 5: Testing & Deployment (Weeks 9-10)

**Goals:**
- Comprehensive testing
- Performance optimization
- Security hardening
- Documentation and deployment

---

## 5. API Development Guide

### 5.1 FastAPI Router Structure

**Router Implementation Pattern:**
```python
from fastapi import APIRouter, Depends, HTTPException, status
from app.dependencies import get_current_user, get_db
from app.schemas.work_item import WorkItemCreate, WorkItemResponse
from app.services.work_item_service import WorkItemService

router = APIRouter()

@router.post("/", response_model=WorkItemResponse)
async def create_work_item(
    work_item: WorkItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new work item"""
    service = WorkItemService(db)
    return await service.create_work_item(work_item, current_user.id)

@router.get("/{item_id}", response_model=WorkItemResponse)
async def get_work_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get work item by ID"""
    service = WorkItemService(db)
    item = await service.get_work_item(item_id, current_user.id)
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work item not found"
        )
    
    return item
```

### 5.2 Dependency Injection Pattern

**Dependencies Implementation:**
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from app.database.connection import SessionLocal
from app.services.auth_service import AuthService

security = HTTPBearer()

def get_db():
    """Database dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(
    token: str = Depends(security),
    db: Session = Depends(get_db)
):
    """Current user dependency"""
    auth_service = AuthService(db)
    user = await auth_service.get_user_from_token(token.credentials)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    return user
```

### 5.3 Response Models

**Pydantic Schema Pattern:**
```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class WorkItemBase(BaseModel):
    """Base work item schema"""
    description: str = Field(..., min_length=1, max_length=1000)
    time_spent_minutes: int = Field(..., ge=0, le=480)  # Max 8 hours

class WorkItemCreate(WorkItemBase):
    """Work item creation schema"""
    jira_ticket_id: Optional[UUID] = None
    message_id: Optional[UUID] = None

class WorkItemUpdate(BaseModel):
    """Work item update schema"""
    description: Optional[str] = Field(None, min_length=1, max_length=1000)
    time_spent_minutes: Optional[int] = Field(None, ge=0, le=480)
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)

class WorkItemResponse(WorkItemBase):
    """Work item response schema"""
    id: UUID
    user_id: UUID
    confidence_score: float
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
```

---

## 6. Database Development

### 6.1 SQLAlchemy Models

**Base Model Pattern:**
```python
from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()

class BaseModel(Base):
    """Abstract base model with common fields"""
    __abstract__ = True
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

**Model Implementation:**
```python
from sqlalchemy import Column, String, Integer, Float, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class WorkItem(BaseModel):
    """Work item model"""
    __tablename__ = "work_items"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=True)
    jira_ticket_id = Column(UUID(as_uuid=True), ForeignKey("jira_tickets.id"), nullable=True)
    
    description = Column(Text, nullable=False)
    time_spent_minutes = Column(Integer, nullable=False)
    confidence_score = Column(Float, nullable=False, default=0.0)
    status = Column(String(50), nullable=False, default="pending")
    ai_analysis = Column(JSON, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="work_items")
    message = relationship("Message", back_populates="work_items")
    jira_ticket = relationship("JIRATicket", back_populates="work_items")
```

### 6.2 Repository Pattern

**Base Repository:**
```python
from typing import List, Optional, TypeVar, Generic
from sqlalchemy.orm import Session
from app.models.base import BaseModel

T = TypeVar('T', bound=BaseModel)

class BaseRepository(Generic[T]):
    """Base repository with common CRUD operations"""
    
    def __init__(self, db: Session, model_class: type[T]):
        self.db = db
        self.model_class = model_class
    
    async def create(self, obj_in: dict) -> T:
        """Create new record"""
        db_obj = self.model_class(**obj_in)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    async def get(self, id: UUID) -> Optional[T]:
        """Get record by ID"""
        return self.db.query(self.model_class).filter(self.model_class.id == id).first()
    
    async def get_multi(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get multiple records"""
        return self.db.query(self.model_class).offset(skip).limit(limit).all()
    
    async def update(self, db_obj: T, obj_in: dict) -> T:
        """Update record"""
        for field, value in obj_in.items():
            setattr(db_obj, field, value)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    async def delete(self, id: UUID) -> bool:
        """Delete record"""
        obj = await self.get(id)
        if obj:
            self.db.delete(obj)
            self.db.commit()
            return True
        return False
```

### 6.3 Migration Management

**Alembic Configuration:**
```python
# alembic/env.py
from alembic import context
from app.models import Base
from app.database.connection import engine

target_metadata = Base.metadata

def run_migrations_online():
    """Run migrations in 'online' mode"""
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )
        
        with context.begin_transaction():
            context.run_migrations()
```

**Migration Commands:**
```bash
# Create new migration
alembic revision --autogenerate -m "Add work_items table"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

---

## 7. AI Integration Guide

### 7.1 OpenRoute Service Implementation

**AI Service Class:**
```python
import openai
from typing import List, Optional
from app.config import settings
from app.schemas.ai import AIAnalysis, TicketMatch

class AIService:
    """OpenRoute AI integration service"""
    
    def __init__(self):
        self.client = openai.OpenAI(
            base_url=settings.OPENROUTE_BASE_URL,
            api_key=settings.OPENROUTE_API_KEY
        )
    
    async def analyze_content(self, content: str, context: Optional[str] = None) -> AIAnalysis:
        """Analyze content and extract work information"""
        
        prompt = self._build_analysis_prompt(content, context)
        
        try:
            response = await self.client.chat.completions.create(
                model=settings.DEFAULT_AI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=settings.MAX_TOKENS,
                temperature=0.3
            )
            
            return self._parse_analysis_response(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            raise AIProcessingError(f"Content analysis failed: {e}")
    
    def _build_analysis_prompt(self, content: str, context: Optional[str]) -> str:
        """Build prompt for content analysis"""
        
        base_prompt = f"""
        Analyze the following communication and extract work-related information:
        
        Content: {content}
        """
        
        if context:
            base_prompt += f"\nContext: {context}"
        
        base_prompt += """
        
        Extract and return JSON with:
        1. "description": Brief work description
        2. "time_indicators": Any time mentions
        3. "project_keywords": Project/task keywords
        4. "technical_details": Technical information
        5. "confidence": Score 0-1 for extraction quality
        
        Focus on actual work activities, ignore social conversation.
        """
        
        return base_prompt
```

### 7.2 Prompt Engineering

**Prompt Templates:**
```python
class PromptTemplates:
    """AI prompt templates"""
    
    EXTRACT_WORK_INFO = """
    Extract work-related information from this communication:
    
    Content: {content}
    User Context: {user_context}
    
    Return JSON with:
    - description: Brief work summary
    - time_spent: Estimated minutes
    - project_hints: Keywords suggesting project
    - confidence: Quality score 0-1
    
    Example output:
    {{
        "description": "Fixed authentication bug in login module",
        "time_spent": 120,
        "project_hints": ["authentication", "login", "bug fix"],
        "confidence": 0.85
    }}
    """
    
    MATCH_JIRA_TICKETS = """
    Match this work description to the most relevant JIRA tickets:
    
    Work Description: {description}
    Available Tickets:
    {tickets}
    
    Return JSON array of matches with confidence scores:
    [
        {{
            "ticket_key": "PROJ-123",
            "confidence": 0.9,
            "reason": "Direct keyword match for authentication"
        }}
    ]
    
    Only include matches with confidence > 0.5.
    """
    
    GENERATE_SUMMARY = """
    Create a professional daily status summary from these work items:
    
    Work Items:
    {work_items}
    
    Generate a structured summary suitable for JIRA logging:
    - Use bullet points
    - Group related activities
    - Include time estimates
    - Professional tone
    
    Format:
    ## Daily Summary - {date}
    
    ### Completed Tasks:
    - [Task description] (X minutes)
    
    ### Key Achievements:
    - [Achievement description]
    
    ### Next Steps:
    - [Planned activity]
    """
```

### 7.3 Response Parsing

**Response Parser:**
```python
import json
from typing import Dict, Any
from app.schemas.ai import AIAnalysis, TicketMatch

class AIResponseParser:
    """Parse AI responses into structured data"""
    
    @staticmethod
    def parse_analysis_response(response: str) -> AIAnalysis:
        """Parse content analysis response"""
        try:
            data = json.loads(response)
            return AIAnalysis(
                description=data.get("description", ""),
                time_spent=data.get("time_spent", 0),
                project_hints=data.get("project_hints", []),
                confidence=data.get("confidence", 0.0),
                technical_details=data.get("technical_details", "")
            )
        except json.JSONDecodeError:
            # Fallback to text parsing
            return AIAnalysis(
                description=response[:200],
                confidence=0.3,
                project_hints=[],
                time_spent=0
            )
    
    @staticmethod
    def parse_ticket_matches(response: str) -> List[TicketMatch]:
        """Parse ticket matching response"""
        try:
            data = json.loads(response)
            matches = []
            
            for match_data in data:
                match = TicketMatch(
                    ticket_key=match_data["ticket_key"],
                    confidence=match_data["confidence"],
                    reason=match_data.get("reason", "")
                )
                matches.append(match)
            
            return matches
        except (json.JSONDecodeError, KeyError):
            return []
```

---

## 8. Testing Guidelines

### 8.1 Test Structure

**Test Organization:**
```
tests/
├── conftest.py              # Shared test configuration
├── test_api/               # API endpoint tests
│   ├── test_auth.py
│   ├── test_work_items.py
│   └── test_reports.py
├── test_core/              # Core logic tests
│   ├── test_collectors/
│   ├── test_processors/
│   └── test_generators/
├── test_services/          # Service integration tests
│   ├── test_ai_service.py
│   ├── test_teams_service.py
│   └── test_jira_service.py
└── test_utils/            # Utility function tests
```

### 8.2 Test Configuration

**Pytest Configuration (`conftest.py`):**
```python
import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database.connection import get_db
from app.models import Base

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def db():
    """Create test database"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(db):
    """Create test client"""
    def override_get_db():
        yield db
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def sample_user(db):
    """Create sample user for testing"""
    from app.models.user import User
    
    user = User(
        email="test@example.com",
        first_name="Test",
        last_name="User"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
```

### 8.3 Test Examples

**API Test Example:**
```python
import pytest
from fastapi import status

class TestWorkItemAPI:
    """Test work item API endpoints"""
    
    def test_create_work_item(self, client, sample_user):
        """Test work item creation"""
        work_item_data = {
            "description": "Fixed authentication bug",
            "time_spent_minutes": 120
        }
        
        response = client.post(
            "/api/v1/work-items/",
            json=work_item_data,
            headers={"Authorization": f"Bearer {sample_user.token}"}
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["description"] == work_item_data["description"]
        assert data["time_spent_minutes"] == work_item_data["time_spent_minutes"]
        assert "id" in data
    
    def test_get_work_item(self, client, sample_user, sample_work_item):
        """Test work item retrieval"""
        response = client.get(
            f"/api/v1/work-items/{sample_work_item.id}",
            headers={"Authorization": f"Bearer {sample_user.token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(sample_work_item.id)
    
    def test_unauthorized_access(self, client):
        """Test unauthorized access"""
        response = client.get("/api/v1/work-items/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
```

**Service Test Example:**
```python
import pytest
from unittest.mock import AsyncMock, patch
from app.services.ai_service import AIService

class TestAIService:
    """Test AI service functionality"""
    
    @pytest.fixture
    def ai_service(self):
        return AIService()
    
    @patch('openai.OpenAI')
    async def test_analyze_content(self, mock_openai, ai_service):
        """Test content analysis"""
        # Mock OpenAI response
        mock_response = AsyncMock()
        mock_response.choices[0].message.content = json.dumps({
            "description": "Fixed authentication bug",
            "time_spent": 120,
            "confidence": 0.85
        })
        mock_openai.return_value.chat.completions.create.return_value = mock_response
        
        content = "Spent 2 hours fixing the authentication bug in the login module"
        result = await ai_service.analyze_content(content)
        
        assert result.description == "Fixed authentication bug"
        assert result.time_spent == 120
        assert result.confidence == 0.85
    
    async def test_error_handling(self, ai_service):
        """Test AI service error handling"""
        with patch.object(ai_service.client.chat.completions, 'create', side_effect=Exception("API Error")):
            with pytest.raises(AIProcessingError):
                await ai_service.analyze_content("test content")
```

### 8.4 Test Coverage

**Coverage Requirements:**
- Overall coverage: > 90%
- Critical paths: 100%
- API endpoints: 100%
- AI processing: > 85%

**Run Tests with Coverage:**
```bash
pytest --cov=app --cov-report=html --cov-report=term-missing
```

---

## 9. Deployment Guide

### 9.1 Docker Configuration

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Docker Compose:**
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/daily_logger
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    volumes:
      - ./logs:/app/logs

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: daily_logger
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  celery:
    build: .
    command: celery -A app.core.celery_app worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/daily_logger
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
```

### 9.2 Production Deployment

**Environment Configuration:**
```bash
# Production environment variables
export APP_NAME="Daily Logger Assist"
export DEBUG=false
export SECRET_KEY="your-production-secret-key"
export DATABASE_URL="postgresql://user:password@localhost:5432/daily_logger"
export OPENROUTE_API_KEY="your-production-api-key"

# Start production server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Nginx Configuration:**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 10. Maintenance Procedures

### 10.1 Database Maintenance

**Backup Procedures:**
```bash
# Create database backup
pg_dump -h localhost -U user daily_logger > backup_$(date +%Y%m%d).sql

# Restore from backup
psql -h localhost -U user daily_logger < backup_20241201.sql
```

**Index Maintenance:**
```sql
-- Check index usage
SELECT schemaname, tablename, attname, n_distinct, correlation 
FROM pg_stats 
WHERE schemaname = 'public';

-- Rebuild indexes
REINDEX INDEX CONCURRENTLY idx_work_items_user_id;
```

### 10.2 Log Management

**Log Rotation:**
```python
# Automatic log rotation configuration
from loguru import logger

logger.add(
    "logs/app.log",
    rotation="10 MB",
    retention="30 days",
    compression="zip"
)
```

### 10.3 Performance Monitoring

**Health Check Endpoint:**
```python
@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    checks = {
        "database": await check_database_connection(),
        "redis": await check_redis_connection(),
        "ai_service": await check_ai_service(),
        "external_apis": await check_external_apis()
    }
    
    overall_status = "healthy" if all(checks.values()) else "unhealthy"
    
    return {
        "status": overall_status,
        "timestamp": datetime.utcnow(),
        "checks": checks
    }
```

---

This development documentation provides comprehensive guidance for implementing, testing, and maintaining the Daily Logger Assist application. Follow these guidelines to ensure consistent, high-quality code and successful project delivery. 