"""
Data Collection Tasks - Daily Logger Assist

Celery tasks for collecting data from Teams, Email, and JIRA.
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta
from celery import current_task
from loguru import logger
from sqlalchemy.orm import Session

from app.tasks.celery_app import celery_app
from app.database.connection import get_db
from app.models.user import User
from app.models.message import Message
from app.models.jira_ticket import JIRATicket
from app.services.teams_service import TeamsService
from app.services.email_service import EmailService
from app.services.jira_service import JIRAService

@celery_app.task(bind=True)
def collect_teams_data(self, user_id: str, since_hours: int = 24):
    """
    Collect Teams messages for a user.
    
    Args:
        user_id: User ID to collect data for
        since_hours: Hours to look back for data
    """
    try:
        logger.info(f"Starting Teams data collection for user {user_id}")
        
        db = next(get_db())
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            logger.error(f"User {user_id} not found")
            return {"status": "error", "message": "User not found"}
        
        # Calculate since datetime
        since = datetime.utcnow() - timedelta(hours=since_hours)
        
                 # Collect Teams data
        teams_service = TeamsService()
        import asyncio
        messages_data = asyncio.run(teams_service.collect_messages(user, since))
        
        # Store messages in database
        stored_count = 0
        for msg_data in messages_data:
            try:
                # Check if message already exists
                existing = db.query(Message).filter(
                    Message.external_id == msg_data["external_id"],
                    Message.user_id == user.id
                ).first()
                
                if not existing:
                    message = Message(
                        user_id=user.id,
                        external_id=msg_data["external_id"],
                        source=msg_data["source"],
                        channel_id=msg_data["channel_id"],
                        thread_id=msg_data.get("thread_id"),
                        content=msg_data["content"],
                        sender=msg_data["sender"],
                        message_timestamp=msg_data["message_timestamp"],
                        message_metadata=msg_data["metadata"]
                    )
                    db.add(message)
                    stored_count += 1
                    
            except Exception as e:
                logger.error(f"Error storing message {msg_data.get('external_id')}: {e}")
                continue
        
        db.commit()
        db.close()
        
        result = {
            "status": "success",
            "collected_count": len(messages_data),
            "stored_count": stored_count,
            "user_id": user_id
        }
        
        logger.info(f"Teams collection completed for user {user_id}: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Teams data collection failed for user {user_id}: {e}")
        return {"status": "error", "message": str(e), "user_id": user_id}

@celery_app.task(bind=True)
def collect_email_data(self, user_id: str, since_hours: int = 24):
    """
    Collect email messages for a user.
    
    Args:
        user_id: User ID to collect data for
        since_hours: Hours to look back for data
    """
    try:
        logger.info(f"Starting email data collection for user {user_id}")
        
        db = next(get_db())
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            logger.error(f"User {user_id} not found")
            return {"status": "error", "message": "User not found"}
        
        # Calculate since datetime
        since = datetime.utcnow() - timedelta(hours=since_hours)
        
                 # Collect email data
        email_service = EmailService()
        import asyncio
        messages_data = asyncio.run(email_service.collect_messages(user, since))
        
        # Store messages in database
        stored_count = 0
        for msg_data in messages_data:
            try:
                # Check if message already exists
                existing = db.query(Message).filter(
                    Message.external_id == msg_data["external_id"],
                    Message.user_id == user.id
                ).first()
                
                if not existing:
                    message = Message(
                        user_id=user.id,
                        external_id=msg_data["external_id"],
                        source=msg_data["source"],
                        channel_id=msg_data["channel_id"],
                        thread_id=msg_data.get("thread_id"),
                        content=msg_data["content"],
                        sender=msg_data["sender"],
                        message_timestamp=msg_data["message_timestamp"],
                        message_metadata=msg_data["metadata"]
                    )
                    db.add(message)
                    stored_count += 1
                    
            except Exception as e:
                logger.error(f"Error storing email {msg_data.get('external_id')}: {e}")
                continue
        
        db.commit()
        db.close()
        
        result = {
            "status": "success",
            "collected_count": len(messages_data),
            "stored_count": stored_count,
            "user_id": user_id
        }
        
        logger.info(f"Email collection completed for user {user_id}: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Email data collection failed for user {user_id}: {e}")
        return {"status": "error", "message": str(e), "user_id": user_id}

@celery_app.task(bind=True)
def collect_jira_data(self, user_id: str, since_hours: int = 24):
    """
    Collect JIRA tickets for a user.
    
    Args:
        user_id: User ID to collect data for
        since_hours: Hours to look back for data
    """
    try:
        logger.info(f"Starting JIRA data collection for user {user_id}")
        
        db = next(get_db())
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            logger.error(f"User {user_id} not found")
            return {"status": "error", "message": "User not found"}
        
        # Calculate since datetime
        since = datetime.utcnow() - timedelta(hours=since_hours)
        
                 # Collect JIRA data
        jira_service = JIRAService()
        import asyncio
        tickets_data = asyncio.run(jira_service.get_user_tickets(user, since))
        
        # Store tickets in database
        stored_count = 0
        updated_count = 0
        
        for ticket_data in tickets_data:
            try:
                # Check if ticket already exists
                existing = db.query(JIRATicket).filter(
                    JIRATicket.ticket_key == ticket_data["ticket_key"],
                    JIRATicket.user_id == user.id
                ).first()
                
                if existing:
                    # Update existing ticket
                    for key, value in ticket_data.items():
                        if hasattr(existing, key) and key not in ['id', 'created_at']:
                            setattr(existing, key, value)
                    updated_count += 1
                else:
                    # Create new ticket
                    ticket = JIRATicket(
                        user_id=user.id,
                        **ticket_data
                    )
                    db.add(ticket)
                    stored_count += 1
                    
            except Exception as e:
                logger.error(f"Error storing JIRA ticket {ticket_data.get('ticket_key')}: {e}")
                continue
        
        db.commit()
        db.close()
        
        result = {
            "status": "success",
            "collected_count": len(tickets_data),
            "stored_count": stored_count,
            "updated_count": updated_count,
            "user_id": user_id
        }
        
        logger.info(f"JIRA collection completed for user {user_id}: {result}")
        return result
        
    except Exception as e:
        logger.error(f"JIRA data collection failed for user {user_id}: {e}")
        return {"status": "error", "message": str(e), "user_id": user_id}

@celery_app.task(bind=True)
def collect_all_data(self, user_id: str = None, since_hours: int = 24):
    """
    Collect data from all sources for a user or all users.
    
    Args:
        user_id: Optional specific user ID, otherwise collect for all users
        since_hours: Hours to look back for data
    """
    try:
        logger.info(f"Starting full data collection (user_id={user_id})")
        
        db = next(get_db())
        
        if user_id:
            users = [db.query(User).filter(User.id == user_id).first()]
            if not users[0]:
                return {"status": "error", "message": "User not found"}
        else:
            users = db.query(User).filter(User.is_active == True).all()
        
        db.close()
        
        results = []
        
        for user in users:
            user_results = {
                "user_id": str(user.id),
                "teams": {"status": "skipped"},
                "email": {"status": "skipped"},
                "jira": {"status": "skipped"}
            }
            
            # Collect Teams data if user has credentials
            if user.teams_credentials:
                try:
                    teams_result = collect_teams_data.delay(str(user.id), since_hours)
                    user_results["teams"] = {"task_id": teams_result.id, "status": "started"}
                except Exception as e:
                    user_results["teams"] = {"status": "error", "message": str(e)}
            
            # Collect email data if user has credentials
            if user.email_credentials:
                try:
                    email_result = collect_email_data.delay(str(user.id), since_hours)
                    user_results["email"] = {"task_id": email_result.id, "status": "started"}
                except Exception as e:
                    user_results["email"] = {"status": "error", "message": str(e)}
            
            # Collect JIRA data if user has credentials
            if user.jira_credentials:
                try:
                    jira_result = collect_jira_data.delay(str(user.id), since_hours)
                    user_results["jira"] = {"task_id": jira_result.id, "status": "started"}
                except Exception as e:
                    user_results["jira"] = {"status": "error", "message": str(e)}
            
            results.append(user_results)
        
        return {
            "status": "success",
            "message": f"Data collection started for {len(users)} users",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Full data collection failed: {e}")
        return {"status": "error", "message": str(e)} 