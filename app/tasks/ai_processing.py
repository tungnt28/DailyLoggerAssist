"""
AI Processing Tasks - Daily Logger Assist

Enhanced Celery tasks for AI-powered content analysis, intelligent categorization,
and productivity analytics (Phase 3).
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from celery import Task
from sqlalchemy.orm import Session
from loguru import logger

from app.tasks.celery_app import celery_app
from app.database.connection import get_db
from app.services.ai_service import AIService
from app.models.user import User
from app.models.message import Message
from app.models.work_item import WorkItem
from app.models.jira_ticket import JIRATicket
from app.models.report import Report

class AIProcessingTask(Task):
    """Base class for AI processing tasks with enhanced error handling."""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"AI processing task {task_id} failed: {exc}")
        super().on_failure(exc, task_id, args, kwargs, einfo)

@celery_app.task(base=AIProcessingTask, bind=True, max_retries=3)
def enhanced_content_analysis(self, user_id: str, content: str, context: Optional[Dict[str, Any]] = None):
    """
    Enhanced content analysis with deep context awareness.
    
    Args:
        user_id: User ID for personalized analysis
        content: Content to analyze
        context: Rich context information
    """
    try:
        logger.info(f"Starting enhanced content analysis for user {user_id}")
        
        # Initialize AI service
        ai_service = AIService()
        
        # Run enhanced analysis
        analysis_result = asyncio.run(
            ai_service.analyze_content_with_context(
                content=content,
                context=context,
                user_id=user_id
            )
        )
        
        # Store results in database
        db = next(get_db())
        try:
            # Create work items from analysis
            work_items = analysis_result.get("work_items", [])
            created_items = []
            
            for item_data in work_items:
                work_item = WorkItem(
                    user_id=user_id,
                    description=item_data.get("description", ""),
                    activity_type=item_data.get("activity_type", "other"),
                    estimated_time=item_data.get("estimated_time", 1.0),
                    priority=item_data.get("priority", "medium"),
                    project_reference=item_data.get("project_reference"),
                    analysis_metadata={
                        "sentiment": analysis_result.get("sentiment_analysis", {}),
                        "urgency": analysis_result.get("urgency_detection", {}),
                        "skills": analysis_result.get("skill_classification", []),
                        "collaboration": analysis_result.get("collaboration_patterns", {}),
                        "productivity": analysis_result.get("productivity_indicators", {})
                    }
                )
                db.add(work_item)
                created_items.append(work_item)
            
            db.commit()
            logger.info(f"Created {len(created_items)} work items from enhanced analysis")
            
            return {
                "success": True,
                "work_items_created": len(created_items),
                "analysis_summary": {
                    "sentiment": analysis_result.get("sentiment_analysis", {}),
                    "urgency_level": analysis_result.get("urgency_detection", {}).get("urgency_level", "medium"),
                    "skills_detected": analysis_result.get("skill_classification", []),
                    "productivity_score": analysis_result.get("productivity_indicators", {}).get("productivity_score", 0)
                }
            }
            
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Enhanced content analysis failed: {e}")
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying enhanced content analysis (attempt {self.request.retries + 1})")
            raise self.retry(countdown=60 * (self.request.retries + 1))
        return {"success": False, "error": str(e)}

@celery_app.task(base=AIProcessingTask, bind=True, max_retries=3)
def intelligent_task_categorization_batch(self, work_item_ids: List[str]):
    """
    Intelligent batch categorization of work items.
    
    Args:
        work_item_ids: List of work item IDs to categorize
    """
    try:
        logger.info(f"Starting intelligent categorization for {len(work_item_ids)} work items")
        
        ai_service = AIService()
        db = next(get_db())
        
        try:
            categorized_count = 0
            
            for work_item_id in work_item_ids:
                work_item = db.query(WorkItem).filter(WorkItem.id == work_item_id).first()
                if not work_item:
                    continue
                
                # Get enhanced categorization
                categorization = asyncio.run(
                    ai_service.intelligent_task_categorization(
                        task_description=work_item.description,
                        context={
                            "activity_type": work_item.activity_type,
                            "priority": work_item.priority,
                            "project_reference": work_item.project_reference
                        }
                    )
                )
                
                # Update work item with categorization
                work_item.analysis_metadata = work_item.analysis_metadata or {}
                work_item.analysis_metadata["categorization"] = categorization
                
                # Update fields based on categorization
                if categorization.get("priority") and categorization.get("confidence", 0) > 0.7:
                    work_item.priority = categorization["priority"]
                
                if categorization.get("category"):
                    work_item.activity_type = categorization["category"]
                
                categorized_count += 1
            
            db.commit()
            logger.info(f"Successfully categorized {categorized_count} work items")
            
            return {
                "success": True,
                "categorized_count": categorized_count,
                "total_requested": len(work_item_ids)
            }
            
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Intelligent categorization failed: {e}")
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying categorization (attempt {self.request.retries + 1})")
            raise self.retry(countdown=60 * (self.request.retries + 1))
        return {"success": False, "error": str(e)}

@celery_app.task(base=AIProcessingTask, bind=True, max_retries=3)
def enhanced_time_estimation_batch(self, work_item_ids: List[str], user_id: str):
    """
    Enhanced time estimation for work items using historical data.
    
    Args:
        work_item_ids: List of work item IDs to estimate
        user_id: User ID for personalized estimation
    """
    try:
        logger.info(f"Starting enhanced time estimation for {len(work_item_ids)} work items")
        
        ai_service = AIService()
        db = next(get_db())
        
        try:
            estimated_count = 0
            
            for work_item_id in work_item_ids:
                work_item = db.query(WorkItem).filter(WorkItem.id == work_item_id).first()
                if not work_item:
                    continue
                
                # Get enhanced time estimation
                estimation = asyncio.run(
                    ai_service.enhanced_time_estimation(
                        task_description=work_item.description,
                        context={
                            "activity_type": work_item.activity_type,
                            "priority": work_item.priority,
                            "project_reference": work_item.project_reference
                        },
                        user_id=user_id,
                        use_historical_data=True
                    )
                )
                
                # Update work item with estimation
                work_item.analysis_metadata = work_item.analysis_metadata or {}
                work_item.analysis_metadata["time_estimation"] = estimation
                
                # Update estimated time if confidence is high
                confidence = estimation.get("confidence_interval", {}).get("confidence", 0)
                if confidence > 0.7:
                    work_item.estimated_time = estimation.get("estimated_hours", work_item.estimated_time)
                
                estimated_count += 1
            
            db.commit()
            logger.info(f"Successfully estimated time for {estimated_count} work items")
            
            return {
                "success": True,
                "estimated_count": estimated_count,
                "total_requested": len(work_item_ids)
            }
            
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Enhanced time estimation failed: {e}")
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying time estimation (attempt {self.request.retries + 1})")
            raise self.retry(countdown=60 * (self.request.retries + 1))
        return {"success": False, "error": str(e)}

@celery_app.task(base=AIProcessingTask, bind=True, max_retries=3)
def automated_jira_work_logging(self, user_id: str, work_item_ids: List[str]):
    """
    Automated JIRA work logging with intelligent time distribution.
    
    Args:
        user_id: User ID
        work_item_ids: List of work item IDs to log
    """
    try:
        logger.info(f"Starting automated JIRA work logging for {len(work_item_ids)} work items")
        
        ai_service = AIService()
        db = next(get_db())
        
        try:
            # Get user and work items
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "error": "User not found"}
            
            work_items = db.query(WorkItem).filter(WorkItem.id.in_(work_item_ids)).all()
            if not work_items:
                return {"success": False, "error": "No work items found"}
            
            # Get available JIRA tickets
            jira_tickets = db.query(JIRATicket).filter(JIRATicket.user_id == user_id).all()
            jira_tickets_data = [
                {
                    "ticket_key": ticket.ticket_key,
                    "title": ticket.title,
                    "description": ticket.description,
                    "status": ticket.status,
                    "priority": ticket.priority
                }
                for ticket in jira_tickets
            ]
            
            # Prepare work items data
            work_items_data = [
                {
                    "description": item.description,
                    "activity_type": item.activity_type,
                    "estimated_time": item.estimated_time,
                    "priority": item.priority,
                    "project_reference": item.project_reference
                }
                for item in work_items
            ]
            
            # Get user preferences
            user_preferences = user.preferences or {}
            
            # Run automated work logging
            logging_result = asyncio.run(
                ai_service.automated_jira_work_logging(
                    work_items=work_items_data,
                    jira_tickets=jira_tickets_data,
                    user_preferences=user_preferences
                )
            )
            
            # Process recommendations
            recommendations = logging_result.get("recommendations", [])
            auto_logged_count = 0
            
            for i, recommendation in enumerate(recommendations):
                if i >= len(work_items):
                    break
                
                work_item = work_items[i]
                action = recommendation.get("recommended_action", "manual_review")
                
                # Store recommendation in work item metadata
                work_item.analysis_metadata = work_item.analysis_metadata or {}
                work_item.analysis_metadata["jira_logging"] = {
                    "recommendation": recommendation,
                    "processed_at": datetime.now().isoformat()
                }
                
                if action == "auto_log":
                    # Mark as automatically logged
                    work_item.analysis_metadata["jira_logging"]["auto_logged"] = True
                    auto_logged_count += 1
            
            db.commit()
            
            logger.info(f"Processed JIRA work logging: {auto_logged_count} auto-logged, {len(recommendations)} total recommendations")
            
            return {
                "success": True,
                "auto_logged_count": auto_logged_count,
                "total_recommendations": len(recommendations),
                "automation_rate": logging_result.get("automation_rate", 0),
                "total_time_logged": logging_result.get("total_time_logged", 0)
            }
            
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Automated JIRA work logging failed: {e}")
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying JIRA work logging (attempt {self.request.retries + 1})")
            raise self.retry(countdown=60 * (self.request.retries + 1))
        return {"success": False, "error": str(e)}

@celery_app.task(base=AIProcessingTask, bind=True, max_retries=3)
def generate_productivity_analytics(self, user_id: str, timeframe: str = "daily", date: Optional[str] = None):
    """
    Generate comprehensive productivity analytics and insights.
    
    Args:
        user_id: User ID
        timeframe: Analysis timeframe (daily, weekly, monthly)
        date: Specific date for analysis (optional)
    """
    try:
        logger.info(f"Starting productivity analytics generation for user {user_id}, timeframe: {timeframe}")
        
        ai_service = AIService()
        db = next(get_db())
        
        try:
            # Calculate date range
            if date:
                target_date = datetime.fromisoformat(date)
            else:
                target_date = datetime.now()
            
            if timeframe == "daily":
                start_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = start_date + timedelta(days=1)
            elif timeframe == "weekly":
                start_date = target_date - timedelta(days=target_date.weekday())
                start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = start_date + timedelta(days=7)
            elif timeframe == "monthly":
                start_date = target_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                if target_date.month == 12:
                    end_date = start_date.replace(year=target_date.year + 1, month=1)
                else:
                    end_date = start_date.replace(month=target_date.month + 1)
            else:
                raise ValueError(f"Invalid timeframe: {timeframe}")
            
            # Get work items for the period
            work_items = db.query(WorkItem).filter(
                WorkItem.user_id == user_id,
                WorkItem.created_at >= start_date,
                WorkItem.created_at < end_date
            ).all()
            
            # Prepare work items data
            work_items_data = [
                {
                    "description": item.description,
                    "activity_type": item.activity_type,
                    "estimated_time": item.estimated_time,
                    "priority": item.priority,
                    "project_reference": item.project_reference,
                    "created_at": item.created_at.isoformat(),
                    "analysis_metadata": item.analysis_metadata or {}
                }
                for item in work_items
            ]
            
            # Generate productivity analytics
            analytics = asyncio.run(
                ai_service.productivity_analytics(
                    work_items=work_items_data,
                    timeframe=timeframe,
                    user_id=user_id
                )
            )
            
            # Create or update report
            report_date = start_date.date()
            existing_report = db.query(Report).filter(
                Report.user_id == user_id,
                Report.report_date == report_date,
                Report.report_type == f"productivity_{timeframe}"
            ).first()
            
            if existing_report:
                existing_report.content = analytics
                existing_report.updated_at = datetime.now()
                report = existing_report
            else:
                report = Report(
                    user_id=user_id,
                    report_type=f"productivity_{timeframe}",
                    report_date=report_date,
                    content=analytics
                )
                db.add(report)
            
            db.commit()
            
            logger.info(f"Generated productivity analytics for {len(work_items)} work items")
            
            return {
                "success": True,
                "analytics": analytics,
                "work_items_analyzed": len(work_items),
                "report_id": str(report.id),
                "period": f"{start_date.date()} to {end_date.date()}"
            }
            
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Productivity analytics generation failed: {e}")
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying productivity analytics (attempt {self.request.retries + 1})")
            raise self.retry(countdown=60 * (self.request.retries + 1))
        return {"success": False, "error": str(e)}

@celery_app.task(base=AIProcessingTask, bind=True)
def process_all_pending_ai_analysis(self, user_id: str):
    """
    Process all pending AI analysis for a user.
    
    Args:
        user_id: User ID
    """
    try:
        logger.info(f"Starting comprehensive AI processing for user {user_id}")
        
        db = next(get_db())
        
        try:
            # Get recent messages without work items
            recent_messages = db.query(Message).filter(
                Message.user_id == user_id,
                Message.created_at >= datetime.now() - timedelta(hours=24)
            ).limit(50).all()
            
            # Get work items needing categorization
            work_items_needing_categorization = db.query(WorkItem).filter(
                WorkItem.user_id == user_id,
                WorkItem.analysis_metadata.is_(None)
            ).limit(20).all()
            
            results = {
                "messages_processed": 0,
                "work_items_categorized": 0,
                "work_items_estimated": 0,
                "analytics_generated": 0
            }
            
            # Process recent messages
            for message in recent_messages:
                try:
                    enhanced_content_analysis.delay(
                        user_id=user_id,
                        content=message.content,
                        context={
                            "source": message.source,
                            "sender": message.sender,
                            "timestamp": message.timestamp.isoformat() if message.timestamp else None
                        }
                    )
                    results["messages_processed"] += 1
                except Exception as e:
                    logger.error(f"Failed to process message {message.id}: {e}")
            
            # Process work items needing categorization
            if work_items_needing_categorization:
                work_item_ids = [str(item.id) for item in work_items_needing_categorization]
                
                # Categorization
                intelligent_task_categorization_batch.delay(work_item_ids)
                results["work_items_categorized"] = len(work_item_ids)
                
                # Time estimation
                enhanced_time_estimation_batch.delay(work_item_ids, user_id)
                results["work_items_estimated"] = len(work_item_ids)
                
                # JIRA work logging
                automated_jira_work_logging.delay(user_id, work_item_ids)
            
            # Generate productivity analytics
            for timeframe in ["daily", "weekly"]:
                generate_productivity_analytics.delay(user_id, timeframe)
                results["analytics_generated"] += 1
            
            logger.info(f"Initiated comprehensive AI processing for user {user_id}: {results}")
            
            return {
                "success": True,
                "initiated_tasks": results
            }
            
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Comprehensive AI processing failed: {e}")
        return {"success": False, "error": str(e)}

# Scheduled tasks for Phase 3
@celery_app.task(base=AIProcessingTask)
def scheduled_ai_analysis():
    """Scheduled task to run AI analysis for all active users."""
    try:
        logger.info("Starting scheduled AI analysis for all users")
        
        db = next(get_db())
        
        try:
            # Get all active users
            active_users = db.query(User).filter(User.is_active == True).all()
            
            for user in active_users:
                # Process AI analysis for each user
                process_all_pending_ai_analysis.delay(str(user.id))
            
            logger.info(f"Initiated AI analysis for {len(active_users)} active users")
            
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Scheduled AI analysis failed: {e}")

@celery_app.task(base=AIProcessingTask)
def scheduled_productivity_analytics():
    """Scheduled task to generate productivity analytics for all users."""
    try:
        logger.info("Starting scheduled productivity analytics generation")
        
        db = next(get_db())
        
        try:
            # Get all active users
            active_users = db.query(User).filter(User.is_active == True).all()
            
            for user in active_users:
                # Generate daily analytics
                generate_productivity_analytics.delay(str(user.id), "daily")
                
                # Generate weekly analytics on Mondays
                if datetime.now().weekday() == 0:
                    generate_productivity_analytics.delay(str(user.id), "weekly")
                
                # Generate monthly analytics on first day of month
                if datetime.now().day == 1:
                    generate_productivity_analytics.delay(str(user.id), "monthly")
            
            logger.info(f"Initiated productivity analytics for {len(active_users)} active users")
            
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Scheduled productivity analytics failed: {e}")

# Legacy tasks with enhanced processing
@celery_app.task(base=AIProcessingTask, bind=True, max_retries=3)
def process_pending_analysis(self, user_id: Optional[str] = None):
    """
    Enhanced version of the original process_pending_analysis task.
    
    Args:
        user_id: Optional user ID to process specific user
    """
    try:
        logger.info(f"Processing pending analysis for user: {user_id if user_id else 'all users'}")
        
        if user_id:
            # Process specific user with enhanced analysis
            result = process_all_pending_ai_analysis.delay(user_id)
            return {"success": True, "task_id": result.id}
        else:
            # Process all users
            scheduled_ai_analysis.delay()
            return {"success": True, "message": "Initiated analysis for all users"}
    
    except Exception as e:
        logger.error(f"Process pending analysis failed: {e}")
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (self.request.retries + 1))
        return {"success": False, "error": str(e)}

@celery_app.task(base=AIProcessingTask, bind=True, max_retries=3)
def match_work_items_to_jira(self, user_id: str):
    """
    Enhanced JIRA matching with automated work logging.
    
    Args:
        user_id: User ID
    """
    try:
        logger.info(f"Matching work items to JIRA for user {user_id}")
        
        db = next(get_db())
        
        try:
            # Get recent work items
            recent_work_items = db.query(WorkItem).filter(
                WorkItem.user_id == user_id,
                WorkItem.created_at >= datetime.now() - timedelta(hours=24)
            ).limit(50).all()
            
            if recent_work_items:
                work_item_ids = [str(item.id) for item in recent_work_items]
                
                # Use enhanced automated work logging
                result = automated_jira_work_logging.delay(user_id, work_item_ids)
                
                return {
                    "success": True,
                    "work_items_processed": len(work_item_ids),
                    "task_id": result.id
                }
            else:
                return {
                    "success": True,
                    "work_items_processed": 0,
                    "message": "No recent work items found"
                }
                
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"JIRA work item matching failed: {e}")
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (self.request.retries + 1))
        return {"success": False, "error": str(e)}

@celery_app.task(base=AIProcessingTask, bind=True, max_retries=3)
def generate_daily_reports(self, user_id: Optional[str] = None):
    """
    Enhanced daily report generation with productivity analytics.
    
    Args:
        user_id: Optional user ID to generate report for specific user
    """
    try:
        logger.info(f"Generating daily reports for user: {user_id if user_id else 'all users'}")
        
        if user_id:
            # Generate comprehensive report for specific user
            result = generate_productivity_analytics.delay(user_id, "daily")
            return {"success": True, "task_id": result.id}
        else:
            # Generate reports for all users
            scheduled_productivity_analytics.delay()
            return {"success": True, "message": "Initiated daily reports for all users"}
    
    except Exception as e:
        logger.error(f"Daily report generation failed: {e}")
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (self.request.retries + 1))
        return {"success": False, "error": str(e)}

# ==================== PHASE 4: COMPREHENSIVE REPORT GENERATION TASKS ====================

@celery_app.task(base=AIProcessingTask, bind=True, max_retries=3)
def generate_report_task(
    self,
    user_id: str,
    report_type: str,
    report_date: str,
    week_start_date: Optional[str] = None,
    template: Optional[str] = None,
    auto_approve: bool = False,
    send_to_jira: bool = False
):
    """Background task for generating comprehensive reports"""
    import asyncio
    
    async def _generate_report():
        from app.services.report_service import ReportService
        from datetime import datetime, timedelta
        from uuid import UUID
        
        db = next(get_db())
        try:
            report_service = ReportService(db)
            report_date_obj = datetime.fromisoformat(report_date).date()
            
            if report_type == "daily":
                report = await report_service.generate_daily_report(
                    user_id=UUID(user_id),
                    report_date=report_date_obj,
                    template=template,
                    auto_approve=auto_approve
                )
            elif report_type == "weekly":
                week_start_obj = datetime.fromisoformat(week_start_date).date() if week_start_date else report_date_obj
                if week_start_obj.weekday() != 0:
                    week_start_obj = week_start_obj - timedelta(days=week_start_obj.weekday())
                
                report = await report_service.generate_weekly_report(
                    user_id=UUID(user_id),
                    week_start=week_start_obj,
                    template=template,
                    auto_approve=auto_approve
                )
            else:
                raise ValueError(f"Invalid report type: {report_type}")
            
            # Send to JIRA if requested
            if send_to_jira and report.jira_updates:
                jira_result = await report_service.send_report_to_jira(
                    report.id, UUID(user_id)
                )
                logger.info(f"JIRA update result: {jira_result}")
            
            logger.info(f"Report {report.id} generated successfully")
            return {
                "success": True,
                "report_id": str(report.id),
                "report_type": report_type,
                "status": report.status,
                "total_work_items": report.total_work_items,
                "total_hours": report.total_hours
            }
            
        finally:
            db.close()
    
    try:
        logger.info(f"Generating {report_type} report for user {user_id}")
        return asyncio.run(_generate_report())
            
    except Exception as exc:
        logger.error(f"Report generation failed: {exc}")
        if self.request.retries < self.max_retries:
            self.retry(countdown=60 * (2 ** self.request.retries), exc=exc)
        raise

@celery_app.task(base=AIProcessingTask, bind=True, max_retries=3)
def send_jira_updates_task(self, report_id: str, user_id: str):
    """Background task for sending report updates to JIRA"""
    import asyncio
    
    async def _send_jira_updates():
        from app.services.report_service import ReportService
        from uuid import UUID
        
        db = next(get_db())
        try:
            report_service = ReportService(db)
            
            result = await report_service.send_report_to_jira(
                UUID(report_id), UUID(user_id)
            )
            
            logger.info(f"JIRA updates completed: {result}")
            return result
            
        finally:
            db.close()
    
    try:
        logger.info(f"Sending JIRA updates for report {report_id}")
        return asyncio.run(_send_jira_updates())
            
    except Exception as exc:
        logger.error(f"JIRA update failed: {exc}")
        if self.request.retries < self.max_retries:
            self.retry(countdown=60 * (2 ** self.request.retries), exc=exc)
        raise 