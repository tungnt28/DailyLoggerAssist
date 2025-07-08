"""
Reports API Routes - Daily Logger Assist

API endpoints for generating and managing daily/weekly reports.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime, timedelta
from uuid import UUID

from app.database.connection import get_db
from app.dependencies import get_current_user, CommonQueryParams
from app.models.user import User
from app.schemas.report import (
    ReportResponse, ReportGenerate, ReportSummary, ReportCreate, ReportUpdate
)
from app.services.report_service import ReportService
from app.tasks.ai_processing import generate_report_task, send_jira_updates_task
from loguru import logger

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/daily/{report_date}", response_model=ReportResponse)
async def get_daily_report(
    report_date: date,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get daily report for specific date"""
    logger.info(f"Daily report requested for {report_date} by user {current_user.id}")
    
    try:
        report_service = ReportService(db)
        
        # Try to find existing report
        reports, _ = report_service.get_reports(
            user_id=current_user.id,
            report_type="daily",
            date_from=report_date,
            date_to=report_date,
            limit=1
        )
        
        if reports:
            return reports[0]
        
        # If no report exists, generate one
        report = await report_service.generate_daily_report(
            user_id=current_user.id,
            report_date=report_date,
            auto_approve=True
        )
        
        return report
        
    except Exception as e:
        logger.error(f"Failed to get daily report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve daily report: {str(e)}"
        )

