"""
Test Configuration and Fixtures - Daily Logger Assist

Comprehensive pytest configuration with fixtures for testing all components.
"""

import pytest
import asyncio
import tempfile
import os
from typing import Generator, Dict, Any
from datetime import date, datetime, timedelta
from uuid import uuid4, UUID

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Import application components
from app.main import app
from app.database.connection import get_db
from app.models.base import Base
from app.models.user import User
from app.models.work_item import WorkItem
from app.models.message import Message
from app.models.report import Report
from app.services.ai_service import AIService
from app.services.report_service import ReportService
from app.config import settings

# Test Database Configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ==================== DATABASE FIXTURES ====================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Create a test database session."""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # Clean up - drop all tables
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Create a test client with database session override."""
    
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()

# ==================== USER FIXTURES ====================

@pytest.fixture
def sample_user(db_session: Session) -> User:
    """Create a sample user for testing."""
    user = User(
        id=uuid4(),
        email="test@example.com",
        first_name="Test",
        last_name="User",
        is_active=True,
        teams_credentials={
            "access_token": "test_teams_token",
            "refresh_token": "test_teams_refresh",
            "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
        },
        jira_credentials={
            "api_token": "test_jira_token",
            "server_url": "https://test.atlassian.net",
            "username": "test@example.com"
        },
        email_credentials={
            "access_token": "test_email_token",
            "refresh_token": "test_email_refresh"
        },
        preferences={
            "ai_confidence_threshold": 0.7,
            "auto_approve_reports": False,
            "default_report_template": "standard_daily"
        }
    )
    
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    return user

@pytest.fixture
def authenticated_headers(sample_user: User) -> Dict[str, str]:
    """Create authentication headers for API testing."""
    # In a real implementation, this would generate a proper JWT token
    # For testing, we'll use a mock token
    return {
        "Authorization": f"Bearer test_token_{sample_user.id}",
        "Content-Type": "application/json"
    }

# ==================== WORK ITEM FIXTURES ====================

@pytest.fixture
def sample_work_items(db_session: Session, sample_user: User) -> list[WorkItem]:
    """Create sample work items for testing."""
    work_items = []
    
    # High confidence work item
    work_item1 = WorkItem(
        id=uuid4(),
        user_id=sample_user.id,
        description="Fixed authentication bug in login module",
        time_spent_minutes=120,
        confidence_score=0.9,
        status="completed",
        ai_analysis={
            "category": "bug_fix",
            "complexity": "medium",
            "technical_domain": "authentication",
            "required_skills": ["python", "security", "debugging"],
            "sentiment": "positive",
            "urgency": "high"
        }
    )
    
    # Medium confidence work item
    work_item2 = WorkItem(
        id=uuid4(),
        user_id=sample_user.id,
        description="Updated documentation for API endpoints",
        time_spent_minutes=60,
        confidence_score=0.7,
        status="completed",
        ai_analysis={
            "category": "documentation",
            "complexity": "low",
            "technical_domain": "documentation",
            "required_skills": ["writing", "api_design"],
            "sentiment": "neutral",
            "urgency": "low"
        }
    )
    
    # Low confidence work item
    work_item3 = WorkItem(
        id=uuid4(),
        user_id=sample_user.id,
        description="Discussed project requirements",
        time_spent_minutes=30,
        confidence_score=0.4,
        status="pending_review",
        ai_analysis={
            "category": "meeting",
            "complexity": "low",
            "technical_domain": "planning",
            "required_skills": ["communication"],
            "sentiment": "neutral",
            "urgency": "medium"
        }
    )
    
    work_items.extend([work_item1, work_item2, work_item3])
    
    for item in work_items:
        db_session.add(item)
    
    db_session.commit()
    
    for item in work_items:
        db_session.refresh(item)
    
    return work_items

# ==================== MESSAGE FIXTURES ====================

@pytest.fixture
def sample_messages(db_session: Session, sample_user: User) -> list[Message]:
    """Create sample messages for testing."""
    messages = []
    
    # Teams message
    message1 = Message(
        id=uuid4(),
        user_id=sample_user.id,
        source="teams",
        channel_id="team_channel_1",
        content="Fixed the login issue, took about 2 hours to debug and implement the solution",
        sender="test@example.com",
        message_timestamp=datetime.utcnow() - timedelta(hours=2),
        processed=True,
        metadata={
            "channel_name": "Development Team",
            "thread_id": "thread_123",
            "mentions": []
        }
    )
    
    # Email message
    message2 = Message(
        id=uuid4(),
        user_id=sample_user.id,
        source="email",
        content="Updated the API documentation as requested. All endpoints now have proper examples.",
        sender="teammate@example.com",
        message_timestamp=datetime.utcnow() - timedelta(hours=1),
        processed=True,
        metadata={
            "subject": "Documentation Update Complete",
            "folder": "Inbox",
            "priority": "normal"
        }
    )
    
    messages.extend([message1, message2])
    
    for message in messages:
        db_session.add(message)
    
    db_session.commit()
    
    for message in messages:
        db_session.refresh(message)
    
    return messages

# ==================== REPORT FIXTURES ====================

@pytest.fixture
def sample_report(db_session: Session, sample_user: User, sample_work_items: list[WorkItem]) -> Report:
    """Create a sample report for testing."""
    report = Report(
        id=uuid4(),
        user_id=sample_user.id,
        title="Daily Report - 2024-01-15",
        report_type="daily",
        report_date=date.today(),
        content="""# Daily Report - 2024-01-15

