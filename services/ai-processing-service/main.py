"""
AI Processing Service for Daily Logger Assist

Handles AI-powered content analysis, task matching, and intelligent features.
"""

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import sys
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
import logging
from pydantic import BaseModel, field_serializer
from uuid import UUID

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.config.base import BaseConfig
from shared.utils.database import init_database, get_db
from shared.models import WorkItem, Message, JIRATicket, User

# Initialize configuration
config = BaseConfig()

# Initialize database
db_manager = init_database(config.DATABASE_URL, "ai-processing-service")
db_manager.create_tables()

# Create FastAPI app
app = FastAPI(
    title="Daily Logger Assist - AI Processing Service",
    description="AI-powered content analysis and task processing",
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
class ContentAnalysisRequest(BaseModel):
    content: str
    source: str  # "teams", "email", "jira"
    context: Optional[Dict[str, Any]] = None

class ContentAnalysisResponse(BaseModel):
    work_items: List[Dict[str, Any]]
    confidence_score: float
    categories: List[str]
    time_estimates: Dict[str, float]
    suggested_tags: List[str]
    processing_time: float

class TaskMatchingRequest(BaseModel):
    work_description: str
    available_tickets: List[Dict[str, Any]]
    user_preferences: Optional[Dict[str, Any]] = None

class TaskMatchingResponse(BaseModel):
    matches: List[Dict[str, Any]]
    best_match: Optional[Dict[str, Any]] = None
    confidence_score: float

class WorkItemCreate(BaseModel):
    description: str
    time_spent_minutes: int
    category: str
    tags: List[str] = []
    message_id: Optional[str] = None
    jira_ticket_id: Optional[str] = None

class WorkItemResponse(BaseModel):
    id: str
    user_id: str
    description: str
    time_spent_minutes: int
    confidence_score: float
    category: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

class AIInsightsResponse(BaseModel):
    productivity_score: float
    time_distribution: Dict[str, float]
    category_breakdown: Dict[str, int]
    suggestions: List[str]
    trends: Dict[str, Any]

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

def analyze_content_ai(content: str, source: str) -> Dict[str, Any]:
    """Mock AI content analysis - replace with actual AI implementation"""
    # TODO: Implement actual AI analysis using OpenRoute or similar
    import time
    start_time = time.time()
    
    # Mock analysis based on content keywords
    work_items = []
    categories = []
    time_estimates = {}
    suggested_tags = []
    
    content_lower = content.lower()
    
    # Simple keyword-based analysis
    if any(word in content_lower for word in ["bug", "fix", "issue", "error"]):
        categories.append("bug_fix")
        time_estimates["bug_fix"] = 2.0
        suggested_tags.extend(["bug", "fix", "maintenance"])
        
        work_items.append({
            "description": f"Fixed issue: {content[:100]}...",
            "category": "bug_fix",
            "priority": "high",
            "estimated_hours": 2.0,
            "confidence": 0.8
        })
    
    if any(word in content_lower for word in ["feature", "implement", "add", "create"]):
        categories.append("feature_development")
        time_estimates["feature_development"] = 4.0
        suggested_tags.extend(["feature", "development", "implementation"])
        
        work_items.append({
            "description": f"Implemented feature: {content[:100]}...",
            "category": "feature_development",
            "priority": "medium",
            "estimated_hours": 4.0,
            "confidence": 0.7
        })
    
    if any(word in content_lower for word in ["meeting", "discuss", "plan", "review"]):
        categories.append("meeting")
        time_estimates["meeting"] = 1.0
        suggested_tags.extend(["meeting", "planning", "discussion"])
        
        work_items.append({
            "description": f"Meeting: {content[:100]}...",
            "category": "meeting",
            "priority": "low",
            "estimated_hours": 1.0,
            "confidence": 0.9
        })
    
    # Default if no specific category found
    if not categories:
        categories.append("general")
        time_estimates["general"] = 1.5
        suggested_tags.extend(["general", "task"])
        
        work_items.append({
            "description": f"General task: {content[:100]}...",
            "category": "general",
            "priority": "medium",
            "estimated_hours": 1.5,
            "confidence": 0.6
        })
    
    processing_time = time.time() - start_time
    
    return {
        "work_items": work_items,
        "confidence_score": 0.75,
        "categories": categories,
        "time_estimates": time_estimates,
        "suggested_tags": list(set(suggested_tags)),
        "processing_time": processing_time
    }

def match_tasks_to_jira(work_description: str, available_tickets: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Mock task matching - replace with actual AI implementation"""
    # TODO: Implement actual AI matching using embeddings or similar
    matches = []
    best_match = None
    best_score = 0.0
    
    work_lower = work_description.lower()
    
    for ticket in available_tickets:
        ticket_text = f"{ticket.get('summary', '')} {ticket.get('description', '')}".lower()
        
        # Simple keyword matching
        common_words = set(work_lower.split()) & set(ticket_text.split())
        score = len(common_words) / max(len(work_lower.split()), len(ticket_text.split()))
        
        if score > 0.1:  # Minimum threshold
            match = {
                "ticket": ticket,
                "confidence": score,
                "reason": f"Matched {len(common_words)} common words"
            }
            matches.append(match)
            
            if score > best_score:
                best_score = score
                best_match = match
    
    return {
        "matches": matches,
        "best_match": best_match,
        "confidence_score": best_score
    }

# Endpoints

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_healthy = db_manager.health_check()
    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "service": "AI Processing Service",
        "version": "1.0.0",
        "database": "healthy" if db_healthy else "unhealthy"
    }

@app.post("/api/v1/ai/analyze", response_model=ContentAnalysisResponse)
async def analyze_content(
    request: ContentAnalysisRequest,
    current_user: User = Depends(get_current_user_from_header)
):
    """Analyze content and extract work items"""
    try:
        analysis = analyze_content_ai(request.content, request.source)
        
        return ContentAnalysisResponse(
            work_items=analysis["work_items"],
            confidence_score=analysis["confidence_score"],
            categories=analysis["categories"],
            time_estimates=analysis["time_estimates"],
            suggested_tags=analysis["suggested_tags"],
            processing_time=analysis["processing_time"]
        )
        
    except Exception as e:
        logging.error(f"Content analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Content analysis failed"
        )

@app.post("/api/v1/ai/match-tasks", response_model=TaskMatchingResponse)
async def match_tasks(
    request: TaskMatchingRequest,
    current_user: User = Depends(get_current_user_from_header)
):
    """Match work description to JIRA tickets"""
    try:
        matching_result = match_tasks_to_jira(request.work_description, request.available_tickets)
        
        return TaskMatchingResponse(
            matches=matching_result["matches"],
            best_match=matching_result["best_match"],
            confidence_score=matching_result["confidence_score"]
        )
        
    except Exception as e:
        logging.error(f"Task matching failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Task matching failed"
        )

@app.post("/api/v1/ai/work-items", response_model=WorkItemResponse)
async def create_work_item(
    work_item: WorkItemCreate,
    current_user: User = Depends(get_current_user_from_header),
    db: Session = Depends(get_db)
):
    """Create a work item from AI analysis"""
    try:
        # Create work item
        db_work_item = WorkItem(
            user_id=str(current_user.id),
            description=work_item.description,
            time_spent_minutes=work_item.time_spent_minutes,
            confidence_score=0.8,  # Default confidence
            category=work_item.category,
            status="pending",
            message_id=work_item.message_id,
            jira_ticket_id=work_item.jira_ticket_id
        )
        
        db.add(db_work_item)
        db.commit()
        db.refresh(db_work_item)
        
        logging.info(f"Creating WorkItemResponse with id type: {type(db_work_item.id)}, value: {db_work_item.id}")
        logging.info(f"Creating WorkItemResponse with user_id type: {type(db_work_item.user_id)}, value: {db_work_item.user_id}")
        
        id_str = str(db_work_item.id)
        user_id_str = str(db_work_item.user_id)
        
        logging.info(f"Converted id to string: {id_str}, type: {type(id_str)}")
        logging.info(f"Converted user_id to string: {user_id_str}, type: {type(user_id_str)}")
        
        data = {
            'id': str(db_work_item.id),
            'user_id': str(db_work_item.user_id),
            'description': db_work_item.description,
            'time_spent_minutes': db_work_item.time_spent_minutes,
            'confidence_score': db_work_item.confidence_score,
            'category': db_work_item.category,
            'status': db_work_item.status,
            'created_at': db_work_item.created_at,
            'updated_at': db_work_item.updated_at
        }
        logging.info(f"WorkItemResponse data: {data}")
        return WorkItemResponse(**data)
        
    except Exception as e:
        logging.error(f"Failed to create work item: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create work item"
        )

@app.get("/api/v1/ai/work-items", response_model=List[WorkItemResponse])
async def get_work_items(
    category: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user_from_header),
    db: Session = Depends(get_db)
):
    """Get work items for the current user"""
    query = db.query(WorkItem).filter(WorkItem.user_id == str(current_user.id))
    
    if category:
        query = query.filter(WorkItem.category == category)
    
    if status:
        query = query.filter(WorkItem.status == status)
    
    work_items = query.order_by(WorkItem.created_at.desc()).all()
    logging.info(f"Found {len(work_items)} work items")
    for item in work_items:
        logging.info(f"Item id type: {type(item.id)}, value: {item.id}")
        logging.info(f"Item user_id type: {type(item.user_id)}, value: {item.user_id}")
    
    return [WorkItemResponse(
        id=str(item.id),
        user_id=str(item.user_id),
        description=item.description,
        time_spent_minutes=item.time_spent_minutes,
        confidence_score=item.confidence_score,
        category=item.category,
        status=item.status,
        created_at=item.created_at,
        updated_at=item.updated_at
    ) for item in work_items]

@app.get("/api/v1/ai/insights", response_model=AIInsightsResponse)
async def get_ai_insights(
    current_user: User = Depends(get_current_user_from_header),
    db: Session = Depends(get_db)
):
    """Get AI-powered insights about user's work patterns"""
    try:
        # Get user's work items
        work_items = db.query(WorkItem).filter(
            WorkItem.user_id == str(current_user.id)
        ).all()
        
        if not work_items:
            return AIInsightsResponse(
                productivity_score=0.0,
                time_distribution={},
                category_breakdown={},
                suggestions=["Start logging your work to get insights!"],
                trends={}
            )
        
        # Calculate insights
        total_hours = sum(item.time_spent_minutes / 60.0 for item in work_items)
        completed_items = [item for item in work_items if item.status == "completed"]
        productivity_score = len(completed_items) / len(work_items) if work_items else 0.0
        
        # Category breakdown
        category_breakdown = {}
        for item in work_items:
            category_breakdown[item.category] = category_breakdown.get(item.category, 0) + 1
        
        # Time distribution
        time_distribution = {}
        for item in work_items:
            category = item.category
            time_distribution[category] = time_distribution.get(category, 0) + (item.time_spent_minutes / 60.0)
        
        # Suggestions
        suggestions = []
        if productivity_score < 0.7:
            suggestions.append("Consider breaking down larger tasks into smaller, manageable pieces")
        if len(category_breakdown) < 3:
            suggestions.append("Try diversifying your work categories for better balance")
        if total_hours < 20:
            suggestions.append("You might be under-estimating your work time")
        
        # Trends (mock data for now)
        trends = {
            "weekly_progress": [0.6, 0.7, 0.8, 0.75, 0.9],
            "most_productive_day": "Wednesday",
            "peak_hours": "10:00-12:00"
        }
        
        return AIInsightsResponse(
            productivity_score=productivity_score,
            time_distribution=time_distribution,
            category_breakdown=category_breakdown,
            suggestions=suggestions,
            trends=trends
        )
        
    except Exception as e:
        logging.error(f"Failed to generate insights: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate insights"
        )

@app.post("/api/v1/ai/batch-analyze")
async def batch_analyze_content(
    contents: List[ContentAnalysisRequest],
    current_user: User = Depends(get_current_user_from_header)
):
    """Analyze multiple content items in batch"""
    try:
        results = []
        for content_request in contents:
            analysis = analyze_content_ai(content_request.content, content_request.source)
            results.append({
                "content": content_request.content,
                "analysis": analysis
            })
        
        return {
            "results": results,
            "total_processed": len(results),
            "average_confidence": sum(r["analysis"]["confidence_score"] for r in results) / len(results)
        }
        
    except Exception as e:
        logging.error(f"Batch analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Batch analysis failed"
        )

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Application startup tasks"""
    logging.info("AI Processing Service starting...")
    logging.info(f"Environment: {config.ENVIRONMENT}")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks"""
    logging.info("AI Processing Service shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8003,
        reload=True
    ) 