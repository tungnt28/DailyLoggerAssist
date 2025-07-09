"""
Reporting Service for Daily Logger Assist

Handles report generation, templates, and analytics.
"""

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import sys
import os
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, date, timedelta
from pydantic import BaseModel

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.config.base import BaseConfig
from shared.utils.database import init_database, get_db
from shared.models import Report, WorkItem, User

# Initialize configuration
config = BaseConfig()

# Initialize database
db_manager = init_database(config.DATABASE_URL, "reporting-service")
db_manager.create_tables()

# Create FastAPI app
app = FastAPI(
    title="Daily Logger Assist - Reporting Service",
    description="Report generation and analytics",
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
class ReportCreate(BaseModel):
    report_type: str  # "daily", "weekly", "monthly", "custom"
    report_date: date
    template_id: Optional[str] = None
    custom_content: Optional[str] = None

class ReportResponse(BaseModel):
    id: str
    user_id: str
    report_type: str
    report_date: str
    template: str
    content: str
    metadata: Dict[str, Any]
    quality_score: float
    status: str
    created_at: str
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True

class ReportTemplateCreate(BaseModel):
    name: str
    description: str
    template_type: str
    content_template: str
    is_default: bool = False

class ReportTemplateResponse(BaseModel):
    id: str
    name: str
    description: str
    template_type: str
    content_template: str
    is_default: bool
    user_id: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True

class AnalyticsResponse(BaseModel):
    productivity_trends: List[Dict[str, Any]]
    category_breakdown: List[Dict[str, Any]]
    weekly_summary: Dict[str, Any]
    time_distribution: List[Dict[str, Any]]

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

def generate_report_content(report_type: str, work_items: List[WorkItem], template: str) -> str:
    """Generate report content based on work items and template"""
    # TODO: Implement actual report generation logic
    # For now, return a simple formatted report
    
    total_hours = sum(item.estimated_hours for item in work_items)
    completed_items = [item for item in work_items if item.status == "completed"]
    
    content = f"""
# {report_type.title()} Report - {datetime.now().strftime('%Y-%m-%d')}

## Summary
- Total work items: {len(work_items)}
- Completed items: {len(completed_items)}
- Total hours: {total_hours:.1f}
- Completion rate: {(len(completed_items) / len(work_items) * 100) if work_items else 0:.1f}%

## Work Items
"""
    
    for item in work_items:
        content += f"""
### {item.description}
- Category: {item.category}
- Priority: {item.priority}
- Status: {item.status}
- Time: {item.estimated_hours:.1f} hours
- Tags: {', '.join(item.tags) if item.tags else 'None'}
"""
    
    return content

def calculate_analytics(work_items: List[WorkItem]) -> Dict[str, Any]:
    """Calculate analytics from work items"""
    if not work_items:
        return {
            "productivity_trends": [],
            "category_breakdown": [],
            "weekly_summary": {
                "total_hours": 0,
                "total_items": 0,
                "average_daily_hours": 0,
                "efficiency_score": 0
            },
            "time_distribution": []
        }
    
    # Category breakdown
    category_breakdown = {}
    for item in work_items:
        category = item.category
        if category not in category_breakdown:
            category_breakdown[category] = {"hours": 0, "items": 0}
        category_breakdown[category]["hours"] += item.estimated_hours
        category_breakdown[category]["items"] += 1
    
    # Convert to list format
    category_list = []
    total_hours = sum(item.estimated_hours for item in work_items)
    for category, data in category_breakdown.items():
        category_list.append({
            "category": category,
            "hours": data["hours"],
            "items": data["items"],
            "percentage": (data["hours"] / total_hours * 100) if total_hours > 0 else 0
        })
    
    # Weekly summary
    completed_items = [item for item in work_items if item.status == "completed"]
    efficiency_score = len(completed_items) / len(work_items) if work_items else 0
    
    weekly_summary = {
        "total_hours": total_hours,
        "total_items": len(work_items),
        "average_daily_hours": total_hours / 7,  # Assuming 7 days
        "efficiency_score": efficiency_score
    }
    
    # Mock productivity trends (last 7 days)
    productivity_trends = []
    for i in range(7):
        day = datetime.now() - timedelta(days=i)
        productivity_trends.append({
            "date": day.strftime("%Y-%m-%d"),
            "hours_worked": total_hours / 7,  # Distribute evenly
            "work_items_completed": len(completed_items) // 7,
            "efficiency_score": efficiency_score
        })
    
    # Mock time distribution (24 hours)
    time_distribution = []
    for hour in range(24):
        time_distribution.append({
            "hour": hour,
            "productivity_score": 0.7 if 9 <= hour <= 17 else 0.3,  # Work hours
            "work_items": len(work_items) // 24
        })
    
    return {
        "productivity_trends": productivity_trends,
        "category_breakdown": category_list,
        "weekly_summary": weekly_summary,
        "time_distribution": time_distribution
    }

# Endpoints

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_healthy = db_manager.health_check()
    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "service": "Reporting Service",
        "version": "1.0.0",
        "database": "healthy" if db_healthy else "unhealthy"
    }

