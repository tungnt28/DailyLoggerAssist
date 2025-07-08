"""
AI Processing API - Daily Logger Assist

Enhanced AI processing endpoints for Phase 3: intelligent categorization,
advanced time estimation, productivity analytics, and automated work logging.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

from app.database.connection import get_db
from app.dependencies import get_current_user, get_current_active_user
from app.models.user import User
from app.models.work_item import WorkItem
from app.models.report import Report
from app.schemas.ai import *
from app.services.ai_service import AIService
from app.tasks.ai_processing import (
    enhanced_content_analysis,
    intelligent_task_categorization_batch,
    enhanced_time_estimation_batch,
    automated_jira_work_logging,
    generate_productivity_analytics,
    process_all_pending_ai_analysis
)

router = APIRouter(prefix="/ai", tags=["Enhanced AI Processing"])

@router.post("/analyze/content", response_model=ContentAnalysisResponse)
async def analyze_content(
    request: ContentAnalysisRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Enhanced content analysis with deep context awareness.
    
    Analyzes content for work items, sentiment, urgency, required skills,
    collaboration patterns, and productivity indicators.
    """
    try:
        # Initialize AI service
        ai_service = AIService()
        
        # Run enhanced analysis
        analysis_result = await ai_service.analyze_content_with_context(
            content=request.content,
            context=request.context.dict() if request.context else None,
            user_id=str(current_user.id)
        )
        
        return ContentAnalysisResponse(
            success=True,
            work_items=analysis_result.get("work_items", []),
            sentiment_analysis=analysis_result.get("sentiment_analysis", {}),
            urgency_detection=analysis_result.get("urgency_detection", {}),
            skill_classification=analysis_result.get("skill_classification", []),
            collaboration_patterns=analysis_result.get("collaboration_patterns", {}),
            productivity_indicators=analysis_result.get("productivity_indicators", {})
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Content analysis failed: {str(e)}"
        )

@router.post("/analyze/content/async", response_model=TaskResponse)
async def analyze_content_async(
    request: ContentAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user)
):
    """
    Asynchronous enhanced content analysis.
    
    Queues content for enhanced analysis and returns a task ID for tracking.
    """
    try:
        # Queue enhanced content analysis task
        task = enhanced_content_analysis.delay(
            user_id=str(current_user.id),
            content=request.content,
            context=request.context.dict() if request.context else None
        )
        
        return TaskResponse(
            success=True,
            task_id=task.id,
            message="Content analysis queued successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue content analysis: {str(e)}"
        )

