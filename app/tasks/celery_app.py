"""
Celery Application - Daily Logger Assist

Celery configuration for background task processing.
"""

from celery import Celery
from app.config import settings

# Create Celery instance
celery_app = Celery(
    "daily_logger_assist",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.data_collection", "app.tasks.ai_processing"]
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task routing
    task_routes={
        "app.tasks.data_collection.*": {"queue": "data_collection"},
        "app.tasks.ai_processing.*": {"queue": "ai_processing"},
    },
    
    # Worker settings
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    
    # Result settings
    result_expires=3600,  # 1 hour
    
    # Retry settings
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    
    # Beat schedule for periodic tasks
    beat_schedule={
        'collect-data-every-hour': {
            'task': 'app.tasks.data_collection.collect_all_data',
            'schedule': 3600.0,  # Every hour
        },
        'process-ai-analysis-every-30-min': {
            'task': 'app.tasks.ai_processing.process_pending_analysis',
            'schedule': 1800.0,  # Every 30 minutes
        },
        'generate-daily-reports': {
            'task': 'app.tasks.ai_processing.generate_daily_reports',
            'schedule': 86400.0,  # Daily at midnight
        },
    },
)

# Auto-discover tasks
celery_app.autodiscover_tasks()

if __name__ == "__main__":
    celery_app.start() 