@app.post("/api/v1/reports", response_model=ReportResponse)
async def create_report(
    report_request: ReportCreate,
    current_user: User = Depends(get_current_user_from_header),
    db: Session = Depends(get_db)
):
    """Create a new report"""
    try:
        # Get work items for the report period
        start_date = report_request.report_date
        end_date = start_date + timedelta(days=1) if report_request.report_type == "daily" else start_date + timedelta(days=7)
        
        work_items = db.query(WorkItem).filter(
            WorkItem.user_id == str(current_user.id),
            WorkItem.created_at >= start_date,
            WorkItem.created_at < end_date
        ).all()
        
        # Get template
        template = "default_template"  # TODO: Implement template selection
        
        # Generate content
        content = generate_report_content(report_request.report_type, work_items, template)
        
        # Calculate metadata
        total_hours = sum(item.estimated_hours for item in work_items)
        categories = {}
        priorities = {}
        for item in work_items:
            categories[item.category] = categories.get(item.category, 0) + 1
            priorities[item.priority] = priorities.get(item.priority, 0) + 1
        
        metadata = {
            "total_work_items": len(work_items),
            "total_time_hours": total_hours,
            "categories": categories,
            "priorities": priorities,
            "jira_tickets_updated": 0  # TODO: Implement JIRA integration
        }
        
        # Create report
        report = Report(
            user_id=str(current_user.id),
            report_type=report_request.report_type,
            report_date=report_request.report_date,
            template=template,
            content=content,
            metadata=metadata,
            quality_score=0.8,  # TODO: Implement quality scoring
            status="completed"
        )
        
        db.add(report)
        db.commit()
        db.refresh(report)
        
        return ReportResponse.from_orm(report)
        
    except Exception as e:
        logging.error(f"Failed to create report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create report"
        )

@app.get("/api/v1/reports", response_model=List[ReportResponse])
async def get_reports(
    report_type: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user_from_header),
    db: Session = Depends(get_db)
):
    """Get reports for the current user"""
    query = db.query(Report).filter(Report.user_id == str(current_user.id))
    
    if report_type:
        query = query.filter(Report.report_type == report_type)
    
    if status:
        query = query.filter(Report.status == status)
    
    reports = query.order_by(Report.created_at.desc()).all()
    return [ReportResponse.from_orm(report) for report in reports]

@app.get("/api/v1/reports/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: str,
    current_user: User = Depends(get_current_user_from_header),
    db: Session = Depends(get_db)
):
    """Get a specific report by ID"""
    report = db.query(Report).filter(
        Report.id == report_id,
        Report.user_id == str(current_user.id)
    ).first()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    return ReportResponse.from_orm(report)

@app.get("/api/v1/reports/templates", response_model=List[ReportTemplateResponse])
async def get_templates(
    template_type: Optional[str] = None,
    current_user: User = Depends(get_current_user_from_header),
    db: Session = Depends(get_db)
):
    """Get report templates"""
    # TODO: Implement template management
    # For now, return default templates
    default_templates = [
        {
            "id": "daily_default",
            "name": "Daily Report Template",
            "description": "Standard daily report template",
            "template_type": "daily",
            "content_template": "Daily report for {date}",
            "is_default": True,
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "id": "weekly_default",
            "name": "Weekly Report Template",
            "description": "Standard weekly report template",
            "template_type": "weekly",
            "content_template": "Weekly report for week of {date}",
            "is_default": True,
            "created_at": datetime.utcnow().isoformat()
        }
    ]
    
    if template_type:
        default_templates = [t for t in default_templates if t["template_type"] == template_type]
    
    return default_templates

@app.get("/api/v1/reports/analytics", response_model=AnalyticsResponse)
async def get_analytics(
    days: int = 30,
    current_user: User = Depends(get_current_user_from_header),
    db: Session = Depends(get_db)
):
    """Get analytics for the current user"""
    try:
        # Get work items for the specified period
        start_date = datetime.utcnow() - timedelta(days=days)
        work_items = db.query(WorkItem).filter(
            WorkItem.user_id == str(current_user.id),
            WorkItem.created_at >= start_date
        ).all()
        
        analytics = calculate_analytics(work_items)
        
        return AnalyticsResponse(**analytics)
        
    except Exception as e:
        logging.error(f"Failed to generate analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate analytics"
        )

@app.post("/api/v1/reports/export/{report_id}")
async def export_report(
    report_id: str,
    format: str = "pdf",  # "pdf", "csv", "json"
    current_user: User = Depends(get_current_user_from_header),
    db: Session = Depends(get_db)
):
    """Export a report in various formats"""
    report = db.query(Report).filter(
        Report.id == report_id,
        Report.user_id == str(current_user.id)
    ).first()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    # TODO: Implement actual export functionality
    # For now, return the report content
    return {
        "report_id": report_id,
        "format": format,
        "content": report.content,
        "export_url": f"/exports/{report_id}.{format}"  # Mock export URL
    }

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Application startup tasks"""
    logging.info("Reporting Service starting...")
    logging.info(f"Environment: {config.ENVIRONMENT}")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks"""
    logging.info("Reporting Service shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8004,
        reload=True
    ) 