@router.post("/categorize/task", response_model=TaskCategorizationResponse)
async def categorize_task(
    request: TaskCategorizationRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Intelligent task categorization with priority and complexity assessment.
    
    Provides comprehensive categorization including technical domain,
    complexity level, required skills, risk factors, and dependencies.
    """
    try:
        # Initialize AI service
        ai_service = AIService()
        
        # Run intelligent categorization
        categorization = await ai_service.intelligent_task_categorization(
            task_description=request.task_description,
            context=request.context.dict() if request.context else None
        )
        
        return TaskCategorizationResponse(
            success=True,
            categorization=categorization
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Task categorization failed: {str(e)}"
        )

@router.post("/categorize/batch", response_model=TaskResponse)
async def categorize_work_items_batch(
    request: BatchCategorizationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Batch categorization of work items.
    
    Queues multiple work items for intelligent categorization.
    """
    try:
        # Verify work items belong to user
        work_items = db.query(WorkItem).filter(
            WorkItem.id.in_([UUID(id) for id in request.work_item_ids]),
            WorkItem.user_id == current_user.id
        ).all()
        
        if len(work_items) != len(request.work_item_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Some work items not found or not accessible"
            )
        
        # Queue categorization task
        task = intelligent_task_categorization_batch.delay(request.work_item_ids)
        
        return TaskResponse(
            success=True,
            task_id=task.id,
            message=f"Queued {len(request.work_item_ids)} work items for categorization"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch categorization failed: {str(e)}"
        )

@router.post("/estimate/time", response_model=TimeEstimationResponse)
async def estimate_time(
    request: TimeEstimationRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Enhanced time estimation using historical data and machine learning insights.
    
    Provides detailed time estimates with confidence intervals and risk factors.
    """
    try:
        # Initialize AI service
        ai_service = AIService()
        
        # Run enhanced time estimation
        estimation = await ai_service.enhanced_time_estimation(
            task_description=request.task_description,
            context=request.context.dict() if request.context else None,
            user_id=str(current_user.id),
            use_historical_data=request.use_historical_data
        )
        
        return TimeEstimationResponse(
            success=True,
            estimation=estimation
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Time estimation failed: {str(e)}"
        )

@router.post("/estimate/batch", response_model=TaskResponse)
async def estimate_time_batch(
    request: BatchTimeEstimationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Batch time estimation for work items.
    
    Queues multiple work items for enhanced time estimation.
    """
    try:
        # Verify work items belong to user
        work_items = db.query(WorkItem).filter(
            WorkItem.id.in_([UUID(id) for id in request.work_item_ids]),
            WorkItem.user_id == current_user.id
        ).all()
        
        if len(work_items) != len(request.work_item_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Some work items not found or not accessible"
            )
        
        # Queue time estimation task
        task = enhanced_time_estimation_batch.delay(
            request.work_item_ids,
            str(current_user.id)
        )
        
        return TaskResponse(
            success=True,
            task_id=task.id,
            message=f"Queued {len(request.work_item_ids)} work items for time estimation"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch time estimation failed: {str(e)}"
        )

@router.post("/jira/auto-log", response_model=JiraWorkLoggingResponse)
async def auto_log_work_to_jira(
    request: JiraWorkLoggingRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Automated JIRA work logging with intelligent time distribution.
    
    Analyzes work items and automatically logs them to appropriate JIRA tickets
    with confidence-based recommendations.
    """
    try:
        # Verify work items belong to user
        work_items = db.query(WorkItem).filter(
            WorkItem.id.in_([UUID(id) for id in request.work_item_ids]),
            WorkItem.user_id == current_user.id
        ).all()
        
        if len(work_items) != len(request.work_item_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Some work items not found or not accessible"
            )
        
        # Queue automated JIRA work logging
        task = automated_jira_work_logging.delay(
            str(current_user.id),
            request.work_item_ids
        )
        
        return JiraWorkLoggingResponse(
            success=True,
            task_id=task.id,
            message=f"Queued {len(request.work_item_ids)} work items for JIRA logging"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"JIRA work logging failed: {str(e)}"
        )

@router.get("/analytics/productivity", response_model=ProductivityAnalyticsResponse)
async def get_productivity_analytics(
    timeframe: str = "daily",
    date: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive productivity analytics and insights.
    
    Retrieves existing analytics or generates them if not available.
    """
    try:
        # Validate timeframe
        if timeframe not in ["daily", "weekly", "monthly"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid timeframe. Must be daily, weekly, or monthly"
            )
        
        # Calculate target date
        if date:
            try:
                target_date = datetime.fromisoformat(date).date()
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date format. Use YYYY-MM-DD"
                )
        else:
            target_date = datetime.now().date()
        
        # Check for existing report
        existing_report = db.query(Report).filter(
            Report.user_id == current_user.id,
            Report.report_date == target_date,
            Report.report_type == f"productivity_{timeframe}"
        ).first()
        
        if existing_report:
            return ProductivityAnalyticsResponse(
                success=True,
                analytics=existing_report.content,
                generated_at=existing_report.updated_at,
                from_cache=True
            )
        
        # Generate new analytics
        task = generate_productivity_analytics.delay(
            str(current_user.id),
            timeframe,
            date
        )
        
        return ProductivityAnalyticsResponse(
            success=True,
            task_id=task.id,
            message="Productivity analytics generation queued",
            from_cache=False
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Productivity analytics failed: {str(e)}"
        )

@router.post("/analytics/generate", response_model=TaskResponse)
async def generate_analytics(
    request: GenerateAnalyticsRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Generate productivity analytics for specified timeframes.
    
    Queues analytics generation for the requested timeframes and date range.
    """
    try:
        tasks_created = []
        
        for timeframe in request.timeframes:
            if timeframe not in ["daily", "weekly", "monthly"]:
                continue
            
            task = generate_productivity_analytics.delay(
                str(current_user.id),
                timeframe,
                request.date
            )
            tasks_created.append(task.id)
        
        return TaskResponse(
            success=True,
            task_id=tasks_created[0] if tasks_created else None,
            message=f"Generated {len(tasks_created)} analytics tasks",
            metadata={"task_ids": tasks_created}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analytics generation failed: {str(e)}"
        )

@router.post("/process/comprehensive", response_model=TaskResponse)
async def comprehensive_ai_processing(
    current_user: User = Depends(get_current_active_user)
):
    """
    Comprehensive AI processing for all pending items.
    
    Processes recent messages, categorizes work items, estimates time,
    matches to JIRA tickets, and generates productivity analytics.
    """
    try:
        # Queue comprehensive AI processing
        task = process_all_pending_ai_analysis.delay(str(current_user.id))
        
        return TaskResponse(
            success=True,
            task_id=task.id,
            message="Comprehensive AI processing queued successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Comprehensive AI processing failed: {str(e)}"
        )

@router.get("/status/processing", response_model=ProcessingStatusResponse)
async def get_processing_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get AI processing status and statistics for the current user.
    
    Returns information about recent processing activities and pending items.
    """
    try:
        # Get processing statistics
        from datetime import timedelta
        
        # Recent work items
        recent_work_items = db.query(WorkItem).filter(
            WorkItem.user_id == current_user.id,
            WorkItem.created_at >= datetime.now() - timedelta(days=7)
        ).count()
        
        # Work items with AI analysis
        analyzed_items = db.query(WorkItem).filter(
            WorkItem.user_id == current_user.id,
            WorkItem.analysis_metadata.isnot(None)
        ).count()
        
        # Recent reports
        recent_reports = db.query(Report).filter(
            Report.user_id == current_user.id,
            Report.created_at >= datetime.now() - timedelta(days=7)
        ).count()
        
        return ProcessingStatusResponse(
            success=True,
            statistics={
                "recent_work_items": recent_work_items,
                "analyzed_items": analyzed_items,
                "analysis_coverage": analyzed_items / max(recent_work_items, 1),
                "recent_reports": recent_reports,
                "ai_service_status": "operational"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get processing status: {str(e)}"
        )

@router.get("/insights/user-patterns", response_model=UserPatternsResponse)
async def get_user_patterns(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get personalized user patterns and insights.
    
    Returns AI-learned patterns about user's work habits, skills, and productivity.
    """
    try:
        # Initialize AI service to access user patterns
        ai_service = AIService()
        user_id = str(current_user.id)
        
        patterns = ai_service.user_patterns.get(user_id, {})
        
        # Process patterns for response
        processed_patterns = {
            "common_skills": dict(patterns.get("common_skills", {})),
            "productivity_trends": patterns.get("productivity_trends", [])[-10:],  # Last 10 entries
            "preferred_categories": dict(patterns.get("preferred_categories", {})),
            "insights": []
        }
        
        # Generate insights from patterns
        if processed_patterns["common_skills"]:
            top_skill = max(processed_patterns["common_skills"], key=processed_patterns["common_skills"].get)
            processed_patterns["insights"].append(f"Most frequently used skill: {top_skill}")
        
        if processed_patterns["productivity_trends"]:
            avg_score = sum(t.get("score", 0) for t in processed_patterns["productivity_trends"]) / len(processed_patterns["productivity_trends"])
            processed_patterns["insights"].append(f"Average productivity score: {avg_score:.1f}")
        
        return UserPatternsResponse(
            success=True,
            patterns=processed_patterns
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user patterns: {str(e)}"
        ) 