## Summary
Completed 3 tasks with a total time investment of 3.5 hours.

## Tasks Completed
- Fixed authentication bug in login module (120 minutes)
- Updated documentation for API endpoints (60 minutes)
- Discussed project requirements (30 minutes)

## Total Time: 3.5 hours""",
        raw_content={
            "work_items": len(sample_work_items),
            "statistics": {
                "total_time_minutes": 210,
                "high_confidence_items": 2,
                "categories": {"bug_fix": 1, "documentation": 1, "meeting": 1}
            }
        },
        total_time_minutes=210,
        total_work_items=3,
        high_confidence_items=2,
        generation_method="ai",
        template_used="standard_daily",
        ai_model_used="openroute-ai",
        status="approved",
        report_quality_score=0.85,
        completeness_score=0.9
    )
    
    db_session.add(report)
    db_session.commit()
    db_session.refresh(report)
    
    return report

# ==================== SERVICE FIXTURES ====================

@pytest.fixture
def ai_service() -> AIService:
    """Create an AI service instance for testing."""
    return AIService()

@pytest.fixture
def report_service(db_session: Session) -> ReportService:
    """Create a report service instance for testing."""
    return ReportService(db_session)

# ==================== MOCK FIXTURES ====================

@pytest.fixture
def mock_ai_response():
    """Mock AI service response for testing."""
    return {
        "work_items": [
            {
                "activity_type": "development",
                "description": "Fixed authentication bug",
                "estimated_time": 2.0,
                "priority": "high",
                "project_reference": "AUTH-123"
            }
        ],
        "sentiment_analysis": {
            "sentiment": "positive",
            "confidence": 0.8,
            "emotional_tone": "satisfied",
            "urgency_indicators": ["fixed", "bug"]
        },
        "urgency_detection": {
            "urgency_level": "high",
            "urgency_score": 8,
            "detected_keywords": ["bug", "fixed", "authentication"]
        }
    }

@pytest.fixture
def mock_jira_tickets():
    """Mock JIRA tickets for testing."""
    return [
        {
            "ticket_key": "AUTH-123",
            "title": "Fix authentication login issue",
            "status": "In Progress",
            "assignee": "test@example.com",
            "project": "AUTH",
            "description": "Users unable to login with correct credentials"
        },
        {
            "ticket_key": "DOC-456",
            "title": "Update API documentation",
            "status": "To Do",
            "assignee": "test@example.com", 
            "project": "DOC",
            "description": "API endpoints need better documentation with examples"
        }
    ]

# ==================== UTILITY FIXTURES ====================

@pytest.fixture
def temp_directory():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

@pytest.fixture
def sample_date_range():
    """Provide a sample date range for testing."""
    today = date.today()
    return {
        "start_date": today - timedelta(days=7),
        "end_date": today,
        "today": today,
        "yesterday": today - timedelta(days=1),
        "week_start": today - timedelta(days=today.weekday())
    }

# ==================== PERFORMANCE TEST FIXTURES ====================

@pytest.fixture
def performance_work_items(db_session: Session, sample_user: User) -> list[WorkItem]:
    """Create a large number of work items for performance testing."""
    work_items = []
    
    for i in range(100):
        work_item = WorkItem(
            id=uuid4(),
            user_id=sample_user.id,
            description=f"Performance test work item {i}",
            time_spent_minutes=30 + (i % 120),  # 30-150 minutes
            confidence_score=0.5 + (i % 5) * 0.1,  # 0.5-0.9
            status="completed",
            ai_analysis={
                "category": f"category_{i % 5}",
                "complexity": ["low", "medium", "high"][i % 3],
                "technical_domain": f"domain_{i % 3}"
            }
        )
        work_items.append(work_item)
    
    for item in work_items:
        db_session.add(item)
    
    db_session.commit()
    
    return work_items

# ==================== SECURITY TEST FIXTURES ====================

@pytest.fixture
def malicious_payloads():
    """Provide common malicious payloads for security testing."""
    return {
        "sql_injection": [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "1; SELECT * FROM users"
        ],
        "xss": [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src='x' onerror='alert(1)'>",
            "<svg onload=alert(1)>"
        ],
        "path_traversal": [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd"
        ],
        "command_injection": [
            "; cat /etc/passwd",
            "| ls -la",
            "&& whoami",
            "; rm -rf /"
        ]
    }

# ==================== CLEANUP UTILITIES ====================

def pytest_configure(config):
    """Configure pytest with custom settings."""
    # Ensure test reports directory exists
    os.makedirs("tests/reports", exist_ok=True)

def pytest_unconfigure(config):
    """Clean up after all tests complete."""
    # Clean up test database
    if os.path.exists("test.db"):
        os.remove("test.db")
    
    # Clean up any temporary test files
    for file in ["test.db-journal", "test.db-wal", "test.db-shm"]:
        if os.path.exists(file):
            os.remove(file) 