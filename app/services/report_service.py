"""
Report Service - Daily Logger Assist

Comprehensive service for generating daily/weekly reports, managing templates,
and handling JIRA updates.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from uuid import UUID
import json

from app.models.report import Report
from app.models.work_item import WorkItem
from app.models.user import User
from app.services.ai_service import AIService
from app.services.jira_service import JIRAService
from app.schemas.report import ReportCreate, ReportUpdate
from loguru import logger


class ReportService:
    """Service for comprehensive report management"""
    
    def __init__(self, db: Session):
        self.db = db
        self.ai_service = AIService()
        self.jira_service = JIRAService()
    
    async def generate_daily_report(
        self,
        user_id: UUID,
        report_date: date,
        template: Optional[str] = None,
        auto_approve: bool = False
    ) -> Report:
        """Generate a comprehensive daily report"""
        logger.info(f"Generating daily report for user {user_id} on {report_date}")
        
        try:
            # Get work items for the date
            work_items = await self._get_work_items_for_date(user_id, report_date)
            
            if not work_items:
                logger.warning(f"No work items found for {report_date}")
                return await self._create_empty_report(user_id, "daily", report_date)
            
            # Calculate statistics
            stats = self._calculate_report_statistics(work_items)
            
            # Generate report content using AI
            content, quality_score = await self._generate_report_content(
                work_items, "daily", template or "standard_daily"
            )
            
            # Prepare JIRA updates
            jira_updates = await self._prepare_jira_updates(work_items)
            
            # Create report
            report_data = ReportCreate(
                title=f"Daily Report - {report_date.strftime('%Y-%m-%d')}",
                report_type="daily",
                report_date=report_date,
                content=content,
                raw_content={
                    "work_items": [self._serialize_work_item(item) for item in work_items],
                    "statistics": stats,
                    "jira_updates": jira_updates
                },
                generation_method="ai",
                template_used=template or "standard_daily",
                ai_model_used="openroute-ai"
            )
            
            report = Report(
                user_id=user_id,
                title=report_data.title,
                report_type=report_data.report_type,
                report_date=report_data.report_date,
                content=report_data.content,
                raw_content=report_data.raw_content,
                total_time_minutes=stats["total_time_minutes"],
                total_work_items=stats["total_work_items"],
                high_confidence_items=stats["high_confidence_items"],
                jira_updates=jira_updates,
                generation_method=report_data.generation_method,
                template_used=report_data.template_used,
                ai_model_used=report_data.ai_model_used,
                status="approved" if auto_approve else "draft",
                report_quality_score=quality_score,
                completeness_score=self._calculate_completeness_score(work_items)
            )
            
            self.db.add(report)
            self.db.commit()
            self.db.refresh(report)
            
            logger.info(f"Daily report generated successfully: {report.id}")
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate daily report: {e}")
            self.db.rollback()
            raise
    
    async def generate_weekly_report(
        self,
        user_id: UUID,
        week_start: date,
        template: Optional[str] = None,
        auto_approve: bool = False
    ) -> Report:
        """Generate a comprehensive weekly report"""
        logger.info(f"Generating weekly report for user {user_id} starting {week_start}")
        
        try:
            # Calculate week end
            week_end = week_start + timedelta(days=6)
            
            # Get work items for the week
            work_items = await self._get_work_items_for_date_range(
                user_id, week_start, week_end
            )
            
            if not work_items:
                logger.warning(f"No work items found for week {week_start}")
                return await self._create_empty_report(user_id, "weekly", week_start, week_start)
            
            # Calculate statistics
            stats = self._calculate_report_statistics(work_items)
            
            # Generate weekly distribution
            daily_distribution = self._generate_weekly_distribution(work_items, week_start)
            
            # Generate report content using AI
            content, quality_score = await self._generate_weekly_content(
                work_items, daily_distribution, week_start, template or "weekly_summary"
            )
            
            # Prepare JIRA updates for the week
            jira_updates = await self._prepare_jira_updates(work_items)
            
            # Create report
            report = Report(
                user_id=user_id,
                title=f"Weekly Report - Week of {week_start.strftime('%Y-%m-%d')}",
                report_type="weekly",
                report_date=week_start,
                week_start_date=week_start,
                content=content,
                raw_content={
                    "work_items": [self._serialize_work_item(item) for item in work_items],
                    "statistics": stats,
                    "daily_distribution": daily_distribution,
                    "jira_updates": jira_updates
                },
                total_time_minutes=stats["total_time_minutes"],
                total_work_items=stats["total_work_items"],
                high_confidence_items=stats["high_confidence_items"],
                jira_updates=jira_updates,
                generation_method="ai",
                template_used=template or "weekly_summary",
                ai_model_used="openroute-ai",
                status="approved" if auto_approve else "draft",
                report_quality_score=quality_score,
                completeness_score=self._calculate_completeness_score(work_items)
            )
            
            self.db.add(report)
            self.db.commit()
            self.db.refresh(report)
            
            logger.info(f"Weekly report generated successfully: {report.id}")
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate weekly report: {e}")
            self.db.rollback()
            raise
    
    async def send_report_to_jira(self, report_id: UUID, user_id: UUID) -> Dict[str, Any]:
        """Send report updates to JIRA tickets"""
        logger.info(f"Sending report {report_id} to JIRA for user {user_id}")
        
        try:
            # Get report
            report = self.db.query(Report).filter(
                and_(Report.id == report_id, Report.user_id == user_id)
            ).first()
            
            if not report:
                raise ValueError(f"Report {report_id} not found")
            
            if not report.jira_updates:
                raise ValueError("No JIRA updates available in report")
            
            # Get user for JIRA credentials
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user or not user.jira_credentials:
                raise ValueError("JIRA credentials not found")
            
            # Process JIRA updates
            successful_updates = []
            failed_updates = []
            
            for update in report.jira_updates:
                try:
                    # Send update to JIRA
                    result = await self.jira_service.add_work_log(
                        ticket_key=update["ticket_key"],
                        time_spent=update["time_spent"],
                        description=update["description"],
                        started=update.get("started"),
                        credentials=user.jira_credentials
                    )
                    
                    if result["success"]:
                        successful_updates.append({
                            **update,
                            "jira_response": result
                        })
                    else:
                        failed_updates.append({
                            **update,
                            "error": result.get("error", "Unknown error")
                        })
                        
                except Exception as e:
                    logger.error(f"Failed to update JIRA ticket {update.get('ticket_key')}: {e}")
                    failed_updates.append({
                        **update,
                        "error": str(e)
                    })
            
            # Update report status
            if failed_updates:
                report.jira_update_status = "partial_success" if successful_updates else "failed"
                report.jira_update_error = f"Failed to update {len(failed_updates)} tickets"
            else:
                report.jira_update_status = "completed"
                report.status = "sent_to_jira"
            
            self.db.commit()
            
            result = {
                "success": len(successful_updates) > 0,
                "total_updates": len(report.jira_updates),
                "successful_updates": len(successful_updates),
                "failed_updates": len(failed_updates),
                "successful_tickets": [u["ticket_key"] for u in successful_updates],
                "failed_tickets": [u["ticket_key"] for u in failed_updates],
                "status": report.jira_update_status
            }
            
            logger.info(f"JIRA update completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to send report to JIRA: {e}")
            # Update report with error
            if 'report' in locals():
                report.jira_update_status = "failed"
                report.jira_update_error = str(e)
                self.db.commit()
            raise
    
    async def get_report_templates(self) -> List[Dict[str, Any]]:
        """Get available report templates"""
        return [
            {
                "id": "standard_daily",
                "name": "Standard Daily Report",
                "description": "Concise daily status report with key accomplishments",
                "type": "daily",
                "sections": ["summary", "tasks_completed", "time_breakdown", "next_steps"]
            },
            {
                "id": "detailed_daily",
                "name": "Detailed Daily Report",
                "description": "Comprehensive daily report with technical details and challenges",
                "type": "daily",
                "sections": ["summary", "tasks_completed", "technical_details", "challenges", "time_breakdown", "next_steps"]
            },
            {
                "id": "weekly_summary",
                "name": "Weekly Summary Report",
                "description": "Weekly overview with daily distribution and productivity metrics",
                "type": "weekly",
                "sections": ["week_overview", "daily_breakdown", "productivity_metrics", "achievements", "planning"]
            },
            {
                "id": "sprint_summary",
                "name": "Sprint Summary Report",
                "description": "Sprint-focused weekly report with velocity and completion metrics",
                "type": "weekly",
                "sections": ["sprint_overview", "velocity_metrics", "completed_stories", "blockers", "retrospective"]
            }
        ]
    
    def get_reports(
        self,
        user_id: UUID,
        report_type: Optional[str] = None,
        status: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Report], int]:
        """Get reports with filtering and pagination"""
        query = self.db.query(Report).filter(Report.user_id == user_id)
        
        if report_type:
            query = query.filter(Report.report_type == report_type)
        
        if status:
            query = query.filter(Report.status == status)
        
        if date_from:
            query = query.filter(Report.report_date >= date_from)
        
        if date_to:
            query = query.filter(Report.report_date <= date_to)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination and ordering
        reports = query.order_by(Report.report_date.desc(), Report.created_at.desc())\
                      .offset(offset)\
                      .limit(limit)\
                      .all()
        
        return reports, total_count
    
    def get_report_by_id(self, report_id: UUID, user_id: UUID) -> Optional[Report]:
        """Get a specific report by ID"""
        return self.db.query(Report).filter(
            and_(Report.id == report_id, Report.user_id == user_id)
        ).first()
    
    async def update_report(
        self,
        report_id: UUID,
        user_id: UUID,
        updates: ReportUpdate
    ) -> Report:
        """Update an existing report"""
        report = self.get_report_by_id(report_id, user_id)
        if not report:
            raise ValueError(f"Report {report_id} not found")
        
        # Update fields
        for field, value in updates.dict(exclude_unset=True).items():
            setattr(report, field, value)
        
        self.db.commit()
        self.db.refresh(report)
        
        logger.info(f"Report {report_id} updated successfully")
        return report
    
    # Private helper methods
    
    async def _get_work_items_for_date(self, user_id: UUID, target_date: date) -> List[WorkItem]:
        """Get work items for a specific date"""
        return self.db.query(WorkItem).filter(
            and_(
                WorkItem.user_id == user_id,
                func.date(WorkItem.created_at) == target_date
            )
        ).all()
    
    async def _get_work_items_for_date_range(
        self, user_id: UUID, start_date: date, end_date: date
    ) -> List[WorkItem]:
        """Get work items for a date range"""
        return self.db.query(WorkItem).filter(
            and_(
                WorkItem.user_id == user_id,
                func.date(WorkItem.created_at) >= start_date,
                func.date(WorkItem.created_at) <= end_date
            )
        ).all()
    
    def _calculate_report_statistics(self, work_items: List[WorkItem]) -> Dict[str, Any]:
        """Calculate statistics for work items"""
        total_time = sum(item.time_spent_minutes for item in work_items)
        high_confidence = sum(1 for item in work_items if item.confidence_score >= 0.7)
        
        # Category breakdown
        categories = {}
        for item in work_items:
            category = item.ai_analysis.get("category", "Other") if item.ai_analysis else "Other"
            categories[category] = categories.get(category, 0) + 1
        
        return {
            "total_time_minutes": total_time,
            "total_work_items": len(work_items),
            "high_confidence_items": high_confidence,
            "average_confidence": sum(item.confidence_score for item in work_items) / len(work_items) if work_items else 0,
            "category_breakdown": categories,
            "time_by_category": self._calculate_time_by_category(work_items)
        }
    
    def _calculate_time_by_category(self, work_items: List[WorkItem]) -> Dict[str, int]:
        """Calculate time spent by category"""
        time_by_category = {}
        for item in work_items:
            category = item.ai_analysis.get("category", "Other") if item.ai_analysis else "Other"
            time_by_category[category] = time_by_category.get(category, 0) + item.time_spent_minutes
        return time_by_category
    
    async def _generate_report_content(
        self, work_items: List[WorkItem], report_type: str, template: str
    ) -> Tuple[str, float]:
        """Generate report content using AI"""
        work_items_data = [self._serialize_work_item(item) for item in work_items]
        
        # Use AI service to generate formatted report
        report_data = await self.ai_service.generate_report(
            work_items=work_items_data,
            report_type=report_type,
            template=template
        )
        
        return report_data["content"], report_data.get("quality_score", 0.8)
    
    async def _generate_weekly_content(
        self,
        work_items: List[WorkItem],
        daily_distribution: Dict[str, Any],
        week_start: date,
        template: str
    ) -> Tuple[str, float]:
        """Generate weekly report content using AI"""
        work_items_data = [self._serialize_work_item(item) for item in work_items]
        
        # Use AI service to generate weekly report
        report_data = await self.ai_service.generate_weekly_report(
            work_items=work_items_data,
            daily_distribution=daily_distribution,
            week_start=week_start.isoformat(),
            template=template
        )
        
        return report_data["content"], report_data.get("quality_score", 0.8)
    
    def _generate_weekly_distribution(
        self, work_items: List[WorkItem], week_start: date
    ) -> Dict[str, Any]:
        """Generate 8-hour daily distribution for the week"""
        # Group work items by day
        daily_items = {}
        for item in work_items:
            day = item.created_at.date()
            if day not in daily_items:
                daily_items[day] = []
            daily_items[day].append(item)
        
        # Create 8-hour distribution for each day
        distribution = {}
        for i in range(7):  # 7 days in a week
            current_date = week_start + timedelta(days=i)
            day_items = daily_items.get(current_date, [])
            
            total_time = sum(item.time_spent_minutes for item in day_items)
            
            distribution[current_date.isoformat()] = {
                "date": current_date.isoformat(),
                "work_items": len(day_items),
                "total_minutes": total_time,
                "total_hours": total_time / 60.0,
                "distribution_quality": min(total_time / 480.0, 1.0),  # 480 minutes = 8 hours
                "items": [self._serialize_work_item(item) for item in day_items]
            }
        
        return distribution
    
    async def _prepare_jira_updates(self, work_items: List[WorkItem]) -> List[Dict[str, Any]]:
        """Prepare JIRA work log updates from work items"""
        jira_updates = []
        
        for item in work_items:
            if item.jira_ticket_id:
                # Get JIRA ticket information
                jira_ticket = await self._get_jira_ticket_info(item.jira_ticket_id)
                if jira_ticket:
                    jira_updates.append({
                        "ticket_key": jira_ticket.get("key"),
                        "work_item_id": str(item.id),
                        "time_spent": f"{item.time_spent_minutes}m",
                        "description": item.description,
                        "started": item.created_at.isoformat(),
                        "confidence": item.confidence_score
                    })
        
        return jira_updates
    
    async def _get_jira_ticket_info(self, ticket_id: UUID) -> Optional[Dict[str, Any]]:
        """Get JIRA ticket information"""
        # This would fetch from JIRA tickets table
        # For now, return a placeholder
        return {"key": f"PROJ-{ticket_id.hex[:8]}", "title": "Sample Ticket"}
    
    def _serialize_work_item(self, item: WorkItem) -> Dict[str, Any]:
        """Serialize work item to dictionary"""
        return {
            "id": str(item.id),
            "description": item.description,
            "time_spent_minutes": item.time_spent_minutes,
            "confidence_score": item.confidence_score,
            "status": item.status,
            "ai_analysis": item.ai_analysis,
            "created_at": item.created_at.isoformat()
        }
    
    async def _create_empty_report(
        self,
        user_id: UUID,
        report_type: str,
        report_date: date,
        week_start_date: Optional[date] = None
    ) -> Report:
        """Create an empty report when no work items are found"""
        content = f"No work items found for {report_type} report on {report_date}"
        
        report = Report(
            user_id=user_id,
            title=f"{report_type.title()} Report - {report_date.strftime('%Y-%m-%d')}",
            report_type=report_type,
            report_date=report_date,
            week_start_date=week_start_date,
            content=content,
            raw_content={"work_items": [], "statistics": {}},
            total_time_minutes=0,
            total_work_items=0,
            high_confidence_items=0,
            generation_method="ai",
            status="draft",
            report_quality_score=0.0,
            completeness_score=0.0
        )
        
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        
        return report
    
    def _calculate_completeness_score(self, work_items: List[WorkItem]) -> float:
        """Calculate report completeness score"""
        if not work_items:
            return 0.0
        
        # Factors affecting completeness
        jira_linked = sum(1 for item in work_items if item.jira_ticket_id)
        high_confidence = sum(1 for item in work_items if item.confidence_score >= 0.7)
        has_description = sum(1 for item in work_items if len(item.description.strip()) > 10)
        
        total_items = len(work_items)
        
        # Calculate weighted score
        jira_score = (jira_linked / total_items) * 0.4
        confidence_score = (high_confidence / total_items) * 0.4
        description_score = (has_description / total_items) * 0.2
        
        return jira_score + confidence_score + description_score 