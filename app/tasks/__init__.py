"""
Background Tasks Package - Daily Logger Assist

Contains Celery task definitions for asynchronous processing.
"""

from .celery_app import celery_app

__all__ = ["celery_app"] 