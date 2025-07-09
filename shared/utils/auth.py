"""
Shared Authentication Utilities for Daily Logger Assist Microservices

Provides JWT token handling and user authentication across services.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
import redis
import json
import logging

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class TokenData(BaseModel):
    """Token data model"""
    user_id: Optional[str] = None
    email: Optional[str] = None
    scopes: list = []

class AuthManager:
    """Manages authentication across microservices"""
    
    def __init__(self, secret_key: str, redis_url: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.redis_client = redis.from_url(redis_url)
        
    def hash_password(self, password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        
        # Store token in Redis for session management
        self._store_token_in_redis(encoded_jwt, data.get("sub"), expire)
        
        return encoded_jwt
    
    def create_refresh_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=7)
        
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        
        # Store refresh token in Redis
        self._store_token_in_redis(encoded_jwt, data.get("sub"), expire, token_type="refresh")
        
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[TokenData]:
        """Verify JWT token"""
        try:
            # Check if token is blacklisted
            if self._is_token_blacklisted(token):
                return None
                
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id: str = payload.get("sub")
            email: str = payload.get("email")
            scopes: list = payload.get("scopes", [])
            
            if user_id is None:
                return None
                
            return TokenData(user_id=user_id, email=email, scopes=scopes)
            
        except JWTError as e:
            logger.error(f"JWT verification failed: {e}")
            return None
    
    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """Refresh access token using refresh token"""
        try:
            payload = jwt.decode(refresh_token, self.secret_key, algorithms=[self.algorithm])
            
            # Check if it's a refresh token
            if payload.get("type") != "refresh":
                return None
                
            user_id: str = payload.get("sub")
            email: str = payload.get("email")
            scopes: list = payload.get("scopes", [])
            
            if user_id is None:
                return None
            
            # Create new access token
            new_token_data = {
                "sub": user_id,
                "email": email,
                "scopes": scopes
            }
            
            return self.create_access_token(new_token_data, timedelta(minutes=30))
            
        except JWTError as e:
            logger.error(f"Refresh token verification failed: {e}")
            return None
    
    def blacklist_token(self, token: str) -> bool:
        """Blacklist a token (logout)"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            exp = payload.get("exp")
            
            if exp:
                # Store in Redis until expiration
                ttl = exp - datetime.utcnow().timestamp()
                if ttl > 0:
                    self.redis_client.setex(f"blacklist:{token}", int(ttl), "blacklisted")
                    return True
            
            return False
            
        except JWTError:
            return False
    
    def _store_token_in_redis(self, token: str, user_id: str, expire: datetime, token_type: str = "access"):
        """Store token in Redis for session management"""
        try:
            ttl = int((expire - datetime.utcnow()).total_seconds())
            if ttl > 0:
                token_data = {
                    "user_id": user_id,
                    "type": token_type,
                    "created_at": datetime.utcnow().isoformat()
                }
                self.redis_client.setex(f"token:{token}", ttl, json.dumps(token_data))
                
                # Also store user session
                session_key = f"session:{user_id}:{token_type}"
                self.redis_client.setex(session_key, ttl, token)
                
        except Exception as e:
            logger.error(f"Failed to store token in Redis: {e}")
    
    def _is_token_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted"""
        try:
            return self.redis_client.exists(f"blacklist:{token}")
        except Exception as e:
            logger.error(f"Failed to check token blacklist: {e}")
            return False
    
    def get_user_sessions(self, user_id: str) -> Dict[str, Any]:
        """Get active sessions for a user"""
        try:
            sessions = {}
            for token_type in ["access", "refresh"]:
                session_key = f"session:{user_id}:{token_type}"
                token = self.redis_client.get(session_key)
                if token:
                    sessions[token_type] = {
                        "token": token.decode(),
                        "ttl": self.redis_client.ttl(session_key)
                    }
            return sessions
        except Exception as e:
            logger.error(f"Failed to get user sessions: {e}")
            return {}

# Global auth manager instance
auth_manager: AuthManager = None

def init_auth(secret_key: str, redis_url: str) -> AuthManager:
    """Initialize authentication manager"""
    global auth_manager
    auth_manager = AuthManager(secret_key, redis_url)
    return auth_manager

def get_auth() -> AuthManager:
    """Get authentication manager"""
    if not auth_manager:
        raise RuntimeError("Authentication not initialized. Call init_auth first.")
    return auth_manager 