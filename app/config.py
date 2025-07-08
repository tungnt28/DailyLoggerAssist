"""
Configuration Management for Daily Logger Assist

Manages all application settings using Pydantic Settings.
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os
import secrets

def generate_secret_key() -> str:
    """Generate a secure random secret key"""
    return secrets.token_urlsafe(32)

class Settings(BaseSettings):
    """Application settings"""
    
    # Application Settings
    APP_NAME: str = "Daily Logger Assist"
    DEBUG: bool = False
    SECRET_KEY: str = ""  # Must be set via environment variable
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # Environment
    ENVIRONMENT: str = "development"
    
    # Database Settings
    DATABASE_URL: str = "sqlite:///./daily_logger.db"
    
    # AI Service (OpenRoute)
    OPENROUTE_API_KEY: Optional[str] = None
    OPENROUTE_BASE_URL: str = "https://openrouter.ai/api/v1"
    DEFAULT_AI_MODEL: str = "gpt-3.5-turbo"
    
    # Microsoft Teams Integration
    TEAMS_CLIENT_ID: Optional[str] = None
    TEAMS_CLIENT_SECRET: Optional[str] = None
    TEAMS_TENANT_ID: Optional[str] = None
    TEAMS_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/teams/callback"
    
    # JIRA Integration
    JIRA_SERVER_URL: str = ""
    JIRA_USERNAME: str = ""
    JIRA_API_TOKEN: str = ""
    
    # Email Integration
    EMAIL_SERVER: Optional[str] = "outlook.office365.com"
    EMAIL_PORT: int = 993
    EMAIL_USE_TLS: bool = True
    
    # Redis (for Celery)
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_PASSWORD: Optional[str] = None
    
    # Celery Settings
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/daily_logger.log"
    
    # Security
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # AI Processing
    MAX_CONTENT_LENGTH: int = 4000
    CONFIDENCE_THRESHOLD: float = 0.7
    MAX_TOKENS: int = 2000
    
    # Data Collection
    TEAMS_SYNC_INTERVAL_HOURS: int = 1
    EMAIL_SYNC_INTERVAL_HOURS: int = 2
    JIRA_SYNC_INTERVAL_HOURS: int = 4
    
    # OAuth settings for external services
    JIRA_BASE_URL: Optional[str] = None
    
    # Production Settings
    SENTRY_DSN: Optional[str] = None
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600  # 1 hour in seconds
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Validate SECRET_KEY
        if not self.SECRET_KEY:
            if self.ENVIRONMENT == "development":
                # Generate a temporary key for development
                self.SECRET_KEY = generate_secret_key()
                print("WARNING: Using auto-generated SECRET_KEY for development. Set SECRET_KEY environment variable for production!")
            else:
                raise ValueError("SECRET_KEY environment variable is required for production")
        
        # Validate minimum SECRET_KEY length
        if len(self.SECRET_KEY) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        
        # Update Redis URLs with password if provided
        if self.REDIS_PASSWORD:
            self.REDIS_URL = f"redis://:{self.REDIS_PASSWORD}@localhost:6379"
            self.CELERY_BROKER_URL = f"redis://:{self.REDIS_PASSWORD}@localhost:6379/0"
            self.CELERY_RESULT_BACKEND = f"redis://:{self.REDIS_PASSWORD}@localhost:6379/0"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = Settings() 