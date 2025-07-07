#!/usr/bin/env python3
"""
Database Setup Script - Daily Logger Assist

Script to initialize the database, create tables, and optionally seed with sample data.
"""

import os
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.connection import engine, create_tables, drop_tables
from app.models import Base, User
from app.config import settings
from sqlalchemy.orm import sessionmaker
from loguru import logger
import click

# Create session for data seeding
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def setup_logging():
    """Setup logging for the setup script"""
    logger.add(
        "logs/setup.log",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        rotation="10 MB"
    )

def create_log_directory():
    """Create logs directory if it doesn't exist"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

def check_database_connection():
    """Check if database connection is working"""
    try:
        from sqlalchemy import text
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

def create_sample_user():
    """Create a sample user for testing"""
    db = SessionLocal()
    try:
        # Check if sample user already exists
        existing_user = db.query(User).filter(User.email == "demo@example.com").first()
        if existing_user:
            logger.info("Sample user already exists")
            return
        
        # Create sample user
        sample_user = User(
            email="demo@example.com",
            first_name="Demo",
            last_name="User",
            is_active=True,
            preferences={
                "ai_confidence_threshold": 0.7,
                "auto_approve_high_confidence": True,
                "timezone": "UTC"
            }
        )
        
        db.add(sample_user)
        db.commit()
        db.refresh(sample_user)
        
        logger.info(f"Sample user created with ID: {sample_user.id}")
        
    except Exception as e:
        logger.error(f"Failed to create sample user: {e}")
        db.rollback()
    finally:
        db.close()

@click.command()
@click.option("--drop", is_flag=True, help="Drop existing tables before creating new ones")
@click.option("--sample-data", is_flag=True, help="Create sample data for testing")
@click.option("--check-only", is_flag=True, help="Only check database connection")
def main(drop: bool, sample_data: bool, check_only: bool):
    """
    Setup Daily Logger Assist database.
    
    This script will create all necessary database tables and optionally
    populate them with sample data for testing.
    """
    create_log_directory()
    setup_logging()
    
    logger.info("Starting database setup...")
    logger.info(f"Database URL: {settings.DATABASE_URL}")
    
    # Check database connection
    if not check_database_connection():
        logger.error("Database setup failed - could not connect to database")
        sys.exit(1)
    
    if check_only:
        logger.info("Database connection check completed successfully")
        return
    
    try:
        # Drop tables if requested
        if drop:
            logger.info("Dropping existing tables...")
            drop_tables()
            logger.info("Tables dropped successfully")
        
        # Create tables
        logger.info("Creating database tables...")
        create_tables()
        logger.info("Database tables created successfully")
        
        # Create sample data if requested
        if sample_data:
            logger.info("Creating sample data...")
            create_sample_user()
            logger.info("Sample data created successfully")
        
        logger.info("Database setup completed successfully!")
        
        # Print next steps
        print("\n" + "="*50)
        print("Database setup completed successfully!")
        print("="*50)
        print(f"Database URL: {settings.DATABASE_URL}")
        
        if sample_data:
            print("\nSample user created:")
            print("  Email: demo@example.com")
            print("  Name: Demo User")
        
        print("\nNext steps:")
        print("1. Start the FastAPI server: uvicorn app.main:app --reload")
        print("2. Visit http://localhost:8000/docs for API documentation")
        print("3. Use the authentication endpoints to get started")
        
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 