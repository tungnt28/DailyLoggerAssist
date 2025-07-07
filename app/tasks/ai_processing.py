"""
AI Processing Tasks - Daily Logger Assist

Celery tasks for AI-powered content analysis and report generation.
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta
from celery import current_task
from loguru import logger
from sqlalchemy.orm import Session
import asyncio

from app.tasks.celery_app import celery_app
from app.database.connection import get_db
from app.models.user import User
from app.models.message import Message
from app.models.work_item import WorkItem
from app.models.jira_ticket import JIRATicket
from app.models.report import Report
from app.services.ai_service import AIService

@celery_app.task(bind=True)
def process_pending_analysis(self, user_id: str = None):
    """
    Process pending messages for AI analysis.
    
    Args:
        user_id: Optional specific user ID, otherwise process for all users
    """
    try:
        logger.info(f"Starting AI analysis processing (user_id={user_id})")
        
        db = next(get_db())
        
        if user_id:
            users = [db.query(User).filter(User.id == user_id).first()]
            if not users[0]:
                return {"status": "error", "message": "User not found"}
        else:
            users = db.query(User).filter(User.is_active == True).all()
        
        ai_service = AIService()
        total_processed = 0
        
        for user in users:
            try:
                # Get unprocessed messages from last 48 hours
                since = datetime.utcnow() - timedelta(hours=48)
                unprocessed_messages = db.query(Message).filter(
                    Message.user_id == user.id,
                    Message.message_timestamp >= since,
                    Message.processed_at.is_(None)
                ).limit(50).all()  # Limit to prevent overload
                
                user_processed = 0
                
                for message in unprocessed_messages:
                    try:
                        # Analyze message for work items
                        context = {
                            "sender": message.sender,
                            "timestamp": message.message_timestamp.isoformat(),
                            "source": message.source
                        }
                        
                        work_items_data = asyncio.run(
                            ai_service.analyze_content_for_work_items(
                                message.content, context
                            )
                        )
                        
                        # Create work items
                        for item_data in work_items_data:
                            work_item = WorkItem(
                                user_id=user.id,
                                message_id=message.id,
                                activity_type=item_data["activity_type"],
                                description=item_data["description"],
                                estimated_time=item_data["estimated_time"],
                                project_reference=item_data.get("project_reference"),
                                priority=item_data["priority"],
                                work_metadata={"ai_generated": True, "source": "message_analysis"}
                            )
                            db.add(work_item)
                        
                        # Mark message as processed
                        message.processed_at = datetime.utcnow()
                        user_processed += 1
                        
                    except Exception as e:
                        logger.error(f"Error processing message {message.id}: {e}")
                        continue
                
                total_processed += user_processed
                logger.info(f"Processed {user_processed} messages for user {user.id}")
                
            except Exception as e:
                logger.error(f"Error processing messages for user {user.id}: {e}")
                continue
        
        db.commit()
        db.close()
        
        result = {
            "status": "success",
            "total_processed": total_processed,
            "users_count": len(users)
        }
        
        logger.info(f"AI analysis completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"AI analysis processing failed: {e}")
        return {"status": "error", "message": str(e)}

@celery_app.task(bind=True)
def match_work_items_to_jira(self, user_id: str):
    """
    Match work items to JIRA tickets using AI.
    
    Args:
        user_id: User ID to process
    """
    try:
        logger.info(f"Starting work item JIRA matching for user {user_id}")
        
        db = next(get_db())
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            return {"status": "error", "message": "User not found"}
        
        # Get unmatched work items from last 7 days
        since = datetime.utcnow() - timedelta(days=7)
        unmatched_items = db.query(WorkItem).filter(
            WorkItem.user_id == user.id,
            WorkItem.created_at >= since,
            WorkItem.jira_ticket_id.is_(None)
        ).limit(20).all()
        
        if not unmatched_items:
            return {"status": "success", "message": "No unmatched work items"}
        
        # Get user's JIRA tickets
        jira_tickets = db.query(JIRATicket).filter(
            JIRATicket.user_id == user.id
        ).all()
        
        if not jira_tickets:
            return {"status": "success", "message": "No JIRA tickets available for matching"}
        
        ai_service = AIService()
        matched_count = 0
        
        for work_item in unmatched_items:
            try:
                # Prepare ticket data for AI
                tickets_data = []
                for ticket in jira_tickets:
                    tickets_data.append({
                        "ticket_key": ticket.ticket_key,
                        "title": ticket.title,
                        "description": ticket.description[:500] if ticket.description else "",
                        "status": ticket.status,
                        "project_key": ticket.project_key
                    })
                
                # Get AI matches
                matches = asyncio.run(
                    ai_service.match_content_to_jira_tickets(
                        work_item.description, tickets_data
                    )
                )
                
                # Apply best match if confidence is high enough
                if matches and matches[0].get("confidence", 0) > 0.7:
                    best_match = matches[0]
                    ticket_key = best_match["ticket_key"]
                    
                    # Find the actual ticket
                    matching_ticket = next(
                        (t for t in jira_tickets if t.ticket_key == ticket_key), 
                        None
                    )
                    
                    if matching_ticket:
                        work_item.jira_ticket_id = matching_ticket.id
                        work_item.work_metadata = work_item.work_metadata or {}
                        work_item.work_metadata.update({
                            "ai_matched": True,
                            "match_confidence": best_match["confidence"],
                            "match_reasoning": best_match.get("reasoning", "")
                        })
                        matched_count += 1
                        
            except Exception as e:
                logger.error(f"Error matching work item {work_item.id}: {e}")
                continue
        
        db.commit()
        db.close()
        
        result = {
            "status": "success",
            "matched_count": matched_count,
            "total_items": len(unmatched_items),
            "user_id": user_id
        }
        
        logger.info(f"JIRA matching completed for user {user_id}: {result}")
        return result
        
    except Exception as e:
        logger.error(f"JIRA matching failed for user {user_id}: {e}")
        return {"status": "error", "message": str(e), "user_id": user_id}

@celery_app.task(bind=True)
def generate_daily_reports(self, date: str = None, user_id: str = None):
    """
    Generate daily reports for users.
    
    Args:
        date: Date in YYYY-MM-DD format (default: yesterday)
        user_id: Optional specific user ID
    """
    try:
        if date:
            report_date = datetime.strptime(date, "%Y-%m-%d").date()
        else:
            report_date = (datetime.utcnow() - timedelta(days=1)).date()
        
        logger.info(f"Generating daily reports for {report_date} (user_id={user_id})")
        
        db = next(get_db())
        
        if user_id:
            users = [db.query(User).filter(User.id == user_id).first()]
            if not users[0]:
                return {"status": "error", "message": "User not found"}
        else:
            users = db.query(User).filter(User.is_active == True).all()
        
        ai_service = AIService()
        reports_generated = 0
        
        for user in users:
            try:
                # Check if report already exists
                existing_report = db.query(Report).filter(
                    Report.user_id == user.id,
                    Report.report_date == report_date,
                    Report.report_type == "daily"
                ).first()
                
                if existing_report:
                    logger.info(f"Daily report already exists for user {user.id} on {report_date}")
                    continue
                
                # Get work items for the date
                start_datetime = datetime.combine(report_date, datetime.min.time())
                end_datetime = datetime.combine(report_date, datetime.max.time())
                
                work_items = db.query(WorkItem).filter(
                    WorkItem.user_id == user.id,
                    WorkItem.created_at >= start_datetime,
                    WorkItem.created_at <= end_datetime
                ).all()
                
                # Get messages for the date
                messages = db.query(Message).filter(
                    Message.user_id == user.id,
                    Message.message_timestamp >= start_datetime,
                    Message.message_timestamp <= end_datetime
                ).all()
                
                # Prepare data for AI
                work_items_data = []
                for item in work_items:
                    work_items_data.append({
                        "description": item.description,
                        "activity_type": item.activity_type,
                        "estimated_time": item.estimated_time,
                        "priority": item.priority
                    })
                
                messages_data = []
                for msg in messages:
                    messages_data.append({
                        "content": msg.content[:200],  # Truncated for AI processing
                        "sender": msg.sender,
                        "source": msg.source
                    })
                
                # Generate summary using AI
                summary_data = asyncio.run(
                    ai_service.generate_daily_summary(
                        work_items_data, messages_data, start_datetime
                    )
                )
                
                # Create report
                report = Report(
                    user_id=user.id,
                    report_type="daily",
                    report_date=report_date,
                    content=summary_data["summary"],
                    report_metadata={
                        "work_items_count": len(work_items),
                        "messages_count": len(messages),
                        "key_achievements": summary_data.get("key_achievements", []),
                        "time_breakdown": summary_data.get("time_breakdown", {}),
                        "insights": summary_data.get("insights", []),
                        "total_productive_hours": summary_data.get("total_productive_hours", 0),
                        "generated_by": "ai"
                    }
                )
                
                db.add(report)
                reports_generated += 1
                
            except Exception as e:
                logger.error(f"Error generating report for user {user.id}: {e}")
                continue
        
        db.commit()
        db.close()
        
        result = {
            "status": "success",
            "reports_generated": reports_generated,
            "report_date": str(report_date),
            "users_count": len(users)
        }
        
        logger.info(f"Daily report generation completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Daily report generation failed: {e}")
        return {"status": "error", "message": str(e)} 