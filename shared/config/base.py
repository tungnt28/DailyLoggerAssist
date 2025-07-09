"""
Base Configuration for Daily Logger Assist Microservices

Shared configuration that all microservices will inherit from.
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os
import secrets

def generate_secret_key() -> str:
    """Generate a secure random secret key"""
    return secrets.token_urlsafe(32)

class BaseConfig(BaseSettings):
    """Base configuration for all microservices"""
    
    # Application Settings
    APP_NAME: str = "Daily Logger Assist"
    DEBUG: bool = False
    SECRET_KEY: str = ""
    ENVIRONMENT: str = "development"
    
    # Database Settings
    DATABASE_URL: str = "postgresql://dailylogger:password@localhost:5432/dailylogger"
    
    # Redis Settings
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_PASSWORD: Optional[str] = None
    
    # Security Settings
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600
    
    # CORS Settings
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Service Discovery
    GATEWAY_URL: str = "http://localhost:8000"
    USER_SERVICE_URL: str = "http://localhost:8001"
    DATA_COLLECTION_SERVICE_URL: str = "http://localhost:8002"
    AI_PROCESSING_SERVICE_URL: str = "http://localhost:8003"
    REPORTING_SERVICE_URL: str = "http://localhost:8004"
    NOTIFICATION_SERVICE_URL: str = "http://localhost:8005"
    
    # Monitoring
    SENTRY_DSN: Optional[str] = None
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Validate SECRET_KEY
        if not self.SECRET_KEY:
            if self.ENVIRONMENT == "development":
                self.SECRET_KEY = generate_secret_key()
                print(f"WARNING: Using auto-generated SECRET_KEY for development.")
            else:
                raise ValueError("SECRET_KEY environment variable is required for production")
        
        # Validate minimum SECRET_KEY length
        if len(self.SECRET_KEY) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        
        # Update Redis URLs with password if provided
        if self.REDIS_PASSWORD:
            self.REDIS_URL = f"redis://:{self.REDIS_PASSWORD}@localhost:6379"
    
    class Config:
        env_file = ".env"
        case_sensitive = True 