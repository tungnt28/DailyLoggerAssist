#!/usr/bin/env python3
"""
Phase 2 Testing Script - Daily Logger Assist

Test the new data collection services and background tasks.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.teams_service import TeamsService
from app.services.email_service import EmailService
from app.services.jira_service import JIRAService
from app.services.ai_service import AIService
from app.models.user import User
from datetime import datetime, timedelta

async def test_services():
    """Test all the new services."""
    
    print("🧪 Testing Phase 2 Services...")
    print("=" * 50)
    
    # Test AI Service
    print("\n1. Testing AI Service...")
    ai_service = AIService()
    
    # Test if AI can be called (will fail without API key)
    try:
        test_result = await ai_service.test_connection()
        print(f"   ✅ AI Service: {'Connected' if test_result else 'Not configured (needs API key)'}")
    except Exception as e:
        print(f"   ⚠️  AI Service: Not configured - {str(e)[:100]}")
    
    # Test work item analysis
    sample_content = "Fixed the login bug in PROJ-123. Spent 2 hours debugging the authentication issue."
    try:
        work_items = await ai_service.analyze_content_for_work_items(sample_content)
        print(f"   ✅ Work Analysis: Extracted {len(work_items)} work items")
        if work_items:
            print(f"      Sample: {work_items[0].get('description', 'N/A')}")
    except Exception as e:
        print(f"   ⚠️  Work Analysis: {str(e)[:100]}")
    
    # Test time estimation
    try:
        estimate = await ai_service.estimate_time_for_task("Fix login bug", "development", "medium")
        print(f"   ✅ Time Estimation: {estimate.get('estimated_hours', 0)}h with {estimate.get('confidence', 'unknown')} confidence")
    except Exception as e:
        print(f"   ⚠️  Time Estimation: {str(e)[:100]}")
    
    # Test Teams Service
    print("\n2. Testing Teams Service...")
    teams_service = TeamsService()
    print("   ✅ Teams Service: Initialized (authentication requires credentials)")
    
    # Test Email Service  
    print("\n3. Testing Email Service...")
    email_service = EmailService()
    print("   ✅ Email Service: Initialized (authentication requires credentials)")
    
    # Test JIRA Service
    print("\n4. Testing JIRA Service...")
    jira_service = JIRAService()
    print("   ✅ JIRA Service: Initialized (authentication requires credentials)")
    
    print("\n🎉 Phase 2 Service Tests Complete!")
    print("\nℹ️  Note: Full testing requires:")
    print("   - OpenRoute API key for AI features")
    print("   - Teams/Email/JIRA credentials for data collection")
    print("   - Redis server for Celery tasks")

if __name__ == "__main__":
    asyncio.run(test_services()) 