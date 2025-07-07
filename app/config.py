"""
Configuration Management for Daily Logger Assist

Manages all application settings using Pydantic Settings.
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    """Application settings"""
    
    # Application Settings
    APP_NAME: str = "Daily Logger Assist"
    DEBUG: bool = False
    SECRET_KEY: str = "your-secret-key-change-in-production"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
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
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = Settings() 