@router.get("/weekly/{week_start}", response_model=ReportResponse)
async def get_weekly_report(
    week_start: date,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get weekly report for specific week"""
    logger.info(f"Weekly report requested for week {week_start} by user {current_user.id}")
    
    try:
        # Validate week_start is actually a Monday
        if week_start.weekday() != 0:
            # Adjust to the Monday of that week
            week_start = week_start - timedelta(days=week_start.weekday())
        
        report_service = ReportService(db)
        
        # Try to find existing report
        reports, _ = report_service.get_reports(
            user_id=current_user.id,
            report_type="weekly",
            date_from=week_start,
            date_to=week_start,
            limit=1
        )
        
        if reports:
            return reports[0]
        
        # If no report exists, generate one
        report = await report_service.generate_weekly_report(
            user_id=current_user.id,
            week_start=week_start,
            auto_approve=True
        )
        
        return report
        
    except Exception as e:
        logger.error(f"Failed to get weekly report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve weekly report: {str(e)}"
        )

@router.post("/generate", response_model=ReportResponse)
async def generate_report(
    request: ReportGenerate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate new report (async for complex reports, sync for simple ones)"""
    logger.info(f"Report generation requested by user {current_user.id}: {request.report_type} for {request.report_date}")
    
    try:
        report_service = ReportService(db)
        
        # For daily reports or if auto_approve is True, generate synchronously
        if request.report_type == "daily" or request.auto_approve:
            if request.report_type == "daily":
                report = await report_service.generate_daily_report(
                    user_id=current_user.id,
                    report_date=request.report_date,
                    template=request.template,
                    auto_approve=request.auto_approve
                )
            else:  # weekly
                week_start = request.week_start_date or request.report_date
                if week_start.weekday() != 0:
                    week_start = week_start - timedelta(days=week_start.weekday())
                
                report = await report_service.generate_weekly_report(
                    user_id=current_user.id,
                    week_start=week_start,
                    template=request.template,
                    auto_approve=request.auto_approve
                )
            
            # If send_to_jira is requested, queue JIRA update
            if request.send_to_jira and report.jira_updates:
                background_tasks.add_task(
                    send_jira_updates_task,
                    str(report.id),
                    str(current_user.id)
                )
            
            return report
        else:
            # For complex weekly reports, generate asynchronously
            task = generate_report_task.delay(
                user_id=str(current_user.id),
                report_type=request.report_type,
                report_date=request.report_date.isoformat(),
                week_start_date=request.week_start_date.isoformat() if request.week_start_date else None,
                template=request.template,
                auto_approve=request.auto_approve,
                send_to_jira=request.send_to_jira
            )
            
            # Return task info (will need to check status later)
            return {
                "id": task.id,
                "status": "generating",
                "message": f"Report generation queued. Task ID: {task.id}",
                "report_type": request.report_type,
                "report_date": request.report_date,
                "estimated_completion": "2-5 minutes"
            }
            
    except Exception as e:
        logger.error(f"Failed to generate report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report: {str(e)}"
        )

@router.get("/", response_model=List[ReportSummary])
async def list_reports(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    common: CommonQueryParams = Depends(),
    report_type: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None
):
    """List user's reports with filtering and pagination"""
    logger.info(f"Reports list requested by user {current_user.id}")
    
    try:
        report_service = ReportService(db)
        
        reports, total_count = report_service.get_reports(
            user_id=current_user.id,
            report_type=report_type,
            status=status,
            date_from=date_from,
            date_to=date_to,
            limit=common.limit,
            offset=common.offset
        )
        
        # Convert to summary format
        report_summaries = []
        for report in reports:
            report_summaries.append(ReportSummary(
                id=report.id,
                title=report.title,
                report_type=report.report_type,
                report_date=report.report_date,
                status=report.status,
                total_hours=report.total_hours,
                total_work_items=report.total_work_items,
                confidence_percentage=report.confidence_percentage,
                created_at=report.created_at
            ))
        
        return report_summaries
        
    except Exception as e:
        logger.error(f"Failed to list reports: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve reports: {str(e)}"
        )

@router.get("/{report_id}", response_model=ReportResponse)
async def get_report_by_id(
    report_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific report by ID"""
    logger.info(f"Report {report_id} requested by user {current_user.id}")
    
    try:
        report_service = ReportService(db)
        report = report_service.get_report_by_id(report_id, current_user.id)
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report {report_id} not found"
            )
        
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get report {report_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve report: {str(e)}"
        )

@router.put("/{report_id}", response_model=ReportResponse)
async def update_report(
    report_id: UUID,
    updates: ReportUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an existing report"""
    logger.info(f"Report {report_id} update requested by user {current_user.id}")
    
    try:
        report_service = ReportService(db)
        
        # Update the report
        updated_report = await report_service.update_report(
            report_id=report_id,
            user_id=current_user.id,
            updates=updates
        )
        
        return updated_report
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to update report {report_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update report: {str(e)}"
        )

@router.post("/send-to-jira/{report_id}")
async def send_report_to_jira(
    report_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send report updates to JIRA"""
    logger.info(f"JIRA update requested for report {report_id} by user {current_user.id}")
    
    try:
        # Validate that report exists and belongs to user
        report_service = ReportService(db)
        report = report_service.get_report_by_id(report_id, current_user.id)
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report {report_id} not found"
            )
        
        if not current_user.jira_credentials:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="JIRA not connected. Please connect JIRA first."
            )
        
        if not report.jira_updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No JIRA updates available in this report"
            )
        
        # For immediate feedback, try to send synchronously for small reports
        if len(report.jira_updates) <= 5:
            try:
                result = await report_service.send_report_to_jira(report_id, current_user.id)
                return {
                    "message": "JIRA updates completed",
                    "report_id": str(report_id),
                    "status": "completed",
                    "result": result
                }
            except Exception as e:
                logger.warning(f"Sync JIRA update failed, falling back to async: {e}")
        
        # For large reports or if sync fails, queue as background task
        background_tasks.add_task(
            send_jira_updates_task,
            str(report_id),
            str(current_user.id)
        )
        
        return {
            "message": "JIRA update queued successfully",
            "report_id": str(report_id),
            "status": "in_progress",
            "estimated_completion": "1-2 minutes"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send report to JIRA: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send report to JIRA: {str(e)}"
        )

@router.get("/templates", tags=["Report Templates"])
async def get_report_templates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get available report templates"""
    logger.info(f"Report templates requested by user {current_user.id}")
    
    try:
        report_service = ReportService(db)
        templates = await report_service.get_report_templates()
        
        return {
            "templates": templates,
            "total_templates": len(templates),
            "default_daily": "standard_daily",
            "default_weekly": "weekly_summary"
        }
        
    except Exception as e:
        logger.error(f"Failed to get report templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve report templates: {str(e)}"
        )

@router.get("/analytics/statistics")
async def get_report_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = 30
):
    """Get report generation statistics for the user"""
    logger.info(f"Report statistics requested by user {current_user.id}")
    
    try:
        report_service = ReportService(db)
        
        # Get reports from the last N days
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        reports, total_count = report_service.get_reports(
            user_id=current_user.id,
            date_from=start_date,
            date_to=end_date,
            limit=1000  # Get all reports in period
        )
        
        # Calculate statistics
        daily_reports = sum(1 for r in reports if r.report_type == "daily")
        weekly_reports = sum(1 for r in reports if r.report_type == "weekly")
        
        total_hours = sum(r.total_hours for r in reports)
        total_work_items = sum(r.total_work_items for r in reports)
        
        avg_quality = sum(r.report_quality_score or 0 for r in reports) / len(reports) if reports else 0
        avg_completeness = sum(r.completeness_score or 0 for r in reports) / len(reports) if reports else 0
        
        # Status breakdown
        status_breakdown = {}
        for report in reports:
            status = report.status
            status_breakdown[status] = status_breakdown.get(status, 0) + 1
        
        return {
            "period_days": days,
            "total_reports": total_count,
            "report_types": {
                "daily": daily_reports,
                "weekly": weekly_reports
            },
            "productivity_metrics": {
                "total_hours_logged": total_hours,
                "total_work_items": total_work_items,
                "average_hours_per_report": total_hours / len(reports) if reports else 0,
                "average_items_per_report": total_work_items / len(reports) if reports else 0
            },
            "quality_metrics": {
                "average_quality_score": avg_quality,
                "average_completeness_score": avg_completeness
            },
            "status_breakdown": status_breakdown,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get report statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve report statistics: {str(e)}"
        ) 