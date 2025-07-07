"""
Data Management API Routes - Daily Logger Assist

API endpoints for managing data collection, work items, and processing.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database.connection import get_db
from app.dependencies import get_current_user, CommonQueryParams
from app.models.user import User
from app.schemas.work_item import WorkItemCreate, WorkItemResponse, WorkItemUpdate
from loguru import logger

router = APIRouter()

@router.post("/sync/teams")
async def sync_teams_data(
    since_hours: int = 24,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Sync data from Microsoft Teams"""
    logger.info(f"Teams sync requested for user {current_user.id}")
    
    if not current_user.teams_credentials:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Teams not connected. Please connect Teams first."
        )
    
    try:
        from app.tasks.data_collection import collect_teams_data
        
        # Start background task for Teams data collection
        task_result = collect_teams_data.delay(str(current_user.id), since_hours)
        
        return {
            "status": "started",
            "message": "Teams data collection started",
            "task_id": task_result.id,
            "user_id": str(current_user.id),
            "since_hours": since_hours
        }
        
    except Exception as e:
        logger.error(f"Teams sync failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Teams data sync failed"
        )

@router.post("/sync/email")
async def sync_email_data(
    since_hours: int = 24,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Sync data from email"""
    logger.info(f"Email sync requested for user {current_user.id}")
    
    if not current_user.email_credentials:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not connected. Please connect email first."
        )
    
    try:
        from app.tasks.data_collection import collect_email_data
        
        # Start background task for email data collection
        task_result = collect_email_data.delay(str(current_user.id), since_hours)
        
        return {
            "status": "started",
            "message": "Email data collection started",
            "task_id": task_result.id,
            "user_id": str(current_user.id),
            "since_hours": since_hours
        }
        
    except Exception as e:
        logger.error(f"Email sync failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Email data sync failed"
        )

@router.post("/sync/jira")
async def sync_jira_data(
    since_hours: int = 24,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Sync JIRA tickets"""
    logger.info(f"JIRA sync requested for user {current_user.id}")
    
    if not current_user.jira_credentials:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="JIRA not connected. Please connect JIRA first."
        )
    
    try:
        from app.tasks.data_collection import collect_jira_data
        
        # Start background task for JIRA data collection
        task_result = collect_jira_data.delay(str(current_user.id), since_hours)
        
        return {
            "status": "started",
            "message": "JIRA data collection started",
            "task_id": task_result.id,
            "user_id": str(current_user.id),
            "since_hours": since_hours
        }
        
    except Exception as e:
        logger.error(f"JIRA sync failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="JIRA data sync failed"
        )

@router.get("/sync/status")
async def get_sync_status(
    current_user: User = Depends(get_current_user)
):
    """Get data sync status"""
    # TODO: Implement actual sync status checking
    return {
        "user_id": str(current_user.id),
        "teams_sync": {
            "status": "idle",
            "last_sync": None,
            "next_sync": None
        },
        "email_sync": {
            "status": "idle", 
            "last_sync": None,
            "next_sync": None
        },
        "jira_sync": {
            "status": "idle",
            "last_sync": None,
            "next_sync": None
        }
    }

@router.post("/process")
async def process_collected_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process collected data with AI"""
    logger.info(f"Data processing requested for user {current_user.id}")
    
    try:
        from app.tasks.ai_processing import process_pending_analysis, match_work_items_to_jira
        
        # Start AI analysis task
        analysis_task = process_pending_analysis.delay(str(current_user.id))
        
        # Start JIRA matching task
        matching_task = match_work_items_to_jira.delay(str(current_user.id))
        
        return {
            "status": "started",
            "message": "Data processing initiated",
            "analysis_task_id": analysis_task.id,
            "matching_task_id": matching_task.id,
            "user_id": str(current_user.id),
            "estimated_completion": "5 minutes"
        }
        
    except Exception as e:
        logger.error(f"Data processing failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Data processing failed"
        ) 