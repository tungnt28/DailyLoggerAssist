"""
Email Service - Daily Logger Assist

Service for collecting emails from Outlook/Exchange using IMAP.
"""

import imaplib
import email
from email.header import decode_header
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
import ssl
from loguru import logger

from app.config import settings
from app.utils.auth import decrypt_credentials
from app.models.message import Message
from app.models.user import User

class EmailService:
    """Email integration service"""
    
    def __init__(self):
        self.default_server = settings.EMAIL_SERVER or "outlook.office365.com"
        self.default_port = settings.EMAIL_PORT or 993
        self.use_tls = settings.EMAIL_USE_TLS or True
        
    async def authenticate(self, user: User) -> Optional[imaplib.IMAP4_SSL]:
        """
        Authenticate with email server and return IMAP connection.
        
        Args:
            user: User with email credentials
            
        Returns:
            Optional[imaplib.IMAP4_SSL]: IMAP connection if successful
        """
        if not user.email_credentials:
            logger.warning(f"No email credentials for user {user.id}")
            return None
            
        try:
            credentials = decrypt_credentials(user.email_credentials)
            if not credentials:
                logger.error(f"Failed to decrypt email credentials for user {user.id}")
                return None
                
            email_address = credentials.get("email")
            password = credentials.get("password")
            server = credentials.get("server", self.default_server)
            port = credentials.get("port", self.default_port)
            use_tls = credentials.get("use_tls", self.use_tls)
            
            if not email_address or not password:
                logger.error(f"Missing email or password for user {user.id}")
                return None
            
            # Create SSL context
            context = ssl.create_default_context()
            
            # Connect to IMAP server
            if use_tls:
                mail = imaplib.IMAP4_SSL(server, port, ssl_context=context)
            else:
                mail = imaplib.IMAP4(server, port)
                
            # Login
            mail.login(email_address, password)
            
            logger.info(f"Email authentication successful for user {user.id}")
            return mail
            
        except Exception as e:
            logger.error(f"Email authentication failed for user {user.id}: {e}")
            return None
    
    def _decode_header(self, header_value: str) -> str:
        """
        Decode email header value.
        
        Args:
            header_value: Raw header value
            
        Returns:
            str: Decoded header value
        """
        try:
            decoded = decode_header(header_value)
            if decoded:
                value, encoding = decoded[0]
                if isinstance(value, bytes):
                    return value.decode(encoding or 'utf-8', errors='ignore')
                return str(value)
            return header_value
        except Exception:
            return header_value or ""
    
    def _extract_text_content(self, msg: email.message.Message) -> str:
        """
        Extract text content from email message.
        
        Args:
            msg: Email message object
            
        Returns:
            str: Extracted text content
        """
        try:
            content = ""
            
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition", ""))
                    
                    # Skip attachments
                    if "attachment" in content_disposition:
                        continue
                        
                    if content_type == "text/plain":
                        charset = part.get_content_charset() or 'utf-8'
                        body = part.get_payload(decode=True)
                        if body:
                            content += body.decode(charset, errors='ignore')
                    elif content_type == "text/html" and not content:
                        # Fall back to HTML if no plain text
                        charset = part.get_content_charset() or 'utf-8'
                        body = part.get_payload(decode=True)
                        if body:
                            html_content = body.decode(charset, errors='ignore')
                            # Simple HTML tag removal
                            import re
                            content = re.sub(r'<[^>]+>', '', html_content)
            else:
                content_type = msg.get_content_type()
                if content_type == "text/plain":
                    charset = msg.get_content_charset() or 'utf-8'
                    body = msg.get_payload(decode=True)
                    if body:
                        content = body.decode(charset, errors='ignore')
            
            # Clean up content
            content = content.strip()
            # Remove excessive whitespace
            import re
            content = re.sub(r'\n\s*\n', '\n\n', content)
            content = re.sub(r' +', ' ', content)
            
            return content
            
        except Exception as e:
            logger.error(f"Error extracting email content: {e}")
            return ""
    
    async def collect_messages(
        self, 
        user: User, 
        since: datetime,
        folders: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Collect emails from specified folders.
        
        Args:
            user: User to collect emails for
            since: Collect emails since this datetime
            folders: Optional list of folder names to collect from
            
        Returns:
            List[Dict[str, Any]]: List of email message data
        """
        try:
            # Run IMAP operations in thread pool since they're blocking
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._collect_messages_sync, user, since, folders)
            
        except Exception as e:
            logger.error(f"Email collection failed for user {user.id}: {e}")
            return []
    
    def _collect_messages_sync(
        self,
        user: User,
        since: datetime,
        folders: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Synchronous email collection implementation.
        """
        mail = None
        try:
            mail = asyncio.run(self.authenticate(user))
            if not mail:
                return []
            
            if not folders:
                folders = ["INBOX", "Sent"]
            
            messages = []
            
            for folder in folders:
                try:
                    # Select folder
                    status, _ = mail.select(folder)
                    if status != 'OK':
                        logger.warning(f"Cannot select folder {folder} for user {user.id}")
                        continue
                    
                    # Search for emails since date
                    search_date = since.strftime("%d-%b-%Y")
                    search_criteria = f'(SINCE "{search_date}")'
                    
                    status, messages_ids = mail.search(None, search_criteria)
                    if status != 'OK':
                        logger.warning(f"Search failed in folder {folder} for user {user.id}")
                        continue
                    
                    message_ids = messages_ids[0].split()
                    
                    # Limit to recent messages to avoid overload
                    if len(message_ids) > 100:
                        message_ids = message_ids[-100:]  # Get most recent 100
                    
                    for msg_id in message_ids:
                        try:
                            # Fetch message
                            status, msg_data = mail.fetch(msg_id, '(RFC822)')
                            if status != 'OK':
                                continue
                                
                            # Parse message
                            raw_email = msg_data[0][1]
                            msg = email.message_from_bytes(raw_email)
                            
                            # Extract headers
                            subject = self._decode_header(msg.get("Subject", ""))
                            sender = self._decode_header(msg.get("From", ""))
                            date_str = msg.get("Date", "")
                            message_id = msg.get("Message-ID", "")
                            
                            # Parse date
                            try:
                                msg_date = email.utils.parsedate_to_datetime(date_str)
                                if msg_date.tzinfo is None:
                                    msg_date = msg_date.replace(tzinfo=datetime.now().astimezone().tzinfo)
                            except Exception:
                                msg_date = datetime.utcnow()
                            
                            # Skip if message is older than since date
                            if msg_date < since:
                                continue
                            
                            # Extract content
                            content = self._extract_text_content(msg)
                            
                            if content.strip():  # Only collect non-empty messages
                                messages.append({
                                    "external_id": message_id,
                                    "channel_id": folder,
                                    "thread_id": msg.get("In-Reply-To"),
                                    "content": content[:4000],  # Limit content length
                                    "sender": sender,
                                    "subject": subject,
                                    "message_timestamp": msg_date,
                                    "source": "email",
                                    "metadata": {
                                        "folder": folder,
                                        "cc": msg.get("Cc", ""),
                                        "bcc": msg.get("Bcc", ""),
                                        "reply_to": msg.get("Reply-To", ""),
                                        "raw_headers": dict(msg.items())
                                    }
                                })
                                
                        except Exception as e:
                            logger.error(f"Error processing email {msg_id}: {e}")
                            continue
                            
                except Exception as e:
                    logger.error(f"Error processing folder {folder}: {e}")
                    continue
            
            logger.info(f"Collected {len(messages)} email messages for user {user.id}")
            return messages
            
        except Exception as e:
            logger.error(f"Email collection sync failed for user {user.id}: {e}")
            return []
        finally:
            if mail:
                try:
                    mail.logout()
                except Exception:
                    pass
    
    async def test_connection(self, user: User) -> bool:
        """
        Test if email connection is working.
        
        Args:
            user: User to test connection for
            
        Returns:
            bool: True if connection is working
        """
        try:
            mail = await self.authenticate(user)
            if not mail:
                return False
                
            # Test by selecting INBOX
            status, _ = mail.select("INBOX")
            success = status == 'OK'
            
            # Clean up
            try:
                mail.logout()
            except Exception:
                pass
                
            return success
            
        except Exception as e:
            logger.error(f"Email connection test failed: {e}")
            return False 