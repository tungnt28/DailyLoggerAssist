"""
Microsoft Teams Service - Daily Logger Assist

Service for collecting messages and data from Microsoft Teams using Graph API.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import aiohttp
import asyncio
from loguru import logger

from app.config import settings
from app.utils.auth import decrypt_credentials
from app.models.message import Message
from app.models.user import User

class TeamsService:
    """Microsoft Teams integration service"""
    
    def __init__(self):
        self.base_url = "https://graph.microsoft.com/v1.0"
        self.client_id = settings.TEAMS_CLIENT_ID
        self.client_secret = settings.TEAMS_CLIENT_SECRET
        self.tenant_id = settings.TEAMS_TENANT_ID
        
    async def authenticate(self, user: User) -> Optional[str]:
        """
        Authenticate with Teams and get access token.
        
        Args:
            user: User with Teams credentials
            
        Returns:
            Optional[str]: Access token if successful
        """
        if not user.teams_credentials:
            logger.warning(f"No Teams credentials for user {user.id}")
            return None
            
        try:
            credentials = decrypt_credentials(user.teams_credentials)
            if not credentials:
                logger.error(f"Failed to decrypt Teams credentials for user {user.id}")
                return None
                
            access_token = credentials.get("access_token")
            expires_at = credentials.get("expires_at")
            
            # Check if token is expired
            if expires_at:
                expires_datetime = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                if datetime.utcnow() > expires_datetime:
                    # Try to refresh token
                    refresh_token = credentials.get("refresh_token")
                    if refresh_token:
                        access_token = await self._refresh_token(refresh_token)
                    else:
                        logger.warning(f"Teams token expired for user {user.id} and no refresh token")
                        return None
                        
            return access_token
            
        except Exception as e:
            logger.error(f"Teams authentication failed for user {user.id}: {e}")
            return None
    
    async def _refresh_token(self, refresh_token: str) -> Optional[str]:
        """
        Refresh the access token using refresh token.
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            Optional[str]: New access token if successful
        """
        try:
            # TODO: Implement actual token refresh with Microsoft Graph
            # This is a placeholder implementation
            
            url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
            data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "scope": "https://graph.microsoft.com/ChannelMessage.Read.All"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data) as response:
                    if response.status == 200:
                        token_data = await response.json()
                        return token_data.get("access_token")
                    else:
                        logger.error(f"Token refresh failed: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return None
    
    async def get_user_channels(self, access_token: str) -> List[Dict[str, Any]]:
        """
        Get list of Teams channels for the user.
        
        Args:
            access_token: Valid access token
            
        Returns:
            List[Dict[str, Any]]: List of channel information
        """
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Get teams the user is a member of
            url = f"{self.base_url}/me/joinedTeams"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        teams_data = await response.json()
                        
                        channels = []
                        for team in teams_data.get("value", []):
                            team_id = team["id"]
                            
                            # Get channels for this team
                            channels_url = f"{self.base_url}/teams/{team_id}/channels"
                            async with session.get(channels_url, headers=headers) as ch_response:
                                if ch_response.status == 200:
                                    channels_data = await ch_response.json()
                                    for channel in channels_data.get("value", []):
                                        channels.append({
                                            "team_id": team_id,
                                            "team_name": team["displayName"],
                                            "channel_id": channel["id"],
                                            "channel_name": channel["displayName"],
                                            "channel_type": channel.get("membershipType", "standard")
                                        })
                        
                        return channels
                    else:
                        logger.error(f"Failed to get Teams channels: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error getting Teams channels: {e}")
            return []
    
    async def collect_messages(
        self, 
        user: User, 
        since: datetime, 
        channels: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Collect messages from Teams channels.
        
        Args:
            user: User to collect messages for
            since: Collect messages since this datetime
            channels: Optional list of channel IDs to collect from
            
        Returns:
            List[Dict[str, Any]]: List of message data
        """
        try:
            access_token = await self.authenticate(user)
            if not access_token:
                logger.error(f"Failed to authenticate Teams for user {user.id}")
                return []
            
            if not channels:
                user_channels = await self.get_user_channels(access_token)
                channels = [ch["channel_id"] for ch in user_channels]
            
            messages = []
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Convert datetime to Microsoft Graph filter format
            since_filter = since.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            
            async with aiohttp.ClientSession() as session:
                for channel_id in channels:
                    try:
                        # Get messages from channel
                        url = f"{self.base_url}/teams/{{team-id}}/channels/{channel_id}/messages"
                        params = {
                            "$filter": f"createdDateTime ge {since_filter}",
                            "$orderby": "createdDateTime desc",
                            "$top": 100
                        }
                        
                        async with session.get(url, headers=headers, params=params) as response:
                            if response.status == 200:
                                messages_data = await response.json()
                                
                                for msg in messages_data.get("value", []):
                                    # Extract message content
                                    content = ""
                                    if msg.get("body", {}).get("content"):
                                        content = msg["body"]["content"]
                                        # Remove HTML tags if present
                                        import re
                                        content = re.sub(r'<[^>]+>', '', content)
                                    
                                    if content.strip():  # Only collect non-empty messages
                                        messages.append({
                                            "external_id": msg["id"],
                                            "channel_id": channel_id,
                                            "thread_id": msg.get("replyToId"),
                                            "content": content.strip(),
                                            "sender": msg.get("from", {}).get("user", {}).get("displayName", "Unknown"),
                                            "message_timestamp": datetime.fromisoformat(msg["createdDateTime"].replace('Z', '+00:00')),
                                            "source": "teams",
                                            "metadata": {
                                                "message_type": msg.get("messageType", "message"),
                                                "importance": msg.get("importance", "normal"),
                                                "team_id": msg.get("chatId"),
                                                "raw_data": msg
                                            }
                                        })
                            elif response.status == 403:
                                logger.warning(f"No access to channel {channel_id}")
                            else:
                                logger.error(f"Failed to get messages from channel {channel_id}: {response.status}")
                                
                    except Exception as e:
                        logger.error(f"Error collecting from channel {channel_id}: {e}")
                        continue
            
            logger.info(f"Collected {len(messages)} Teams messages for user {user.id}")
            return messages
            
        except Exception as e:
            logger.error(f"Teams message collection failed for user {user.id}: {e}")
            return []
    
    async def test_connection(self, user: User) -> bool:
        """
        Test if Teams connection is working.
        
        Args:
            user: User to test connection for
            
        Returns:
            bool: True if connection is working
        """
        try:
            access_token = await self.authenticate(user)
            if not access_token:
                return False
                
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Simple test request
            url = f"{self.base_url}/me"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    return response.status == 200
                    
        except Exception as e:
            logger.error(f"Teams connection test failed: {e}")
            return False 