"""
JIRA Service - Daily Logger Assist

Service for collecting and managing JIRA tickets and work logs.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import aiohttp
import asyncio
import base64
from loguru import logger

from app.config import settings
from app.utils.auth import decrypt_credentials
from app.models.jira_ticket import JIRATicket
from app.models.user import User

class JIRAService:
    """JIRA integration service"""
    
    def __init__(self):
        self.base_url = None  # Will be set from user credentials
        
    async def authenticate(self, user: User) -> Optional[Dict[str, str]]:
        """
        Authenticate with JIRA and return auth headers.
        
        Args:
            user: User with JIRA credentials
            
        Returns:
            Optional[Dict[str, str]]: Auth headers if successful
        """
        if not user.jira_credentials:
            logger.warning(f"No JIRA credentials for user {user.id}")
            return None
            
        try:
            credentials = decrypt_credentials(user.jira_credentials)
            if not credentials:
                logger.error(f"Failed to decrypt JIRA credentials for user {user.id}")
                return None
                
            server_url = credentials.get("server_url")
            username = credentials.get("username")
            api_token = credentials.get("api_token")
            
            if not all([server_url, username, api_token]):
                logger.error(f"Missing JIRA credentials for user {user.id}")
                return None
            
            # Set base URL
            self.base_url = server_url.rstrip('/')
            
            # Create basic auth header
            auth_string = f"{username}:{api_token}"
            auth_bytes = auth_string.encode('ascii')
            auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
            
            headers = {
                "Authorization": f"Basic {auth_b64}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            return headers
            
        except Exception as e:
            logger.error(f"JIRA authentication failed for user {user.id}: {e}")
            return None
    
    async def get_user_tickets(
        self,
        user: User,
        since: Optional[datetime] = None,
        project_keys: Optional[List[str]] = None,
        statuses: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get JIRA tickets assigned to or reported by the user.
        
        Args:
            user: User to get tickets for
            since: Get tickets updated since this datetime
            project_keys: Optional list of project keys to filter by
            statuses: Optional list of statuses to filter by
            
        Returns:
            List[Dict[str, Any]]: List of ticket data
        """
        try:
            headers = await self.authenticate(user)
            if not headers:
                return []
            
            # Get user's JIRA account info
            user_info = await self._get_current_user(headers)
            if not user_info:
                logger.error(f"Could not get JIRA user info for user {user.id}")
                return []
            
            jira_username = user_info.get("accountId") or user_info.get("name")
            
            # Build JQL query
            jql_parts = [
                f"(assignee = '{jira_username}' OR reporter = '{jira_username}')"
            ]
            
            if since:
                since_str = since.strftime("%Y-%m-%d %H:%M")
                jql_parts.append(f"updated >= '{since_str}'")
            
            if project_keys:
                project_filter = " OR ".join([f"project = '{key}'" for key in project_keys])
                jql_parts.append(f"({project_filter})")
            
            if statuses:
                status_filter = " OR ".join([f"status = '{status}'" for status in statuses])
                jql_parts.append(f"({status_filter})")
            
            jql = " AND ".join(jql_parts)
            
            # Search for tickets
            search_url = f"{self.base_url}/rest/api/3/search"
            params = {
                "jql": jql,
                "fields": "summary,description,status,priority,assignee,reporter,project,issuetype,labels,components,created,updated,duedate,timeestimate,timespent",
                "maxResults": 100,
                "startAt": 0
            }
            
            tickets = []
            
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for issue in data.get("issues", []):
                            try:
                                ticket_data = self._parse_jira_issue(issue)
                                tickets.append(ticket_data)
                            except Exception as e:
                                logger.error(f"Error parsing JIRA issue {issue.get('key')}: {e}")
                                continue
                                
                    elif response.status == 401:
                        logger.error(f"JIRA authentication failed for user {user.id}")
                    else:
                        logger.error(f"JIRA search failed for user {user.id}: {response.status}")
                        error_text = await response.text()
                        logger.error(f"Error details: {error_text}")
            
            logger.info(f"Retrieved {len(tickets)} JIRA tickets for user {user.id}")
            return tickets
            
        except Exception as e:
            logger.error(f"JIRA ticket retrieval failed for user {user.id}: {e}")
            return []
    
    async def _get_current_user(self, headers: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        Get current JIRA user information.
        
        Args:
            headers: Auth headers
            
        Returns:
            Optional[Dict[str, Any]]: User information
        """
        try:
            url = f"{self.base_url}/rest/api/3/myself"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Failed to get JIRA user info: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error getting JIRA user info: {e}")
            return None
    
    def _parse_jira_issue(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse JIRA issue data into our format.
        
        Args:
            issue: Raw JIRA issue data
            
        Returns:
            Dict[str, Any]: Parsed ticket data
        """
        fields = issue.get("fields", {})
        
        # Extract dates
        created_str = fields.get("created")
        updated_str = fields.get("updated") 
        due_str = fields.get("duedate")
        
        created_at = None
        updated_at = None
        due_date = None
        
        try:
            if created_str:
                created_at = datetime.fromisoformat(created_str.replace('Z', '+00:00'))
        except Exception:
            pass
            
        try:
            if updated_str:
                updated_at = datetime.fromisoformat(updated_str.replace('Z', '+00:00'))
        except Exception:
            pass
            
        try:
            if due_str:
                due_date = datetime.fromisoformat(f"{due_str}T00:00:00+00:00")
        except Exception:
            pass
        
        # Extract assignee and reporter
        assignee = None
        reporter = None
        
        if fields.get("assignee"):
            assignee = fields["assignee"].get("displayName") or fields["assignee"].get("emailAddress")
            
        if fields.get("reporter"):
            reporter = fields["reporter"].get("displayName") or fields["reporter"].get("emailAddress")
        
        # Extract project info
        project = fields.get("project", {})
        project_name = project.get("name", "Unknown")
        project_key = project.get("key", "UNK")
        
        # Extract labels and components
        labels = [label for label in fields.get("labels", [])]
        components = [comp.get("name") for comp in fields.get("components", []) if comp.get("name")]
        
        return {
            "ticket_key": issue.get("key"),
            "ticket_id": issue.get("id"),
            "title": fields.get("summary", ""),
            "description": fields.get("description", {}).get("content", "") if isinstance(fields.get("description"), dict) else fields.get("description", ""),
            "status": fields.get("status", {}).get("name", "Unknown"),
            "priority": fields.get("priority", {}).get("name"),
            "assignee": assignee,
            "reporter": reporter,
            "project": project_name,
            "project_key": project_key,
            "issue_type": fields.get("issuetype", {}).get("name"),
            "labels": labels,
            "components": components,
            "jira_created_at": created_at,
            "jira_updated_at": updated_at,
            "due_date": due_date,
            "time_estimate": fields.get("timeestimate"),
            "time_spent": fields.get("timespent"),
            "ticket_metadata": {
                "raw_issue": issue,
                "url": f"{self.base_url}/browse/{issue.get('key')}"
            }
        }
    
    async def add_work_log(
        self,
        user: User,
        ticket_key: str,
        time_spent: str,
        description: str,
        date_started: Optional[datetime] = None
    ) -> bool:
        """
        Add work log entry to JIRA ticket.
        
        Args:
            user: User adding the work log
            ticket_key: JIRA ticket key (e.g., "PROJ-123")
            time_spent: Time spent (e.g., "2h", "30m", "1h 30m")
            description: Work description
            date_started: When the work was started
            
        Returns:
            bool: True if successful
        """
        try:
            headers = await self.authenticate(user)
            if not headers:
                return False
            
            if not date_started:
                date_started = datetime.utcnow()
            
            # Format date for JIRA API
            started_str = date_started.strftime("%Y-%m-%dT%H:%M:%S.000+0000")
            
            worklog_data = {
                "comment": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": description
                                }
                            ]
                        }
                    ]
                },
                "started": started_str,
                "timeSpent": time_spent
            }
            
            url = f"{self.base_url}/rest/api/3/issue/{ticket_key}/worklog"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=worklog_data) as response:
                    if response.status in [200, 201]:
                        logger.info(f"Work log added to {ticket_key} for user {user.id}")
                        return True
                    else:
                        logger.error(f"Failed to add work log to {ticket_key}: {response.status}")
                        error_text = await response.text()
                        logger.error(f"Error details: {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error adding work log to {ticket_key}: {e}")
            return False
    
    async def test_connection(self, user: User) -> bool:
        """
        Test if JIRA connection is working.
        
        Args:
            user: User to test connection for
            
        Returns:
            bool: True if connection is working
        """
        try:
            headers = await self.authenticate(user)
            if not headers:
                return False
            
            # Test with simple API call
            url = f"{self.base_url}/rest/api/3/myself"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    return response.status == 200
                    
        except Exception as e:
            logger.error(f"JIRA connection test failed: {e}")
            return False 